"""Review API endpoints for manual content review workflow."""

import asyncio
import json
from datetime import datetime
from typing import Annotated
from uuid import UUID, uuid4

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sse_starlette.sse import EventSourceResponse

from app.config import settings
from app.database import get_db
from app.models.client import Client
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.review_job import ReviewJob
from app.models.settings import AppSettings
from app.models.user import User
from app.schemas.ai_review import AIReviewRequest, BatchAIReviewRequest
from app.schemas.review import (
    EditContentRequest,
    ProductGroupReview,
    ReviewActionRequest,
    ReviewActionResponse,
    ReviewStatsResponse,
    UndoReviewRequest,
)
from app.services.ai_review_service import AIReviewService
from app.utils.dependencies import get_current_user

router = APIRouter(prefix="/review", tags=["review"])


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into RedisSettings."""
    url = settings.REDIS_URL
    if url.startswith("redis://"):
        url = url[8:]
    if ":" in url:
        host, port = url.split(":")
        return RedisSettings(host=host, port=int(port))
    return RedisSettings(host=url)


@router.get("/{client_id}/products", response_model=list[ProductGroupReview])
async def get_products_for_review(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    status_filter: Annotated[str, Query(description="Filter by review status")] = "all",
    db: AsyncSession = Depends(get_db),
) -> list[ProductGroupReview]:
    """
    Get list of product groups for review.

    - Filters: all, pending, approved, rejected, ai_approved, ai_rejected, edited
    - Only returns products with status='generated'
    - Orders by row_index for consistent queue
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Build query for product groups
    query = select(ProductGroup).where(
        ProductGroup.client_id == client_id,
        ProductGroup.status == "generated",  # Only show generated products
    )

    # Apply status filter
    if status_filter == "pending":
        query = query.where(ProductGroup.review_status.is_(None))
    elif status_filter == "approved":
        query = query.where(ProductGroup.review_status == "approved")
    elif status_filter == "rejected":
        query = query.where(ProductGroup.review_status == "rejected")
    elif status_filter == "edited":
        query = query.where(ProductGroup.review_status == "edited")
    elif status_filter == "ai_approved":
        query = query.where(ProductGroup.ai_review_status == "ai_approved")
    elif status_filter == "ai_rejected":
        query = query.where(ProductGroup.ai_review_status == "ai_rejected")
    # 'all' = no filter

    query = query.order_by(ProductGroup.created_at.desc())

    result = await db.execute(query)
    product_groups = result.scalars().all()

    # For each group, fetch first product for images and original_data
    review_list = []
    for group in product_groups:
        # Get first product in group for images and original data
        product_result = await db.execute(
            select(Product)
            .where(Product.group_id == group.id)
            .order_by(Product.row_index)
            .limit(1)
        )
        first_product = product_result.scalar_one_or_none()

        # Build original_data dict
        original_data = {}
        if first_product:
            original_data = {
                "description": first_product.description or "",
                "product_type": first_product.product_type or "",
                "option_name": first_product.option_name or "",
                "country_of_origin": first_product.country_of_origin or "",
                "made_to_order": first_product.made_to_order or "",
            }

        review_list.append(
            ProductGroupReview(
                id=group.id,
                product_name=group.product_name,
                product_token=group.product_token,
                sku=group.sku,
                variant_count=group.variant_count,
                generated_title=group.generated_title,
                generated_description=group.generated_description,
                edited_title=group.edited_title,
                edited_description=group.edited_description,
                status=group.status,
                review_status=group.review_status,
                ai_review_status=group.ai_review_status,
                ai_review_reason=group.ai_review_reason,
                ai_review_safety_flags=group.ai_review_safety_flags or [],
                images=first_product.images if first_product else [],
                original_data=original_data,
                row_index=first_product.row_index if first_product else 0,
                reviewed_at=group.reviewed_at,
                ai_reviewed_at=group.ai_reviewed_at,
            )
        )

    return review_list


