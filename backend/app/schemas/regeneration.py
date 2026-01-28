"""Pydantic schemas for smart regeneration."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

# Predefined rejection reasons (from CONTEXT.md decisions)
RejectionReasonType = Literal[
    "off_brand_tone",
    "generic_boring",
    "factually_wrong",
    "seo_issues",
]

# Human-readable labels for frontend display
REJECTION_REASON_LABELS = {
    "off_brand_tone": "Off-brand tone",
    "generic_boring": "Generic/boring",
    "factually_wrong": "Factually wrong",
    "seo_issues": "SEO issues",
}


class RejectWithReasonsRequest(BaseModel):
    """Request to reject product with optional feedback reasons."""

    product_group_id: UUID
    rejection_reasons: list[RejectionReasonType] = []  # Optional, can be empty


# --- Regeneration Context schemas (06-03) ---

# Mapping from rejection reasons to positive guidance for regeneration prompts
REASON_TO_POSITIVE_GUIDANCE = {
    "off_brand_tone": "authentic brand voice and personality",
    "generic_boring": "unique, specific, engaging details",
    "factually_wrong": "accuracy and truthfulness to original data",
    "seo_issues": "natural keyword integration and SEO best practices",
}


def get_positive_guidance(reasons: list[str]) -> str:
    """Convert rejection reasons to positive guidance phrases.

    Takes a list of rejection reason keys and returns a comma-separated
    string of positive guidance that the AI should focus on.

    Args:
        reasons: List of RejectionReasonType string values.

    Returns:
        Comma-separated positive guidance string, or empty string if no matches.
    """
    guidance = []
    for reason in reasons:
        if reason in REASON_TO_POSITIVE_GUIDANCE:
            guidance.append(REASON_TO_POSITIVE_GUIDANCE[reason])
    return ", ".join(guidance) if guidance else ""


class RegenerationContext(BaseModel):
    """Context for regeneration prompts - includes feedback from rejection.

    Carries information about why previous content was rejected so the AI
    model can generate significantly different content that addresses the feedback.
    """

    previous_title: str | None = None
    previous_description: str | None = None
    rejection_reasons: list[RejectionReasonType] = []
    ai_review_flags: list[str] = []
    regeneration_count: int = 0


# --- Generation History schemas (06-04) ---


class GenerationHistoryItem(BaseModel):
    """Single generation attempt in history."""

    id: str  # Audit ID for restore
    title: str | None
    description: str | None
    created_at: datetime
    cost: str  # Formatted as "$X.XXXX"
    attempt_number: int
    regeneration_number: int  # 0 = original, 1+ = regeneration
    is_current: bool  # Whether this is the currently active version


class GenerationHistoryResponse(BaseModel):
    """Response for generation history endpoint."""

    product_group_id: str
    product_name: str
    current_title: str | None
    current_description: str | None
    history: list[GenerationHistoryItem]


class RestoreVersionRequest(BaseModel):
    """Request to restore a previous version."""

    audit_id: str


class RestoreVersionResponse(BaseModel):
    """Response after restoring a version."""

    success: bool
    message: str
    restored_title: str | None
    restored_description: str | None
