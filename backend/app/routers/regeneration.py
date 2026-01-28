"""Regeneration API endpoints for smart regeneration workflow."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.generation_audit import GenerationAudit
from app.models.product_group import ProductGroup
from app.models.user import User
from app.schemas.regeneration import (
    GenerationHistoryItem,
    GenerationHistoryResponse,
    RestoreVersionResponse,
)
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/regeneration", tags=["regeneration"])


@router.get(
    "/{product_group_id}/history",
    response_model=GenerationHistoryResponse,
)
async def get_generation_history(
    product_group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> GenerationHistoryResponse:
    """Get generation history for a product group.

    Returns all successful generation attempts ordered by created_at desc.
    Each item shows title, description, cost, and timestamp.
    """
    # Get product group and verify ownership
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this product's history",
        )

    # Get all successful generation audits for this product
    result = await db.execute(
        select(GenerationAudit)
        .where(GenerationAudit.product_group_id == product_group_id)
        .where(GenerationAudit.success == True)  # noqa: E712
        .where(GenerationAudit.generated_title.isnot(None))
        .where(GenerationAudit.generated_description.isnot(None))
        .order_by(GenerationAudit.created_at.desc())
    )
    audits = result.scalars().all()

    # Determine current content for is_current flag
    current_title = group.edited_title or group.generated_title
    current_description = group.edited_description or group.generated_description

    # Build history items
    history = []
    for i, audit in enumerate(audits):
        # Estimate regeneration number from job order
        # Most recent = highest regeneration number, descending
        regen_num = group.regeneration_count - i if group.regeneration_count else 0
        if regen_num < 0:
            regen_num = 0

        # Check if this audit's content matches current content
        is_current = (
            audit.generated_title == current_title
            and audit.generated_description == current_description
        )

        history.append(
            GenerationHistoryItem(
                id=str(audit.id),
                title=audit.generated_title,
                description=audit.generated_description,
                created_at=audit.created_at,
                cost=f"${audit.cost:.4f}",
                attempt_number=audit.attempt_number,
                regeneration_number=regen_num,
                is_current=is_current,
            )
        )

    return GenerationHistoryResponse(
        product_group_id=str(product_group_id),
        product_name=group.product_name,
        current_title=current_title,
        current_description=current_description,
        history=history,
    )


@router.post(
    "/{product_group_id}/restore/{audit_id}",
    response_model=RestoreVersionResponse,
)
async def restore_version(
    product_group_id: UUID,
    audit_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RestoreVersionResponse:
    """Restore a previous generation version as the current content.

    Copies the audit's title/description to ProductGroup.generated_*.
    Clears edited_* fields and resets review_status to pending.
    """
    # Get product group and verify ownership
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this product",
        )

    # Get the audit record
    result = await db.execute(
        select(GenerationAudit).where(GenerationAudit.id == audit_id)
    )
    audit = result.scalar_one_or_none()

    if not audit:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Version not found",
        )

    # Verify audit belongs to this product group
    if audit.product_group_id != product_group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Version does not belong to this product",
        )

    # Restore content: copy audit content to generated_*, clear edits, reset review
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == product_group_id)
        .values(
            generated_title=audit.generated_title,
            generated_description=audit.generated_description,
            edited_title=None,
            edited_description=None,
            review_status=None,
            reviewed_at=None,
        )
    )
    await db.commit()

    return RestoreVersionResponse(
        success=True,
        message="Version restored successfully",
        restored_title=audit.generated_title,
        restored_description=audit.generated_description,
    )
