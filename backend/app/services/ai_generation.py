"""AI generation service using LangChain with structured output."""

import time
from decimal import Decimal
from typing import Any, Callable, Awaitable

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
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.schemas.ai_output import DescriptionContent, ProductContent, TitleContent
from app.services.cost_tracker import CostTracker

# Callback type for tracking attempt results
# signature: async def callback(attempt_number: int, success: bool, error: str | None) -> None
AttemptCallback = Callable[[int, bool, str | None], Awaitable[None]]


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

        # Initialize LangChain models with structured output
        self._model = None  # Combined model (legacy)
        self._title_model = None  # Task 1: Title only
        self._description_model = None  # Task 2: Description only

    @property
    def model(self) -> ChatOpenAI:
        """Lazy-load the LangChain model."""
        if self._model is None:
            # Build model kwargs - only add prompt_cache_retention for models that support it
            # gpt-4o-mini does NOT support prompt_cache_retention
            model_kwargs = {
                "model": self.model_name,
                "temperature": self.temperature,
                "api_key": self.api_key,
            }

            # Only add prompt caching for models that support it (gpt-5.2, gpt-4o, etc.)
            # gpt-4o-mini does not support this feature
            if self.model_name not in ["gpt-4o-mini", "gpt-3.5-turbo"]:
                model_kwargs["extra_body"] = {"prompt_cache_retention": "24h"}

            base_model = ChatOpenAI(**model_kwargs)
            # Enable structured output with Pydantic validation
            # include_raw=True returns both parsed content and raw AIMessage with token usage
            self._model = base_model.with_structured_output(
                ProductContent,
                strict=True,
                include_raw=True,
            )
        return self._model

    @property
    def title_model(self) -> ChatOpenAI:
        """Lazy-load the LangChain model for Task 1 (title generation)."""
        if self._title_model is None:
            model_kwargs = {
                "model": self.model_name,
                "temperature": self.temperature,
                "api_key": self.api_key,
            }
            if self.model_name not in ["gpt-4o-mini", "gpt-3.5-turbo"]:
                model_kwargs["extra_body"] = {"prompt_cache_retention": "24h"}

            base_model = ChatOpenAI(**model_kwargs)
            self._title_model = base_model.with_structured_output(
                TitleContent,
                strict=True,
                include_raw=True,
            )
        return self._title_model

    @property
    def description_model(self) -> ChatOpenAI:
        """Lazy-load the LangChain model for Task 2 (description generation)."""
        if self._description_model is None:
            model_kwargs = {
                "model": self.model_name,
                "temperature": self.temperature,
                "api_key": self.api_key,
            }
            if self.model_name not in ["gpt-4o-mini", "gpt-3.5-turbo"]:
                model_kwargs["extra_body"] = {"prompt_cache_retention": "24h"}

            base_model = ChatOpenAI(**model_kwargs)
            self._description_model = base_model.with_structured_output(
                DescriptionContent,
                strict=True,
                include_raw=True,
            )
        return self._description_model

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

        # Get prompts (client custom > app defaults > error if not configured)
        title_prompt = client.task1_prompt or (app_settings.default_task1_prompt if app_settings else None)
        if not title_prompt:
            raise ValueError("Task 1 (Title) prompt not configured. Set a prompt in Client settings or global Settings.")

        description_prompt = client.task2_prompt or (app_settings.default_task2_prompt if app_settings else None)
        if not description_prompt:
            raise ValueError("Task 2 (Description) prompt not configured. Set a prompt in Client settings or global Settings.")

        system_prompt = client.system_prompt or (app_settings.default_system_prompt if app_settings else None)
        if not system_prompt:
            raise ValueError("System prompt not configured. Set a prompt in Client settings or global Settings.")

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

        # Get character limits from settings
        min_title_len = app_settings.task1_min_length if app_settings and app_settings.task1_min_length else 30
        max_title_len = app_settings.task1_max_length if app_settings and app_settings.task1_max_length else 60
        min_desc_len = app_settings.task2_min_length if app_settings and app_settings.task2_min_length else 2000
        max_desc_len = app_settings.task2_max_length if app_settings and app_settings.task2_max_length else 3000

        # Build system content: system prompt + brand context
        system_content = system_prompt
        if brand_context:
            system_content += "\n\n" + "\n".join(brand_context)

        # Build user content: task prompts + length requirements + product data
        user_content = f"""{title_prompt}

{description_prompt}

Character limits: Title must be {min_title_len}-{max_title_len} characters. Description must be {min_desc_len}-{max_desc_len} characters.

Product Information:
{chr(10).join(field_data)}"""

        if is_retry and previous_error:
            user_content += f"\n\n[Previous attempt failed: {previous_error}]"

        messages = [
            ("system", system_content),
            ("user", user_content),
        ]

        return ChatPromptTemplate.from_messages(messages)

    def build_title_prompt(
        self,
        product_group: ProductGroup,
        primary_product: Product,
        client: Client,
        app_settings: AppSettings | None = None,
        is_retry: bool = False,
        previous_error: str | None = None,
    ) -> ChatPromptTemplate:
        """
        Build prompt for Task 1 (Title Generation) only.

        Uses only: product_name, description, images as input fields.

        Args:
            product_group: The product group to generate title for
            primary_product: The primary product for accessing description/images
            client: Client with brand info and custom prompts
            app_settings: App settings with default prompts
            is_retry: Whether this is a retry attempt
            previous_error: Error message from previous attempt

        Returns:
            ChatPromptTemplate ready for invocation
        """
        # Build field context - only product_name, description, images
        field_data = []
        if product_group.product_name:
            field_data.append(f"Product Name: {product_group.product_name}")
        if primary_product.description:
            field_data.append(f"Description: {primary_product.description}")
        if primary_product.images:
            field_data.append(f"Images: {primary_product.images}")

        # Add variant info if multi-variant
        if product_group.variant_count > 1:
            field_data.append(f"Product Variants: {product_group.variant_count} options available")

        # Get title prompt (client custom > app defaults > error if not configured)
        title_prompt = client.task1_prompt or (app_settings.default_task1_prompt if app_settings else None)
        if not title_prompt:
            raise ValueError("Task 1 (Title) prompt not configured. Set a prompt in Client settings or global Settings.")

        system_prompt = client.system_prompt or (app_settings.default_system_prompt if app_settings else None)
        if not system_prompt:
            raise ValueError("System prompt not configured. Set a prompt in Client settings or global Settings.")

        # Get length limits from settings
        min_len = app_settings.task1_min_length if app_settings and app_settings.task1_min_length else 30
        max_len = app_settings.task1_max_length if app_settings and app_settings.task1_max_length else 60

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

        # Build system content: system prompt + brand context
        system_content = system_prompt
        if brand_context:
            system_content += "\n\n" + "\n".join(brand_context)

        # Build user content: task prompt + length requirement + product data
        user_content = f"""{title_prompt}

Character limit: {min_len}-{max_len} characters.

Product Information:
{chr(10).join(field_data)}"""

        if is_retry and previous_error:
            user_content += f"\n\n[Previous attempt failed: {previous_error}]"

        messages = [
            ("system", system_content),
            ("user", user_content),
        ]

        return ChatPromptTemplate.from_messages(messages)

    def build_description_prompt(
        self,
        product_group: ProductGroup,
        primary_product: Product,
        client: Client,
        app_settings: AppSettings | None = None,
        is_retry: bool = False,
        previous_error: str | None = None,
    ) -> ChatPromptTemplate:
        """
        Build prompt for Task 2 (Description Generation) only.

        Uses: product_name, description, images, country_of_origin as input fields.

        Args:
            product_group: The product group to generate description for
            primary_product: The primary product for accessing description/images
            client: Client with brand info and custom prompts
            app_settings: App settings with default prompts
            is_retry: Whether this is a retry attempt
            previous_error: Error message from previous attempt

        Returns:
            ChatPromptTemplate ready for invocation
        """
        # Build field context - product_name, description, images, country_of_origin
        field_data = []
        if product_group.product_name:
            field_data.append(f"Product Name: {product_group.product_name}")
        if primary_product.description:
            field_data.append(f"Description: {primary_product.description}")
        if primary_product.images:
            field_data.append(f"Images: {primary_product.images}")
        if primary_product.country_of_origin:
            field_data.append(f"Country Of Origin: {primary_product.country_of_origin}")

        # Add variant info if multi-variant
        if product_group.variant_count > 1:
            field_data.append(f"Product Variants: {product_group.variant_count} options available")

        # Get description prompt (client custom > app defaults > error if not configured)
        description_prompt = client.task2_prompt or (app_settings.default_task2_prompt if app_settings else None)
        if not description_prompt:
            raise ValueError("Task 2 (Description) prompt not configured. Set a prompt in Client settings or global Settings.")

        system_prompt = client.system_prompt or (app_settings.default_system_prompt if app_settings else None)
        if not system_prompt:
            raise ValueError("System prompt not configured. Set a prompt in Client settings or global Settings.")

        # Get length limits from settings
        min_len = app_settings.task2_min_length if app_settings and app_settings.task2_min_length else 2000
        max_len = app_settings.task2_max_length if app_settings and app_settings.task2_max_length else 3000

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

        # Build system content: system prompt + brand context
        system_content = system_prompt
        if brand_context:
            system_content += "\n\n" + "\n".join(brand_context)

        # Build user content: task prompt + length requirement + product data
        user_content = f"""{description_prompt}

Character limit: {min_len}-{max_len} characters.

Product Information:
{chr(10).join(field_data)}"""

        if is_retry and previous_error:
            user_content += f"\n\n[Previous attempt failed: {previous_error}]"

        messages = [
            ("system", system_content),
            ("user", user_content),
        ]

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

            except (ValidationError, ValueError) as e:
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

    async def generate_title(
        self,
        product_group: ProductGroup,
        primary_product: Product,
        client: Client,
        job: GenerationJob,
        app_settings: AppSettings | None = None,
        on_attempt: AttemptCallback | None = None,
    ) -> tuple[TitleContent | None, GenerationAudit]:
        """
        Generate title only (Task 1) for a product group with retry logic.

        Args:
            product_group: Product group to generate title for
            primary_product: Primary product for accessing description/images
            client: Client with settings
            job: Current generation job
            app_settings: App settings for defaults
            on_attempt: Optional callback called after each attempt with (attempt_number, success, error)

        Returns:
            Tuple of (TitleContent or None if failed, GenerationAudit)
        """
        last_audit = None
        last_error = None

        print(f"[AIService] Starting TITLE generation for product {product_group.id} (name: {product_group.product_name})")

        for attempt in range(1, self.MAX_RETRIES + 2):
            start_time = time.time()

            # Build title-only prompt
            prompt = self.build_title_prompt(
                product_group,
                primary_product,
                client,
                app_settings,
                is_retry=(attempt > 1),
                previous_error=last_error,
            )

            # Format prompt as string for audit
            formatted_messages = prompt.format_messages()
            prompt_str = "\n".join(
                f"[{m.type}] {m.content[:500]}..." if len(m.content) > 500 else f"[{m.type}] {m.content}"
                for m in formatted_messages
            )

            try:
                print(f"[AIService] Title attempt {attempt}: Invoking model...")
                cache_key = str(client.id) if client else None
                raw_result = await self._invoke_title_with_retry(prompt, cache_key=cache_key)
                print(f"[AIService] Title attempt {attempt}: Model returned result")

                raw_message = raw_result.get("raw")
                result = raw_result.get("parsed")
                parsing_error = raw_result.get("parsing_error")

                # Check if parsing failed (e.g., character count validation)
                if result is None:
                    # parsing_error is an Exception object - convert to string
                    error_msg = str(parsing_error) if parsing_error else "Model returned invalid response - parsing failed"
                    print(f"[AIService] Title parsing failed: {error_msg}")
                    raise ValueError(error_msg)

                # Validate title length against settings
                min_len = app_settings.task1_min_length if app_settings and app_settings.task1_min_length else 30
                max_len = app_settings.task1_max_length if app_settings and app_settings.task1_max_length else 60
                char_count = len(result.title)
                if not min_len <= char_count <= max_len:
                    raise ValueError(f"Title must be {min_len}-{max_len} characters, got {char_count}")

                # Get token usage
                usage = {}
                if raw_message and hasattr(raw_message, "response_metadata"):
                    usage = raw_message.response_metadata.get("token_usage", {})

                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                prompt_details = usage.get("prompt_tokens_details", {})
                cached_input_tokens = prompt_details.get("cached_tokens", 0) if prompt_details else 0

                if input_tokens == 0:
                    input_tokens = self.cost_tracker.count_tokens(prompt_str)
                if output_tokens == 0:
                    output_tokens = self.cost_tracker.count_tokens(result.title)

                cost = self.cost_tracker.add_usage(input_tokens, output_tokens, cached_input_tokens)
                duration_ms = int((time.time() - start_time) * 1000)

                # Create successful audit for title
                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=True,
                    generated_title=result.title,
                    generated_description=None,  # Title only
                    title_length=len(result.title),
                    description_length=0,
                    prompt_used=prompt_str[:10000],
                    model_version=self.model_name,
                    temperature=Decimal(str(self.temperature)),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    duration_ms=duration_ms,
                )
                self.db.add(audit)

                # Notify callback of successful attempt
                print(f"[AIService] Title SUCCESS - on_attempt is {on_attempt}, calling callback for attempt {attempt}")
                if on_attempt:
                    await on_attempt(attempt, True, None)
                    print(f"[AIService] Title SUCCESS - callback completed")
                else:
                    print(f"[AIService] Title SUCCESS - NO CALLBACK PROVIDED")

                return result, audit

            except (ValidationError, ValueError) as e:
                last_error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)

                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=False,
                    error_message=f"Validation error: {last_error}",
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

                # Notify callback of failed attempt (validation error)
                if on_attempt:
                    await on_attempt(attempt, False, f"Validation error: {last_error}")

                if attempt >= self.MAX_RETRIES + 1:
                    return None, audit

            except Exception as e:
                print(f"[AIService] Title API error for product {product_group.id}: {e}")
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

                # Notify callback of failed attempt (API error)
                if on_attempt:
                    await on_attempt(attempt, False, f"API error: {last_error}")

                if attempt >= self.MAX_RETRIES + 1:
                    return None, audit

        return None, last_audit

    async def generate_description(
        self,
        product_group: ProductGroup,
        primary_product: Product,
        client: Client,
        job: GenerationJob,
        app_settings: AppSettings | None = None,
        on_attempt: AttemptCallback | None = None,
    ) -> tuple[DescriptionContent | None, GenerationAudit]:
        """
        Generate description only (Task 2) for a product group with retry logic.

        Args:
            product_group: Product group to generate description for
            primary_product: Primary product for accessing description/images
            client: Client with settings
            job: Current generation job
            app_settings: App settings for defaults
            on_attempt: Optional callback called after each attempt with (attempt_number, success, error)

        Returns:
            Tuple of (DescriptionContent or None if failed, GenerationAudit)
        """
        last_audit = None
        last_error = None

        print(f"[AIService] Starting DESCRIPTION generation for product {product_group.id} (name: {product_group.product_name})")

        for attempt in range(1, self.MAX_RETRIES + 2):
            start_time = time.time()

            # Build description-only prompt
            prompt = self.build_description_prompt(
                product_group,
                primary_product,
                client,
                app_settings,
                is_retry=(attempt > 1),
                previous_error=last_error,
            )

            # Format prompt as string for audit
            formatted_messages = prompt.format_messages()
            prompt_str = "\n".join(
                f"[{m.type}] {m.content[:500]}..." if len(m.content) > 500 else f"[{m.type}] {m.content}"
                for m in formatted_messages
            )

            try:
                print(f"[AIService] Description attempt {attempt}: Invoking model...")
                cache_key = str(client.id) if client else None
                raw_result = await self._invoke_description_with_retry(prompt, cache_key=cache_key)
                print(f"[AIService] Description attempt {attempt}: Model returned result")

                raw_message = raw_result.get("raw")
                result = raw_result.get("parsed")
                parsing_error = raw_result.get("parsing_error")

                # Check if parsing failed (e.g., character count validation)
                if result is None:
                    # parsing_error is an Exception object - convert to string
                    error_msg = str(parsing_error) if parsing_error else "Model returned invalid response - parsing failed"
                    print(f"[AIService] Description parsing failed: {error_msg}")
                    raise ValueError(error_msg)

                # Validate description length against settings
                min_len = app_settings.task2_min_length if app_settings and app_settings.task2_min_length else 2000
                max_len = app_settings.task2_max_length if app_settings and app_settings.task2_max_length else 3000
                char_count = len(result.description)
                if not min_len <= char_count <= max_len:
                    raise ValueError(f"Description must be {min_len}-{max_len} characters, got {char_count}")

                # Get token usage
                usage = {}
                if raw_message and hasattr(raw_message, "response_metadata"):
                    usage = raw_message.response_metadata.get("token_usage", {})

                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)
                prompt_details = usage.get("prompt_tokens_details", {})
                cached_input_tokens = prompt_details.get("cached_tokens", 0) if prompt_details else 0

                if input_tokens == 0:
                    input_tokens = self.cost_tracker.count_tokens(prompt_str)
                if output_tokens == 0:
                    output_tokens = self.cost_tracker.count_tokens(result.description)

                cost = self.cost_tracker.add_usage(input_tokens, output_tokens, cached_input_tokens)
                duration_ms = int((time.time() - start_time) * 1000)

                # Create successful audit for description
                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=True,
                    generated_title=None,  # Description only
                    generated_description=result.description,
                    title_length=0,
                    description_length=len(result.description),
                    prompt_used=prompt_str[:10000],
                    model_version=self.model_name,
                    temperature=Decimal(str(self.temperature)),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                    cost=cost,
                    duration_ms=duration_ms,
                )
                self.db.add(audit)

                # Notify callback of successful attempt
                print(f"[AIService] Description SUCCESS - on_attempt is {on_attempt}, calling callback for attempt {attempt}")
                if on_attempt:
                    await on_attempt(attempt, True, None)
                    print(f"[AIService] Description SUCCESS - callback completed")
                else:
                    print(f"[AIService] Description SUCCESS - NO CALLBACK PROVIDED")

                return result, audit

            except (ValidationError, ValueError) as e:
                last_error = str(e)
                duration_ms = int((time.time() - start_time) * 1000)

                audit = GenerationAudit(
                    job_id=job.id,
                    product_group_id=product_group.id,
                    attempt_number=attempt,
                    success=False,
                    error_message=f"Validation error: {last_error}",
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

                # Notify callback of failed attempt (validation error)
                if on_attempt:
                    await on_attempt(attempt, False, f"Validation error: {last_error}")

                if attempt >= self.MAX_RETRIES + 1:
                    return None, audit

            except Exception as e:
                print(f"[AIService] Description API error for product {product_group.id}: {e}")
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

                # Notify callback of failed attempt (API error)
                if on_attempt:
                    await on_attempt(attempt, False, f"API error: {last_error}")

                if attempt >= self.MAX_RETRIES + 1:
                    return None, audit

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

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    async def _invoke_title_with_retry(self, prompt: ChatPromptTemplate, cache_key: str | None = None) -> dict:
        """
        Invoke the title model with retry logic for rate limits.

        Returns dict with 'raw' (AIMessage) and 'parsed' (TitleContent) keys.
        """
        formatted_messages = prompt.format_messages()
        invoke_kwargs = {}
        if cache_key:
            invoke_kwargs["prompt_cache_key"] = cache_key
        return await self.title_model.ainvoke(formatted_messages, **invoke_kwargs)

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    async def _invoke_description_with_retry(self, prompt: ChatPromptTemplate, cache_key: str | None = None) -> dict:
        """
        Invoke the description model with retry logic for rate limits.

        Returns dict with 'raw' (AIMessage) and 'parsed' (DescriptionContent) keys.
        """
        formatted_messages = prompt.format_messages()
        invoke_kwargs = {}
        if cache_key:
            invoke_kwargs["prompt_cache_key"] = cache_key
        return await self.description_model.ainvoke(formatted_messages, **invoke_kwargs)

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
