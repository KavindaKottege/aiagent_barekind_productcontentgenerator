"""AI review service using LangChain with structured output."""

import time
from decimal import Decimal

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import (
    retry,
    stop_after_attempt,
    wait_random_exponential,
)

from app.models.product import Product
from app.models.product_group import ProductGroup
from app.schemas.ai_review import AIReviewResult
from app.services.cost_tracker import CostTracker


class AIReviewService:
    """
    Service for reviewing AI-generated product content.

    Handles:
    - Accuracy evaluation against original data
    - Safety flag detection (quantity confusion, misleading expectations)
    - Structured output with LangChain
    - Token counting and cost tracking
    - Retry logic for rate limits
    """

    def __init__(
        self,
        db: AsyncSession,
        api_key: str,
        model: str = "gpt-5.2",
        temperature: float = 0.3,
    ):
        """Initialize the AI review service."""
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
            )
            # Enable structured output with Pydantic validation
            self._model = base_model.with_structured_output(
                AIReviewResult,
                strict=True,
            )
        return self._model

    def build_review_prompt(
        self,
        product_group: ProductGroup,
        products: list[Product],
    ) -> ChatPromptTemplate:
        """
        Build review prompt with original data and generated content.

        Args:
            product_group: The product group with generated content
            products: List of variant products with original data

        Returns:
            ChatPromptTemplate ready for invocation
        """
        # Aggregate original data from products (use first product as primary source)
        primary_product = products[0] if products else None

        # Build original data section
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

            # Image count
            image_count = len(primary_product.images) if primary_product.images else 0
            original_data.append(f"Images Available: {image_count} images")

        # Add variant info if multi-variant
        if len(products) > 1:
            original_data.append(f"\nProduct has {len(products)} variants:")
            for i, prod in enumerate(products[:5], 1):  # Show max 5 variants
                variant_info = f"  {i}. {prod.option_name or 'No option name'}"
                if prod.sku:
                    variant_info += f" (SKU: {prod.sku})"
                original_data.append(variant_info)
            if len(products) > 5:
                original_data.append(f"  ... and {len(products) - 5} more variants")

        original_data_str = "\n".join(original_data) if original_data else "No original data available"

        # Build generated content section
        generated_title = product_group.generated_title or "[No title generated]"
        generated_description = product_group.generated_description or "[No description generated]"

        # Build the review prompt
        messages = [
            ("system", """You are reviewing AI-generated product content for accuracy and safety.

Your job is to evaluate whether the generated content accurately represents the original product data
and to flag any safety concerns that could mislead or confuse buyers."""),
            ("system", f"""ORIGINAL PRODUCT DATA:
{original_data_str}

GENERATED CONTENT:
Title: {generated_title}
Description: {generated_description}"""),
            ("system", """CRITICAL SAFETY CHECKS (flag ANY of these):

1. QUANTITY CONFUSION: Does the description clearly indicate if this is a single item or a set/pack?
   - Look for words like "set of", "pack of", "includes X pieces"
   - If original data suggests multiple items, generated content MUST make this clear
   - Flag if a buyer might be confused about how many items they're receiving

2. MISLEADING EXPECTATIONS: Does the description accurately represent what the buyer will receive?
   - Check if any features are exaggerated or invented
   - Verify claims match the original product data
   - Flag if buyer expectations might not match reality

3. MISREPRESENTATION: Does the generated title fairly represent the original product name?
   - The AI title should be an improvement, not a reinvention
   - Key product identifiers should be preserved
   - Flag if the original product identity is lost

EVALUATION CRITERIA:
- If ANY safety flag is triggered, you MUST recommend "reject"
- Provide a brief reason (max 2 lines) explaining your decision
- Give an accuracy score from 0.0 to 1.0 (1.0 = perfect match, 0.0 = completely wrong)
- List all applicable safety flags in the safety_flags array

Evaluate the generated content now."""),
        ]

        return ChatPromptTemplate.from_messages(messages)

    async def review_product(
        self,
        product_group: ProductGroup,
        products: list[Product],
    ) -> tuple[AIReviewResult, Decimal]:
        """
        Review a product group's generated content.

        Args:
            product_group: Product group with generated content to review
            products: List of variant products with original data

        Returns:
            Tuple of (AIReviewResult, cost)
        """
        start_time = time.time()

        # Build review prompt
        prompt = self.build_review_prompt(product_group, products)

        # Format prompt as string for token counting
        prompt_str = "\n".join(
            f"[{m[0]}] {m[1]}" for m in prompt.messages
        )

        # Call the model with retry logic
        result = await self._invoke_with_retry(prompt)

        # Get token usage from response metadata
        usage = getattr(result, "response_metadata", {}).get("token_usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        # If no token info in metadata, estimate with tiktoken
        if input_tokens == 0:
            input_tokens = self.cost_tracker.count_tokens(prompt_str)
        if output_tokens == 0:
            # Estimate output tokens from result
            output_str = f"{result.recommendation} {result.reason} {' '.join(result.safety_flags)}"
            output_tokens = self.cost_tracker.count_tokens(output_str)

        # Calculate cost
        cost = self.cost_tracker.add_usage(input_tokens, output_tokens)

        return result, cost

    @retry(
        stop=stop_after_attempt(4),
        wait=wait_random_exponential(multiplier=1, min=4, max=60),
        reraise=True,
    )
    async def _invoke_with_retry(self, prompt: ChatPromptTemplate) -> AIReviewResult:
        """
        Invoke the model with retry logic for rate limits.

        Uses tenacity for exponential backoff on API errors.
        """
        return await self.model.ainvoke(prompt.messages)