@router.get("/{client_id}/product/{product_group_id}", response_model=ProductGroupReview)
async def get_product_for_review(
    client_id: UUID,
    product_group_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ProductGroupReview:
    """Get single product group for review UI."""
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get product group
    result = await db.execute(
        select(ProductGroup).where(
            ProductGroup.id == product_group_id,
            ProductGroup.client_id == client_id,
        )
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Get first product for images and original data
    product_result = await db.execute(
        select(Product)
        .where(Product.group_id == group.id)
        .order_by(Product.row_index)
        .limit(1)
    )
    first_product = product_result.scalar_one_or_none()

    # Build original_data dict
    original_data = {}
    if first_product:
        original_data = {
            "description": first_product.description or "",
            "product_type": first_product.product_type or "",
            "option_name": first_product.option_name or "",
            "country_of_origin": first_product.country_of_origin or "",
            "made_to_order": first_product.made_to_order or "",
        }

    return ProductGroupReview(
        id=group.id,
        product_name=group.product_name,
        product_token=group.product_token,
        sku=group.sku,
        variant_count=group.variant_count,
        generated_title=group.generated_title,
        generated_description=group.generated_description,
        edited_title=group.edited_title,
        edited_description=group.edited_description,
        status=group.status,
        review_status=group.review_status,
        ai_review_status=group.ai_review_status,
        ai_review_reason=group.ai_review_reason,
        ai_review_safety_flags=group.ai_review_safety_flags or [],
        images=first_product.images if first_product else [],
        original_data=original_data,
        row_index=first_product.row_index if first_product else 0,
        reviewed_at=group.reviewed_at,
        ai_reviewed_at=group.ai_reviewed_at,
    )


@router.post("/approve", response_model=ReviewActionResponse)
async def approve_product(
    request: ReviewActionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Approve a product group.

    Sets review_status='approved' and reviewed_at timestamp.
    Returns next unreviewed product for auto-advance.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this product",
        )

    # Update review status
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status="approved",
            reviewed_at=func.now(),
        )
    )
    await db.commit()

    # Find next unreviewed product (same client, row_index order)
    next_result = await db.execute(
        select(ProductGroup)
        .join(Product, Product.group_id == ProductGroup.id)
        .where(
            ProductGroup.client_id == group.client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
        .order_by(Product.row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return ReviewActionResponse(
        success=True,
        message="Product approved successfully",
        next_product_id=next_group.id if next_group else None,
    )


@router.post("/reject", response_model=ReviewActionResponse)
async def reject_product(
    request: ReviewActionRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Reject a product group.

    Sets review_status='rejected' and reviewed_at timestamp.
    Returns next unreviewed product for auto-advance.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this product",
        )

    # Update review status
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status="rejected",
            reviewed_at=func.now(),
        )
    )
    await db.commit()

    # Find next unreviewed product (same client, row_index order)
    next_result = await db.execute(
        select(ProductGroup)
        .join(Product, Product.group_id == ProductGroup.id)
        .where(
            ProductGroup.client_id == group.client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
        .order_by(Product.row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return ReviewActionResponse(
        success=True,
        message="Product rejected successfully",
        next_product_id=next_group.id if next_group else None,
    )


@router.post("/edit", response_model=ReviewActionResponse)
async def edit_product_content(
    request: EditContentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Save edited content for a product group.

    Sets edited_title, edited_description, and review_status='edited'.
    User must explicitly approve after editing.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to edit this product",
        )

    # Update edited content
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            edited_title=request.edited_title,
            edited_description=request.edited_description,
            review_status="edited",
        )
    )
    await db.commit()

    return ReviewActionResponse(
        success=True,
        message="Edits saved successfully. Click Approve to finalize.",
        next_product_id=None,  # Don't auto-advance after edit
    )


@router.post("/undo", response_model=ReviewActionResponse)
async def undo_review(
    request: UndoReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewActionResponse:
    """
    Undo a review action.

    Clears review_status and reviewed_at.
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    group = result.scalar_one_or_none()

    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to modify this product",
        )

    # Revert review status
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == request.product_group_id)
        .values(
            review_status=None,
            reviewed_at=None,
        )
    )
    await db.commit()

    return ReviewActionResponse(
        success=True,
        message="Review action undone successfully",
        next_product_id=None,
    )


@router.get("/{client_id}/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> ReviewStatsResponse:
    """
    Get review statistics for a client.

    Returns counts for each review status.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Count total generated products
    total_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.status == "generated",
        )
    )
    total_generated = total_result.scalar() or 0

    # Count pending review (review_status is null)
    pending_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
    )
    pending_review = pending_result.scalar() or 0

    # Count manually approved
    approved_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "approved",
        )
    )
    manually_approved = approved_result.scalar() or 0

    # Count manually rejected
    rejected_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "rejected",
        )
    )
    manually_rejected = rejected_result.scalar() or 0

    # Count AI approved
    ai_approved_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.ai_review_status == "ai_approved",
        )
    )
    ai_approved = ai_approved_result.scalar() or 0

    # Count AI rejected
    ai_rejected_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.ai_review_status == "ai_rejected",
        )
    )
    ai_rejected = ai_rejected_result.scalar() or 0

    # Count edited
    edited_result = await db.execute(
        select(func.count(ProductGroup.id)).where(
            ProductGroup.client_id == client_id,
            ProductGroup.review_status == "edited",
        )
    )
    edited = edited_result.scalar() or 0

    return ReviewStatsResponse(
        total_generated=total_generated,
        pending_review=pending_review,
        manually_approved=manually_approved,
        manually_rejected=manually_rejected,
        ai_approved=ai_approved,
        ai_rejected=ai_rejected,
        edited=edited,
    )


