"""Regeneration API endpoints for smart regeneration workflow."""

from typing import Annotated
from uuid import UUID, uuid4

from arq import create_pool
from arq.connections import RedisSettings
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.client import Client
from app.models.generation_audit import GenerationAudit
from app.models.generation_job import GenerationJob
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.models.user import User
from app.schemas.regeneration import (
    GenerationHistoryItem,
    GenerationHistoryResponse,
    RegenerateSingleRequest,
    RegenerationEstimate,
    RegenerationJobResponse,
    RestoreVersionResponse,
)
from app.utils.dependencies import get_current_user


def _get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into RedisSettings for ARQ job enqueueing."""
    url = settings.REDIS_URL
    if url.startswith("redis://"):
        url = url[8:]
    if ":" in url:
        host, port = url.split(":")
        return RedisSettings(host=host, port=int(port))
    return RedisSettings(host=url)

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


# --- Regeneration endpoints (06-05) ---


@router.get(
    "/{client_id}/estimate",
    response_model=RegenerationEstimate,
)
async def get_regeneration_estimate(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RegenerationEstimate:
    """Get estimate for batch regeneration of rejected products.

    Returns count of rejected products and estimated cost based on
    average generation cost (~$0.02 per product).
    """
    # Validate client ownership
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Count rejected products
    result = await db.execute(
        select(func.count(ProductGroup.id))
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.review_status == "rejected")
    )
    rejected_count = result.scalar() or 0

    # Estimate cost at ~$0.02 per product (based on typical generation cost)
    estimated_cost = f"${rejected_count * 0.02:.2f}"

    return RegenerationEstimate(
        rejected_count=rejected_count,
        estimated_cost=estimated_cost,
    )


@router.post(
    "/regenerate-single",
    response_model=RegenerationJobResponse,
)
async def regenerate_single_product(
    request: RegenerateSingleRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RegenerationJobResponse:
    """Regenerate a single product with enhanced prompts.

    Creates a generation job for just this one product.
    The product's status is reset to 'pending' and regeneration_count incremented.

    Note: Any user edits (edited_title, edited_description) are intentionally cleared
    on regeneration. The original generated content is preserved in GenerationAudit
    history and can be restored from there. This is by design -- regeneration creates
    fresh AI content, and users can re-apply edits after reviewing the new content.
    """
    # Get product group and verify ownership
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
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
            detail="Not authorized",
        )

    # Validate API key configured
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    app_settings = result.scalar_one_or_none()
    if not app_settings or not app_settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key not configured",
        )

    # Check for active job for this client
    result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.client_id == group.client_id)
        .where(GenerationJob.status.in_(["pending", "running"]))
    )
    active_job = result.scalar_one_or_none()
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A generation job is already running for this client",
        )

    # Reset product status for regeneration
    # Note: edited_title/edited_description are intentionally cleared -- users can
    # restore previous versions from history if needed, or re-apply edits to new content
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            status="pending",
            review_status=None,
            edited_title=None,
            edited_description=None,
            regeneration_count=ProductGroup.regeneration_count + 1,
        )
    )

    # Create generation job for single product
    job = GenerationJob(
        id=uuid4(),
        client_id=group.client_id,
        user_id=current_user.id,
        status="pending",
        total_count=1,
        target_product_group_id=request.product_group_id,
    )
    db.add(job)
    await db.commit()

    # Enqueue to ARQ with target_product_group_id for single-product mode
    try:
        pool = await create_pool(_get_redis_settings())
        try:
            await pool.enqueue_job(
                "generation_worker",
                str(job.id),
                str(group.client_id),
                str(current_user.id),
                str(request.product_group_id),  # Target single product
            )
        finally:
            await pool.close()
    except Exception as e:
        print(f"[Regeneration] Error enqueueing job: {e}")

    return RegenerationJobResponse(
        job_id=str(job.id),
        status="pending",
        total_count=1,
        is_regeneration=True,
        message="Regeneration started for 1 product",
    )


@router.post(
    "/{client_id}/regenerate-rejected",
    response_model=RegenerationJobResponse,
)
async def regenerate_rejected_products(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> RegenerationJobResponse:
    """Regenerate all rejected products for a client.

    Resets all rejected products to 'pending' status and creates generation job.
    Worker will use enhanced prompts with rejection feedback.

    Note: Any user edits (edited_title, edited_description) are intentionally cleared
    on regeneration. The original generated content is preserved in GenerationAudit
    history and can be restored from there. This is by design -- regeneration creates
    fresh AI content, and users can re-apply edits after reviewing the new content.
    """
    # Validate client ownership
    result = await db.execute(
        select(Client).where(Client.id == client_id, Client.user_id == current_user.id)
    )
    client = result.scalar_one_or_none()
    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Validate API key configured
    result = await db.execute(select(AppSettings).where(AppSettings.id == 1))
    app_settings = result.scalar_one_or_none()
    if not app_settings or not app_settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key not configured",
        )

    # Check for active job
    result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.client_id == client_id)
        .where(GenerationJob.status.in_(["pending", "running"]))
    )
    active_job = result.scalar_one_or_none()
    if active_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A generation job is already running for this client",
        )

    # Count rejected products
    result = await db.execute(
        select(func.count(ProductGroup.id))
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.review_status == "rejected")
    )
    rejected_count = result.scalar() or 0

    if rejected_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No rejected products to regenerate",
        )

    # Reset all rejected products for regeneration
    # Note: edited_title/edited_description are intentionally cleared -- users can
    # restore previous versions from history if needed, or re-apply edits to new content
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.review_status == "rejected")
        .values(
            status="pending",
            review_status=None,
            edited_title=None,
            edited_description=None,
            regeneration_count=ProductGroup.regeneration_count + 1,
        )
    )

    # Create generation job
    job = GenerationJob(
        id=uuid4(),
        client_id=client_id,
        user_id=current_user.id,
        status="pending",
        total_count=rejected_count,
    )
    db.add(job)
    await db.commit()

    # Enqueue to ARQ (no target_product_group_id = batch mode)
    try:
        pool = await create_pool(_get_redis_settings())
        try:
            await pool.enqueue_job(
                "generation_worker",
                str(job.id),
                str(client_id),
                str(current_user.id),
            )
        finally:
            await pool.close()
    except Exception as e:
        print(f"[Regeneration] Error enqueueing job: {e}")

    return RegenerationJobResponse(
        job_id=str(job.id),
        status="pending",
        total_count=rejected_count,
        is_regeneration=True,
        message=f"Regeneration started for {rejected_count} rejected products",
    )
