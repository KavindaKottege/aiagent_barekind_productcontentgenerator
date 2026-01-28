"""Review schemas for review workflow."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


class ProductGroupReview(BaseModel):
    """Response schema for product group in review UI."""

    id: UUID
    product_name: str
    product_token: str
    sku: str
    variant_count: int
    generated_title: str | None
    generated_description: str | None
    edited_title: str | None
    edited_description: str | None
    status: str  # pending, generated, etc.
    review_status: str | None  # approved, rejected, edited
    ai_review_status: str | None  # ai_approved, ai_rejected
    ai_review_reason: str | None
    ai_review_safety_flags: list[str]
    images: list[str]  # from first product in group
    original_data: dict  # product fields for collapsible panel
    row_index: int
    reviewed_at: datetime | None
    ai_reviewed_at: datetime | None

    model_config = {"from_attributes": True}


class ReviewActionRequest(BaseModel):
    """Request schema for approve/reject actions."""

    product_group_id: UUID
    action: Literal["approve", "reject"]


class EditContentRequest(BaseModel):
    """Request schema for saving edited content.

    Both fields are optional - only provided fields will be updated.
    Validation only applies to fields that are provided.
    """

    product_group_id: UUID
    edited_title: str | None = None
    edited_description: str | None = None

    @field_validator("edited_title")
    @classmethod
    def validate_title_length(cls, v: str | None) -> str | None:
        """Validate title character count if provided."""
        if v is not None and not (30 <= len(v) <= 60):
            raise ValueError("Title must be between 30 and 60 characters")
        return v

    @field_validator("edited_description")
    @classmethod
    def validate_description_length(cls, v: str | None) -> str | None:
        """Validate description character count if provided."""
        if v is not None and not (2000 <= len(v) <= 3000):
            raise ValueError("Description must be between 2000 and 3000 characters")
        return v


class ReviewActionResponse(BaseModel):
    """Response schema for review actions."""

    success: bool
    message: str
    next_product_id: UUID | None = None


class ReviewStatsResponse(BaseModel):
    """Response schema for review statistics."""

    total_generated: int
    pending_review: int
    manually_approved: int
    manually_rejected: int
    ai_approved: int
    ai_rejected: int
    edited: int


class UndoReviewRequest(BaseModel):
    """Request schema for undoing a review action."""

    product_group_id: UUID
    previous_status: str | None = None