@router.get("/{client_id}/next-unreviewed")
async def get_next_unreviewed(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get next unreviewed product for a client.

    Returns product_group_id or null if none remaining.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Find next unreviewed product (row_index order)
    next_result = await db.execute(
        select(ProductGroup)
        .join(Product, Product.group_id == ProductGroup.id)
        .where(
            ProductGroup.client_id == client_id,
            ProductGroup.status == "generated",
            ProductGroup.review_status.is_(None),
        )
        .order_by(Product.row_index)
        .limit(1)
    )
    next_group = next_result.scalar_one_or_none()

    return {"product_group_id": str(next_group.id) if next_group else None}


# AI Review Endpoints

@router.post("/{client_id}/ai-review/start")
async def start_ai_review(
    client_id: UUID,
    request: BatchAIReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Start batch AI review for all generated products.

    Creates ReviewJob and enqueues to ARQ worker.
    Blocks if active ReviewJob already exists for client.

    Args:
        auto_approve: If True, AI-auto mode sets review_status directly.
                      If False, AI-assisted mode only sets ai_review_status.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Validate API key is configured
    result = await db.execute(
        select(AppSettings).where(AppSettings.id == 1)
    )
    app_settings = result.scalar_one_or_none()

    if not app_settings or not app_settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key not configured. Please configure it in Settings.",
        )

    # Check for existing active review job
    result = await db.execute(
        select(ReviewJob)
        .where(ReviewJob.client_id == client_id)
        .where(ReviewJob.status.in_(["pending", "running"]))
        .order_by(ReviewJob.created_at.desc())
        .limit(1)
    )
    existing_job = result.scalar_one_or_none()

    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"AI review already in progress for this client. Job ID: {existing_job.id}",
        )

    # Count products needing review
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.status == "generated")
        .where(ProductGroup.ai_review_status.is_(None))
    )
    products_needing_review = result.scalars().all()

    if not products_needing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No products need AI review. All generated products have already been reviewed.",
        )

    # Create review job
    job = ReviewJob(
        id=uuid4(),
        client_id=client_id,
        user_id=current_user.id,
        status="pending",
        total_count=len(products_needing_review),
    )
    db.add(job)
    await db.flush()

    # Enqueue to ARQ worker
    pool = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job(
            "batch_ai_review_worker",
            str(job.id),
            request.auto_approve,  # Pass auto_approve parameter to worker
            _job_id=str(job.id),
        )
    finally:
        await pool.close()

    await db.commit()

    return {
        "job_id": str(job.id),
        "status": "pending",
        "total_count": len(products_needing_review),
        "auto_approve": request.auto_approve,
        "message": f"AI review started for {len(products_needing_review)} products",
    }


