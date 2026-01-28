"""AI review service using LangChain with structured output."""

import time
from decimal import Decimal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from app.models.client import Client
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.schemas.ai_review import TitleReviewResult, DescriptionReviewResult, CombinedReviewResult
from app.services.cost_tracker import CostTracker


class AIReviewService:
    """
    Service for reviewing AI-generated product content.

    Handles:
    - Task 3: Title review with suggested corrections
    - Task 4: Description review with suggested corrections
    - Structured output with LangChain
    - Token counting and cost tracking
    - Retry logic for rate limits
    """

    def __init__(
        self,
        db: AsyncSession,
        api_key: str,
        model: str = "gpt-4o-mini",
        temperature: float = 0.3,
    ):
        """Initialize the AI review service."""
        self.db = db
        self.api_key = api_key
        self.model_name = model
        self.temperature = temperature
        self.cost_tracker = CostTracker(model)

        # Lazy-loaded models
        self._title_review_model = None
        self._description_review_model = None

    @property
    def title_review_model(self) -> ChatOpenAI:
        """Lazy-load the title review model (Task 3)."""
        if self._title_review_model is None:
            base_model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key,
            )
            self._title_review_model = base_model.with_structured_output(
                TitleReviewResult,
                strict=True,
            )
        return self._title_review_model

    @property
    def description_review_model(self) -> ChatOpenAI:
        """Lazy-load the description review model (Task 4)."""
        if self._description_review_model is None:
            base_model = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.api_key,
            )
            self._description_review_model = base_model.with_structured_output(
                DescriptionReviewResult,
                strict=True,
            )
        return self._description_review_model

    def _build_brand_context(self, client: Client) -> str:
        """Build brand context string from client data."""
        brand_context = []
        if client.brand_name:
            brand_context.append(f"Brand Name: {client.brand_name}")
        if client.story:
            brand_context.append(f"Brand Story: {client.story}")
        if client.tone:
            brand_context.append(f"Brand Tone: {client.tone}")
        if client.guidelines:
            brand_context.append(f"Brand Guidelines: {client.guidelines}")
        return "\n".join(brand_context) if brand_context else "No brand information available"

    def _build_original_data(self, products: list[Product]) -> str:
        """Build original product data string."""
        primary_product = products[0] if products else None
        original_data = []

        if primary_product:
            if primary_product.product_name:
                original_data.append(f"Product Name: {primary_product.product_name}")
            if primary_product.description:
                original_data.append(f"Description: {primary_product.description}")
            if primary_product.product_type:
                original_data.append(f"Product Type: {primary_product.product_type}")
            if primary_product.option_name:
                original_data.append(f"Option/Variant: {primary_product.option_name}")
            if primary_product.country_of_origin:
                original_data.append(f"Country of Origin: {primary_product.country_of_origin}")
            if primary_product.made_to_order is not None:
                original_data.append(f"Made to Order: {primary_product.made_to_order}")
            if primary_product.sku:
                original_data.append(f"SKU: {primary_product.sku}")

            image_count = len(primary_product.images) if primary_product.images else 0
            original_data.append(f"Images Available: {image_count} images")

        if len(products) > 1:
            original_data.append(f"\nProduct has {len(products)} variants:")
            for i, prod in enumerate(products[:5], 1):
                variant_info = f"  {i}. {prod.option_name or 'No option name'}"
                if prod.sku:
                    variant_info += f" (SKU: {prod.sku})"
                original_data.append(variant_info)
            if len(products) > 5:
                original_data.append(f"  ... and {len(products) - 5} more variants")

        return "\n".join(original_data) if original_data else "No original data available"

    def build_title_review_prompt(
        self,
        product_group: ProductGroup,
        products: list[Product],
        client: Client,
        app_settings: AppSettings | None = None,
    ) -> ChatPromptTemplate:
        """Build prompt for Task 3 - title review only."""
        # System prompt is required
        system_prompt = client.system_prompt or (app_settings.default_system_prompt if app_settings else None)
        if not system_prompt:
            raise ValueError("System prompt not configured. Set a prompt in Client settings or global Settings.")

        # Task 3 prompt - from settings only (no client override for review tasks)
        task3_prompt = app_settings.default_task3_prompt if app_settings else None
        if not task3_prompt:
            raise ValueError("Task 3 (Title Review) prompt not configured. Please set a prompt in Settings.")

        brand_context_str = self._build_brand_context(client)
        original_data_str = self._build_original_data(products)
        generated_title = product_group.generated_title or "[No title generated]"

        # Build system content: system prompt + brand context
        system_content = system_prompt + "\n\n" + brand_context_str

        # Build user content: task prompt + original data + generated title
        user_content = f"""{task3_prompt}

Original Product Data:
{original_data_str}

Generated Title to Review:
{generated_title}"""

        messages = [
            ("system", system_content),
            ("user", user_content),
        ]

        return ChatPromptTemplate.from_messages(messages)

    def build_description_review_prompt(
        self,
        product_group: ProductGroup,
        products: list[Product],
        client: Client,
        app_settings: AppSettings | None = None,
    ) -> ChatPromptTemplate:
        """Build prompt for Task 4 - description review only."""
        # System prompt is required
        system_prompt = client.system_prompt or (app_settings.default_system_prompt if app_settings else None)
        if not system_prompt:
            raise ValueError("System prompt not configured. Set a prompt in Client settings or global Settings.")

        # Task 4 prompt - from settings only (no client override for review tasks)
        task4_prompt = app_settings.default_task4_prompt if app_settings else None
        if not task4_prompt:
            raise ValueError("Task 4 (Description Review) prompt not configured. Please set a prompt in Settings.")

        brand_context_str = self._build_brand_context(client)
        original_data_str = self._build_original_data(products)
        generated_description = product_group.generated_description or "[No description generated]"

        # Build system content: system prompt + brand context
        system_content = system_prompt + "\n\n" + brand_context_str

        # Build user content: task prompt + original data + generated description
        user_content = f"""{task4_prompt}

Original Product Data:
{original_data_str}

Generated Description to Review:
{generated_description}"""

        messages = [
            ("system", system_content),
            ("user", user_content),
        ]

        return ChatPromptTemplate.from_messages(messages)

    async def review_title(
        self,
        product_group: ProductGroup,
        products: list[Product],
        client: Client,
        app_settings: AppSettings | None = None,
    ) -> tuple[TitleReviewResult, Decimal]:
        """
        Task 3: Review a product's generated title.

        Args:
            product_group: Product group with generated title
            products: List of variant products with original data
            client: Client/brand information
            app_settings: App settings with Task 3 prompt

        Returns:
            Tuple of (TitleReviewResult, cost)
        """
        prompt = self.build_title_review_prompt(product_group, products, client, app_settings)
        formatted_messages = prompt.format_messages()
        prompt_str = "\n".join(f"[{m.type}] {m.content}" for m in formatted_messages)

        result = await self._invoke_title_review_with_retry(prompt)

        # Estimate tokens
        input_tokens = self.cost_tracker.count_tokens(prompt_str)
        output_str = f"{result.recommendation} {result.reason} {result.suggested_title}"
        output_tokens = self.cost_tracker.count_tokens(output_str)

        print(f"[Task 3 - Title Review] Tokens - input: {input_tokens}, output: {output_tokens}")

        cost = self.cost_tracker.add_usage(input_tokens, output_tokens)
        print(f"[Task 3 - Title Review] Cost: ${cost:.6f}, total: ${self.cost_tracker.total_cost:.6f}")

        return result, cost

    async def review_description(
        self,
        product_group: ProductGroup,
        products: list[Product],
        client: Client,
        app_settings: AppSettings | None = None,
    ) -> tuple[DescriptionReviewResult, Decimal]:
        """
        Task 4: Review a product's generated description.

        Args:
            product_group: Product group with generated description
            products: List of variant products with original data
            client: Client/brand information
            app_settings: App settings with Task 4 prompt

        Returns:
            Tuple of (DescriptionReviewResult, cost)
        """
        prompt = self.build_description_review_prompt(product_group, products, client, app_settings)
        formatted_messages = prompt.format_messages()
        prompt_str = "\n".join(f"[{m.type}] {m.content}" for m in formatted_messages)

        result = await self._invoke_description_review_with_retry(prompt)

        # Estimate tokens
        input_tokens = self.cost_tracker.count_tokens(prompt_str)
        output_str = f"{result.recommendation} {result.reason} {result.suggested_description[:500] if result.suggested_description else ''}"
        output_tokens = self.cost_tracker.count_tokens(output_str)

        print(f"[Task 4 - Description Review] Tokens - input: {input_tokens}, output: {output_tokens}")

        cost = self.cost_tracker.add_usage(input_tokens, output_tokens)
        print(f"[Task 4 - Description Review] Cost: ${cost:.6f}, total: ${self.cost_tracker.total_cost:.6f}")

        return result, cost

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    async def _invoke_title_review_with_retry(self, prompt: ChatPromptTemplate) -> TitleReviewResult:
        """Invoke title review model with retry logic."""
        formatted_messages = prompt.format_messages()
        return await self.title_review_model.ainvoke(formatted_messages)

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    async def _invoke_description_review_with_retry(self, prompt: ChatPromptTemplate) -> DescriptionReviewResult:
        """Invoke description review model with retry logic."""
        formatted_messages = prompt.format_messages()
        return await self.description_review_model.ainvoke(formatted_messages)

    async def review_product(
        self,
        product_group: ProductGroup,
        products: list[Product],
    ) -> tuple[CombinedReviewResult, Decimal]:
        """
        Review a product's generated title and description.

        This method fetches the required client and app_settings from the database,
        then calls both review_title() and review_description(), combining the results.

        Args:
            product_group: Product group with generated title and description
            products: List of variant products with original data

        Returns:
            Tuple of (CombinedReviewResult, total_cost)
        """
        # Fetch client from database
        result = await self.db.execute(
            select(Client).where(Client.id == product_group.client_id)
        )
        client = result.scalar_one_or_none()
        if not client:
            raise ValueError(f"Client not found for product group {product_group.id}")

        # Fetch app_settings (id=1)
        result = await self.db.execute(
            select(AppSettings).where(AppSettings.id == 1)
        )
        app_settings = result.scalar_one_or_none()

        # Task 3: Review title
        title_result, title_cost = await self.review_title(
            product_group, products, client, app_settings
        )

        # Task 4: Review description
        desc_result, desc_cost = await self.review_description(
            product_group, products, client, app_settings
        )

        # Combine results - reject if either task rejects
        title_approved = title_result.recommendation == "approve"
        desc_approved = desc_result.recommendation == "approve"
        both_approved = title_approved and desc_approved

        recommendation = "approve" if both_approved else "reject"

        # Combine reasons
        reasons = []
        if not title_approved:
            reasons.append(f"Title: {title_result.reason}")
        if not desc_approved:
            reasons.append(f"Description: {desc_result.reason}")
        combined_reason = " | ".join(reasons) if reasons else "Content approved"

        # Combine safety flags
        combined_flags = list(set(title_result.safety_flags + desc_result.safety_flags))

        # Average accuracy score
        accuracy_score = (title_result.accuracy_score + desc_result.accuracy_score) / 2

        # Suggestions only if that task rejected
        suggested_title = title_result.suggested_title if not title_approved else None
        suggested_description = desc_result.suggested_description if not desc_approved else None

        combined_result = CombinedReviewResult(
            recommendation=recommendation,
            reason=combined_reason[:500],  # Truncate to fit
            safety_flags=combined_flags,
            accuracy_score=accuracy_score,
            suggested_title=suggested_title,
            suggested_description=suggested_description,
        )

        total_cost = title_cost + desc_cost

        return combined_result, total_cost
