"""Cost tracking service using tiktoken for accurate token counting."""

from decimal import Decimal
from typing import Any

import tiktoken


class CostTracker:
    """
    Tracks tokens and costs for AI generation jobs.

    Uses tiktoken for accurate token counting and stores running totals
    for real-time cost display and soft cap enforcement.
    """

    # GPT-5.2 pricing (per 1M tokens) - update if pricing changes
    # Source: https://platform.openai.com/docs/pricing (Jan 2026)
    PRICING = {
        "gpt-5.2": {
            "input": Decimal("1.75"),  # $1.75 per 1M input tokens
            "output": Decimal("14.00"),  # $14.00 per 1M output tokens
        },
        # Fallback for unknown models
        "default": {
            "input": Decimal("2.00"),
            "output": Decimal("15.00"),
        },
    }

    TOKENS_PER_MILLION = Decimal("1_000_000")

    def __init__(self, model: str = "gpt-5.2"):
        """Initialize cost tracker for specified model."""
        self.model = model
        self._encoding = None  # Lazy load

        # Running totals
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_generations = 0
        self.total_cost = Decimal("0")

    @property
    def encoding(self) -> tiktoken.Encoding:
        """Lazy-load tiktoken encoding for the model."""
        if self._encoding is None:
            try:
                # Try model-specific encoding
                self._encoding = tiktoken.encoding_for_model(self.model)
            except KeyError:
                # Fallback to cl100k_base (GPT-4 family) or o200k_base (newer models)
                # GPT-5.2 likely uses o200k_base
                try:
                    self._encoding = tiktoken.get_encoding("o200k_base")
                except Exception:
                    self._encoding = tiktoken.get_encoding("cl100k_base")
        return self._encoding

    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken."""
        if not text:
            return 0
        return len(self.encoding.encode(text))

    def count_message_tokens(self, messages: list[dict[str, Any]]) -> int:
        """
        Count tokens in a list of chat messages.

        Includes overhead for message formatting (role, content structure).
        """
        total = 0
        for message in messages:
            # Each message has ~4 token overhead for formatting
            total += 4
            for key, value in message.items():
                if isinstance(value, str):
                    total += self.count_tokens(value)
        # Add 2 tokens for reply priming
        total += 2
        return total

    def get_pricing(self) -> dict[str, Decimal]:
        """Get pricing for current model."""
        return self.PRICING.get(self.model, self.PRICING["default"])

    def calculate_cost(self, input_tokens: int, output_tokens: int) -> Decimal:
        """Calculate cost for given token counts."""
        pricing = self.get_pricing()
        input_cost = (Decimal(input_tokens) / self.TOKENS_PER_MILLION) * pricing["input"]
        output_cost = (Decimal(output_tokens) / self.TOKENS_PER_MILLION) * pricing["output"]
        return input_cost + output_cost

    def add_usage(self, input_tokens: int, output_tokens: int) -> Decimal:
        """
        Add token usage from a generation and return the cost.

        Updates running totals and returns cost for this generation.
        """
        cost = self.calculate_cost(input_tokens, output_tokens)

        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.total_generations += 1
        self.total_cost += cost

        return cost

    def average_cost_per_generation(self) -> Decimal:
        """Calculate running average cost per product."""
        if self.total_generations == 0:
            return Decimal("0")
        return self.total_cost / Decimal(self.total_generations)

    def projected_total_cost(self, total_products: int) -> Decimal:
        """
        Project total cost based on running average.

        Args:
            total_products: Total number of products to generate

        Returns:
            Projected total cost for entire job
        """
        if self.total_generations == 0:
            # No data yet, use rough estimate (~$0.02 per product)
            return Decimal(total_products) * Decimal("0.02")

        avg_cost = self.average_cost_per_generation()
        remaining = total_products - self.total_generations
        return self.total_cost + (avg_cost * Decimal(remaining))

    def check_soft_cap(self, soft_cap: Decimal) -> bool:
        """Check if current cost exceeds or equals soft cap."""
        return self.total_cost >= soft_cap

    def format_cost(self, cost: Decimal) -> str:
        """Format cost as currency string."""
        return f"${cost:.2f}"

    def to_dict(self) -> dict:
        """Export tracking data for storage/display."""
        return {
            "model": self.model,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_generations": self.total_generations,
            "total_cost": float(self.total_cost),
            "average_cost": float(self.average_cost_per_generation()),
        }

    def reset(self) -> None:
        """Reset all counters (for new job)."""
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_generations = 0
        self.total_cost = Decimal("0")