@router.get("/{client_id}/ai-review/status")
async def get_ai_review_status(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Get current AI review job status.

    Returns job progress including auto_approve mode.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get most recent review job
    result = await db.execute(
        select(ReviewJob)
        .where(ReviewJob.client_id == client_id)
        .order_by(ReviewJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()

    if not job:
        return {"status": "no_job", "message": "No AI review job found"}

    # Calculate elapsed time
    elapsed_seconds = 0
    if job.started_at:
        end_time = job.completed_at or datetime.utcnow()
        elapsed_seconds = int((end_time - job.started_at).total_seconds())

    # Estimate remaining time
    estimated_remaining = None
    if job.completed_count > 0 and job.total_count > job.completed_count:
        avg_time_per_product = elapsed_seconds / job.completed_count
        remaining_products = job.total_count - job.completed_count
        estimated_remaining = int(avg_time_per_product * remaining_products)

    return {
        "job_id": str(job.id),
        "status": job.status,
        "total_count": job.total_count,
        "completed_count": job.completed_count,
        "total_cost": f"${job.total_cost:.2f}",
        "elapsed_seconds": elapsed_seconds,
        "estimated_remaining_seconds": estimated_remaining,
        "error_message": job.error_message,
    }


@router.get("/{client_id}/ai-review/progress")
async def stream_ai_review_progress(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Server-Sent Events endpoint for real-time AI review progress.

    Polls job status every 500ms and streams progress events.
    Events: progress, complete, error
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    async def event_generator():
        """Generate SSE events for job progress."""
        try:
            while True:
                # Get latest job for this client
                async with db.begin():
                    result = await db.execute(
                        select(ReviewJob)
                        .where(ReviewJob.client_id == client_id)
                        .order_by(ReviewJob.created_at.desc())
                        .limit(1)
                    )
                    job = result.scalar_one_or_none()

                    if not job:
                        yield {
                            "event": "error",
                            "data": json.dumps({"message": "No review job found"}),
                        }
                        break

                    # Calculate progress
                    elapsed_seconds = 0
                    if job.started_at:
                        end_time = job.completed_at or datetime.utcnow()
                        elapsed_seconds = int((end_time - job.started_at).total_seconds())

                    estimated_remaining = None
                    if job.completed_count > 0 and job.total_count > job.completed_count:
                        avg_time = elapsed_seconds / job.completed_count
                        remaining = job.total_count - job.completed_count
                        estimated_remaining = int(avg_time * remaining)

                    progress = {
                        "status": job.status,
                        "completed": job.completed_count,
                        "total": job.total_count,
                        "cost": f"{job.total_cost:.2f}",
                        "elapsed_seconds": elapsed_seconds,
                        "estimated_remaining_seconds": estimated_remaining,
                    }

                    # Send progress update
                    yield {
                        "event": "progress",
                        "data": json.dumps(progress),
                    }

                    # Check for terminal states
                    if job.status in ["completed", "failed", "cancelled"]:
                        yield {
                            "event": "complete",
                            "data": json.dumps({
                                "status": job.status,
                                "summary": {
                                    "total_products": job.total_count,
                                    "completed": job.completed_count,
                                    "total_cost": f"{job.total_cost:.2f}",
                                    "elapsed_seconds": elapsed_seconds,
                                },
                            }),
                        }
                        break

                # Poll every 500ms
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return EventSourceResponse(event_generator())


@router.post("/{client_id}/ai-review/pause")
async def pause_ai_review(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Pause running AI review job.

    Job will stop after current product.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get active job
    result = await db.execute(
        select(ReviewJob)
        .where(ReviewJob.client_id == client_id)
        .where(ReviewJob.status == "running")
        .order_by(ReviewJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No running AI review job found",
        )

    # Update job status
    await db.execute(
        update(ReviewJob)
        .where(ReviewJob.id == job.id)
        .values(status="paused")
    )
    await db.commit()

    return {"message": "AI review pause requested. Will stop after current product."}


@router.post("/{client_id}/ai-review/cancel")
async def cancel_ai_review(
    client_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Cancel AI review job.

    Job will stop after current product.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Get active job
    result = await db.execute(
        select(ReviewJob)
        .where(ReviewJob.client_id == client_id)
        .where(ReviewJob.status.in_(["pending", "running", "paused"]))
        .order_by(ReviewJob.created_at.desc())
        .limit(1)
    )
    job = result.scalar_one_or_none()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active AI review job found",
        )

    # Update job status
    await db.execute(
        update(ReviewJob)
        .where(ReviewJob.id == job.id)
        .values(
            status="cancelled",
            completed_at=datetime.utcnow(),
        )
    )
    await db.commit()

    return {"message": "AI review job cancelled"}


@router.post("/{client_id}/ai-review/resume")
async def resume_ai_review(
    client_id: UUID,
    request: BatchAIReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Resume paused AI review job.

    Creates new job that continues from where previous job stopped.
    Can change auto_approve mode on resume.
    """
    # Validate client belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client not found",
        )

    # Count products still needing review
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.status == "generated")
        .where(ProductGroup.ai_review_status.is_(None))
    )
    products_needing_review = result.scalars().all()

    if not products_needing_review:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No products need AI review.",
        )

    # Create new review job
    job = ReviewJob(
        id=uuid4(),
        client_id=client_id,
        user_id=current_user.id,
        status="pending",
        total_count=len(products_needing_review),
    )
    db.add(job)
    await db.flush()

    # Enqueue to ARQ worker
    pool = await create_pool(get_redis_settings())
    try:
        await pool.enqueue_job(
            "batch_ai_review_worker",
            str(job.id),
            request.auto_approve,
            _job_id=str(job.id),
        )
    finally:
        await pool.close()

    await db.commit()

    return {
        "job_id": str(job.id),
        "status": "pending",
        "total_count": len(products_needing_review),
        "auto_approve": request.auto_approve,
        "message": f"AI review resumed for {len(products_needing_review)} products",
    }


@router.post("/ai-single")
async def review_single_product(
    request: AIReviewRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    On-demand AI review for single product.

    Calls AIReviewService directly (not background).
    Returns AIReviewResult immediately.
    Updates product_group with AI recommendation (ai_review_status only, NOT review_status).
    Single product review is always AI-assisted mode (recommendations only).
    """
    # Get product group
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == request.product_group_id)
    )
    product_group = result.scalar_one_or_none()

    if not product_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product group not found",
        )

    # Verify user owns this product group
    if product_group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to review this product",
        )

    # Get app settings for API key
    result = await db.execute(
        select(AppSettings).where(AppSettings.id == 1)
    )
    app_settings = result.scalar_one_or_none()

    if not app_settings or not app_settings.openai_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OpenAI API key not configured",
        )

    # Get related products
    result = await db.execute(
        select(Product)
        .where(Product.product_group_id == product_group.id)
        .order_by(Product.created_at)
    )
    products = result.scalars().all()

    # Initialize AI review service
    ai_service = AIReviewService(
        db=db,
        api_key=app_settings.openai_api_key,
        model=app_settings.ai_model or "gpt-5.2",
        temperature=0.3,
    )

    # Review the product
    try:
        result_obj, cost = await ai_service.review_product(product_group, list(products))

        # Update product_group with AI review (ai_review_status only, NOT review_status)
        await db.execute(
            update(ProductGroup)
            .where(ProductGroup.id == product_group.id)
            .values(
                ai_review_status=f"ai_{result_obj.recommendation}d",
                ai_review_reason=result_obj.reason,
                ai_review_safety_flags=result_obj.safety_flags,
                ai_reviewed_at=datetime.utcnow(),
            )
        )
        await db.commit()

        return {
            "recommendation": result_obj.recommendation,
            "reason": result_obj.reason,
            "safety_flags": result_obj.safety_flags,
            "accuracy_score": result_obj.accuracy_score,
            "cost": f"${cost:.4f}",
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"AI review failed: {str(e)}",
        )
