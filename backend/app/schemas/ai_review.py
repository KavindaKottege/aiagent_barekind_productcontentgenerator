"""AI review schemas for structured review results."""

from pydantic import BaseModel, Field
from typing import Literal


class AIReviewResult(BaseModel):
    """Structured AI review result with safety checks."""

    recommendation: Literal["approve", "reject"] = Field(
        description="Whether to approve or reject the generated content"
    )
    reason: str = Field(
        max_length=200,
        description="Brief reason for recommendation (max 2 lines)"
    )
    safety_flags: list[str] = Field(
        default_factory=list,
        description="List of safety concerns: quantity_confusion, misleading_expectations, misrepresentation"
    )
    accuracy_score: float = Field(
        ge=0.0, le=1.0,
        description="Accuracy score from 0.0 to 1.0"
    )


class AIReviewRequest(BaseModel):
    """Request for single product AI review."""
    product_group_id: str


class BatchAIReviewRequest(BaseModel):
    """Request for batch AI review."""
    client_id: str
    auto_approve: bool = False  # When True, sets review_status directly (AI-auto mode)
