"""AI generation service using LangChain with structured output."""

import time
from decimal import Decimal
from typing import Any

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import ValidationError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from app.models.client import Client
from app.models.generation_audit import GenerationAudit
from app.models.generation_job import GenerationJob
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.schemas.ai_output import ProductContent
from app.services.cost_tracker import CostTracker


# Default prompts when client has no custom prompts
DEFAULT_TITLE_PROMPT = """You are an expert product title writer for online marketplaces.
Create a compelling, SEO-optimized product title that captures the essence of the product.
The title MUST be exactly 30-60 characters long, including spaces.
Count every character carefully before responding."""

DEFAULT_DESCRIPTION_PROMPT = """You are an expert product description writer for online marketplaces.
Create an engaging, detailed product description that highlights key features and benefits.
The description MUST be exactly 2000-3000 characters long, including spaces and punctuation.
Count every character carefully before responding."""

CHARACTER_LIMIT_ENFORCEMENT = """CRITICAL CHARACTER LIMITS - YOU MUST FOLLOW THESE EXACTLY:
- Title: MUST be between 30 and 60 characters (count spaces)
- Description: MUST be between 2000 and 3000 characters (count spaces and punctuation)

Before responding, COUNT YOUR CHARACTERS. If you violate these limits, you will be asked to regenerate."""


