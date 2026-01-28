"""AI review schemas for structured review results."""

from pydantic import BaseModel, Field
from typing import Literal


class TitleReviewResult(BaseModel):
    """Task 3: Title review result with suggested correction."""

    recommendation: Literal["approve", "reject"] = Field(
        description="Whether to approve or reject the generated title"
    )
    reason: str = Field(
        max_length=200,
        description="Brief reason for recommendation (max 2 lines)"
    )
    safety_flags: list[str] = Field(
        description="List of safety concerns (empty array if none): misrepresentation, brand_misalignment"
    )
    accuracy_score: float = Field(
        ge=0.0, le=1.0,
        description="Accuracy score from 0.0 to 1.0"
    )
    suggested_title: str = Field(
        description="Corrected title if rejecting. If approving, return the original title unchanged."
    )


class DescriptionReviewResult(BaseModel):
    """Task 4: Description review result with suggested correction."""

    recommendation: Literal["approve", "reject"] = Field(
        description="Whether to approve or reject the generated description"
    )
    reason: str = Field(
        max_length=200,
        description="Brief reason for recommendation (max 2 lines)"
    )
    safety_flags: list[str] = Field(
        description="List of safety concerns (empty array if none): quantity_confusion, misleading_expectations, brand_misalignment"
    )
    accuracy_score: float = Field(
        ge=0.0, le=1.0,
        description="Accuracy score from 0.0 to 1.0"
    )
    suggested_description: str = Field(
        description="Corrected description if rejecting. If approving, return the original description unchanged."
    )


class CombinedReviewResult(BaseModel):
    """Combined result from title and description review."""

    recommendation: Literal["approve", "reject"] = Field(
        description="Overall recommendation - reject if either title or description is rejected"
    )
    reason: str = Field(
        description="Combined reason from title and/or description review"
    )
    safety_flags: list[str] = Field(
        description="Combined safety flags from both reviews"
    )
    accuracy_score: float = Field(
        ge=0.0, le=1.0,
        description="Average accuracy score from both reviews"
    )
    suggested_title: str | None = Field(
        default=None,
        description="Suggested title correction if title was rejected"
    )
    suggested_description: str | None = Field(
        default=None,
        description="Suggested description correction if description was rejected"
    )


class AIReviewRequest(BaseModel):
    """Request for single product AI review."""
    product_group_id: str


class BatchAIReviewRequest(BaseModel):
    """Request for batch AI review."""
    auto_approve: bool = False  # When True, sets review_status directly (AI-auto mode)
    force_rerun: bool = False  # When True, resets and re-reviews all products
