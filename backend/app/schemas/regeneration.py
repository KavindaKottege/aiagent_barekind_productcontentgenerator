"""Pydantic schemas for smart regeneration."""

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