class AIGenerationService:
    """
    Service for generating product content using LangChain and OpenAI.

    Handles:
    - Dynamic prompt building from client settings and product fields
    - Structured output with character limit validation
    - Retry logic for rate limits and validation failures
    - Token counting and cost tracking
    - Audit trail storage
    """

    MAX_RETRIES = 3  # 1 original + 3 retries = 4 total attempts

    def __init__(
        self,
        db: AsyncSession,
        api_key: str,
        model: str = "gpt-5.2",
        temperature: float = 0.7,
    ):
        """Initialize the AI generation service."""
        self.db = db
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.cost_tracker = CostTracker(model)

        # Initialize LangChain model with structured output
        self._model = None

    @property
    def model(self) -> ChatOpenAI:
        """Lazy-load the LangChain model."""
        if self._model is None:
            base_model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key,
                # Enable 24-hour extended prompt caching for cost savings
                # OpenAI caches identical prompt prefixes (system messages, brand info)
                # and charges 50% less for cached input tokens
                extra_body={"prompt_cache_retention": "24h"},
            )
            # Enable structured output with Pydantic validation
            # include_raw=True returns both parsed content and raw AIMessage with token usage
            self._model = base_model.with_structured_output(
                ProductContent,
                strict=True,
                include_raw=True,
            )
        return self._model

    def build_prompt(
        self,
        product_group: ProductGroup,
        client: Client,
        app_settings: AppSettings | None = None,
        is_retry: bool = False,
        previous_error: str | None = None,
    ) -> ChatPromptTemplate:
        """
        Build dynamic prompt based on client settings and product fields.

        Args:
            product_group: The product group to generate content for
            client: Client with brand info and custom prompts
            app_settings: App settings with default prompts
            is_retry: Whether this is a retry attempt
            previous_error: Error message from previous attempt (for retry prompts)

        Returns:
            ChatPromptTemplate ready for invocation
        """
        # Get selected fields (or defaults)
        selected_fields = client.ai_input_fields or [
            "product_name",
            "description",
            "product_type",
            "option_name",
            "country_of_origin",
            "sku",
            "images",
        ]

        # Build field context from product group
        field_data = []
        for field in selected_fields:
            value = getattr(product_group, field, None)
            if value:
                # Format field name nicely
                field_label = field.replace("_", " ").title()
                field_data.append(f"{field_label}: {value}")

        # Add variant info if multi-variant
        if product_group.variant_count > 1:
            field_data.append(f"Product Variants: {product_group.variant_count} options available")

        # Get prompts (client custom > app defaults > hardcoded defaults)
        title_prompt = (
            client.task1_prompt
            or (app_settings.default_task1_prompt if app_settings else None)
            or DEFAULT_TITLE_PROMPT
        )
        description_prompt = (
            client.task2_prompt
            or (app_settings.default_task2_prompt if app_settings else None)
            or DEFAULT_DESCRIPTION_PROMPT
        )
        system_prompt = (
            client.system_prompt
            or (app_settings.default_system_prompt if app_settings else None)
            or ""
        )

        # Build brand context if available
        brand_context = []
        if client.brand_name:
            brand_context.append(f"Brand: {client.brand_name}")
        if client.story:
            brand_context.append(f"Brand Story: {client.story}")
        if client.tone:
            brand_context.append(f"Tone: {client.tone}")
        if client.language:
            brand_context.append(f"Language: {client.language}")
        if client.guidelines:
            brand_context.append(f"Guidelines: {client.guidelines}")

        # Build messages list
        messages = []

        # System prompt (if exists)
        if system_prompt:
            messages.append(("system", system_prompt))

        # Brand context
        if brand_context:
            messages.append(("system", "Brand Information:\n" + "\n".join(brand_context)))

        # Task prompts
        messages.append(("system", f"TITLE GENERATION INSTRUCTIONS:\n{title_prompt}"))
        messages.append(("system", f"DESCRIPTION GENERATION INSTRUCTIONS:\n{description_prompt}"))

        # Character limit enforcement
        messages.append(("system", CHARACTER_LIMIT_ENFORCEMENT))

        # Retry-specific instructions
        if is_retry and previous_error:
            messages.append((
                "system",
                f"PREVIOUS ATTEMPT FAILED: {previous_error}\n"
                "Please regenerate with STRICT adherence to character limits. "
                "Count every single character before responding."
            ))

        # User message with product data
        messages.append((
            "user",
            "Generate a title and description for this product:\n\n"
            + "\n".join(field_data)
        ))

        return ChatPromptTemplate.from_messages(messages)

    async def generate_content(
        self,
        product_group: ProductGroup,
        client: Client,
        job: GenerationJob,
        app_settings: AppSettings | None = None,
    ) -> tuple[ProductContent | None, GenerationAudit]:
        """
        Generate content for a product group with retry logic.

        Args:
            product_group: Product group to generate for
            client: Client with settings
            job: Current generation job
            app_settings: App settings for defaults

        Returns:
            Tuple of (ProductContent or None if failed, GenerationAudit)
        """
        last_audit = None
        last_error = None

        print(f"[AIService] Starting generation for product {product_group.id} (name: {product_group.product_name})")
        print(f"[AIService] Using model: {self.model_name}, API key present: {bool(self.api_key)}, key starts with: {self.api_key[:8] if self.api_key else 'None'}...")

        for attempt in range(1, self.MAX_RETRIES + 2):  # +2 because range is exclusive
            start_time = time.time()

            # Build prompt (with retry context if applicable)
            prompt = self.build_prompt(
                product_group,
                client,
                app_settings,
                is_retry=(attempt > 1),
                previous_error=last_error,
            )

            # Format prompt as string for audit - format the messages to get actual content
            formatted_messages = prompt.format_messages()
            prompt_str = "\n".join(
                f"[{m.type}] {m.content[:500]}..." if len(m.content) > 500 else f"[{m.type}] {m.content}"
                for m in formatted_messages
            )

            try:
                # Call the model with client_id as cache key for better cache routing
                print(f"[AIService] Attempt {attempt}: Invoking model...")
                cache_key = str(client.id) if client else None
                raw_result = await self._invoke_with_retry(prompt, cache_key=cache_key)
                print(f"[AIService] Attempt {attempt}: Model returned result")

                # With include_raw=True, result is {"raw": AIMessage, "parsed": ProductContent}
                raw_message = raw_result.get("raw")
                result = raw_result.get("parsed")

                # Get token usage from raw AIMessage response metadata
                usage = {}
                if raw_message and hasattr(raw_message, "response_metadata"):
                    usage = raw_message.response_metadata.get("token_usage", {})
                    print(f"[AIService] Token usage from API: {usage}")

                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

                # Get cached tokens from prompt_tokens_details (OpenAI API)
                prompt_details = usage.get("prompt_tokens_details", {})
                cached_input_tokens = prompt_details.get("cached_tokens", 0) if prompt_details else 0

                # If no token info in metadata, estimate with tiktoken
                if input_tokens == 0:
                    input_tokens = self.cost_tracker.count_tokens(prompt_str)
                if output_tokens == 0:
                    output_tokens = self.cost_tracker.count_tokens(
                        f"{result.title} {result.description}"
                    )

                # Calculate cost (with cached token discount)
                cost = self.cost_tracker.add_usage(input_tokens, output_tokens, cached_input_tokens)
                print(f"[AIService] Cost breakdown - input: ${self.cost_tracker.total_input_cost}, cached: ${self.cost_tracker.total_cached_input_cost}, output: ${self.cost_tracker.total_output_cost}")

                duration_ms = int((time.time() - start_time) * 1000)

                # Create successful audit
                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=True,
                    generated_title=result.title,
                    generated_description=result.description,
                    title_length=len(result.title),
                    description_length=len(result.description),
                    prompt_used=prompt_str[:10000],  # Truncate if too long
                    model_version=self.model_name,
                    temperature=Decimal(str(self.temperature)),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    duration_ms=duration_ms,
                )
                self.db.add(audit)

                return result, audit

            except ValidationError as e:
                # Character limit violation - store and retry
                last_error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)

                # Try to extract the generated content for audit
                generated_title = None
                generated_description = None
                if hasattr(e, "errors"):
                    for error in e.errors():
                        if "title" in error.get("loc", []):
                            # Extract title from input
                            pass  # Will be None
                        if "description" in error.get("loc", []):
                            pass  # Will be None

                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=False,
                    error_message=f"Validation error: {last_error}",
                    generated_title=generated_title,
                    generated_description=generated_description,
                    prompt_used=prompt_str[:10000],
                    model_version=self.model_name,
                    temperature=Decimal(str(self.temperature)),
                    input_tokens=0,  # Unknown on validation failure
                    output_tokens=0,
                    cost=Decimal("0"),
                    duration_ms=duration_ms,
                )
                self.db.add(audit)
                last_audit = audit

                if attempt >= self.MAX_RETRIES + 1:
                    # Max retries exceeded
                    return None, audit

            except Exception as e:
                # Other error (API error, rate limit, etc.)
                print(f"[AIService] API error for product {product_group.id}: {e}")
                import traceback
                traceback.print_exc()
                last_error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)

                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=False,
                    error_message=f"API error: {last_error}",
                    prompt_used=prompt_str[:10000],
                    model_version=self.model_name,
                    temperature=Decimal(str(self.temperature)),
                    input_tokens=0,
                    output_tokens=0,
                    cost=Decimal("0"),
                    duration_ms=duration_ms,
                )
                self.db.add(audit)
                last_audit = audit

                if attempt >= self.MAX_RETRIES + 1:
                    return None, audit

        # Should not reach here, but return last audit if we do
        return None, last_audit

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    async def _invoke_with_retry(self, prompt: ChatPromptTemplate, cache_key: str | None = None) -> dict:
        """
        Invoke the model with retry logic for rate limits.

        Uses tenacity for exponential backoff on API errors.
        Returns dict with 'raw' (AIMessage) and 'parsed' (ProductContent) keys.

        Args:
            prompt: The prompt template to invoke
            cache_key: Optional cache key (e.g. client_id) to improve cache hit rates
                      by routing requests with same prefix to same server
        """
        # Format the prompt template to get actual Message objects
        formatted_messages = prompt.format_messages()

        # Use prompt_cache_key to route requests with same client to same cache server
        # This maximizes cache hits since all products for a client share the same
        # system prompts, brand info, and instructions prefix
        invoke_kwargs = {}
        if cache_key:
            invoke_kwargs["prompt_cache_key"] = cache_key

        return await self.model.ainvoke(formatted_messages, **invoke_kwargs)

    async def get_pending_product_groups(
        self, client_id: str, status_filter: list[str] | None = None
    ) -> list[ProductGroup]:
        """
        Get product groups that need generation.

        Args:
            client_id: Client ID to filter by
            status_filter: List of statuses to include (default: ['pending'])

        Returns:
            List of ProductGroup objects ordered by row_index
        """
        if status_filter is None:
            status_filter = ["pending"]

        query = (
            select(ProductGroup)
            .where(ProductGroup.client_id == client_id)
            .where(ProductGroup.status.in_(status_filter))
            .order_by(ProductGroup.created_at)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_product_group_status(
        self,
        product_group_id: str,
        status: str,
        title: str | None = None,
        description: str | None = None,
        error_message: str | None = None,
    ) -> None:
        """Update product group with generated content and status."""
        values: dict[str, Any] = {"status": status}
        if title is not None:
            values["generated_title"] = title
        if description is not None:
            values["generated_description"] = description

        stmt = (
            update(ProductGroup)
            .where(ProductGroup.id == product_group_id)
            .values(**values)
        )
        await self.db.execute(stmt)

    async def get_app_settings(self) -> AppSettings | None:
        """Get app settings for default prompts and API key."""
        result = await self.db.execute(
            select(AppSettings).where(AppSettings.id == 1)
        )
        return result.scalar_one_or_none()

    async def get_client(self, client_id: str) -> Client | None:
        """Get client by ID."""
        result = await self.db.execute(
            select(Client).where(Client.id == client_id)
        )
        return result.scalar_one_or_none()
