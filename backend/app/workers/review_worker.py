"""ARQ worker function for batch AI review."""

import asyncio
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.product import Product
from app.models.product_group import ProductGroup
from app.models.review_job import ReviewJob
from app.models.settings import AppSettings
from app.services.ai_review_service import AIReviewService


async def batch_ai_review_worker(ctx: dict, job_id: str, auto_approve: bool = False) -> dict:
    """
    ARQ worker for batch AI review with progress tracking.

    Args:
        ctx: ARQ context with database session
        job_id: ReviewJob ID
        auto_approve: If True, sets review_status directly (AI-auto mode).
                      If False, only sets ai_review_status (AI-assisted mode).

    Returns:
        Dictionary with job completion summary
    """
    session_factory = ctx["db_session_factory"]

    async with session_factory() as db:
        # Load job
        job = await _get_job(db, job_id)
        if not job:
            return {"status": "error", "message": "Job not found"}

        # Mark job as running
        await _update_job_status(db, job_id, "running", started_at=datetime.utcnow())
        await db.commit()

        # Load client and app settings
        client = await _get_client(db, job.client_id)
        app_settings = await _get_app_settings(db)

        if not client:
            await _update_job_status(db, job_id, "failed", error_message="Client not found")
            await db.commit()
            return {"status": "error", "message": "Client not found"}

        if not app_settings or not app_settings.openai_api_key:
            await _update_job_status(db, job_id, "failed", error_message="OpenAI API key not configured")
            await db.commit()
            return {"status": "error", "message": "OpenAI API key not configured"}

        # Query all ProductGroups for client with status='generated' and ai_review_status IS NULL
        product_groups = await _get_products_needing_review(db, str(job.client_id))

        if not product_groups:
            await _update_job_status(
                db, job_id, "completed",
                completed_at=datetime.utcnow(),
            )
            await db.commit()
            return {"status": "completed", "message": "No products need review"}

        # Update total count
        await _update_job_progress(db, job_id, total_count=len(product_groups))
        await db.commit()

        # Initialize AI review service
        ai_service = AIReviewService(
            db=db,
            api_key=app_settings.openai_api_key,
            model=app_settings.ai_model or "gpt-5.2",
            temperature=0.3,  # Lower temperature for more consistent reviews
        )

        # Process each product group
        completed = 0
        success_count = 0
        failed_count = 0

        for product_group in product_groups:
            # Check job status before each product (for pause/cancel)
            current_status = await _get_job_status(db, job_id)

            if current_status == "cancelled":
                await _update_job_status(
                    db, job_id, "cancelled",
                    completed_at=datetime.utcnow(),
                )
                await db.commit()
                return {
                    "status": "cancelled",
                    "completed": completed,
                    "success": success_count,
                    "failed": failed_count,
                }

            if current_status == "paused":
                await _update_job_status(
                    db, job_id, "paused",
                )
                await db.commit()
                return {
                    "status": "paused",
                    "completed": completed,
                    "success": success_count,
                    "failed": failed_count,
                }

            # Fetch related products (for original data)
            products = await _get_products_for_group(db, product_group.id)

            # Review this product
            try:
                result, cost = await ai_service.review_product(product_group, products)

                # Update product_group with AI review result
                update_values = {
                    "ai_review_status": f"ai_{result.recommendation}d",  # ai_approved or ai_rejected
                    "ai_review_reason": result.reason,
                    "ai_review_safety_flags": result.safety_flags,
                    "ai_reviewed_at": datetime.utcnow(),
                }

                # CRITICAL - AI-auto mode: set review_status directly
                if auto_approve:
                    if result.recommendation == "approve":
                        update_values["review_status"] = "ai_approved"
                    else:
                        update_values["review_status"] = "ai_rejected"

                # AI-assisted mode: only ai_review_status is set, user must manually approve/reject
                # (no review_status update)

                await _update_product_group(db, product_group.id, update_values)

                success_count += 1

            except Exception as e:
                # Log error but continue processing
                failed_count += 1
                # Could optionally store error in product_group

            completed += 1

            # Update job progress
            await _update_job_progress(
                db,
                job_id,
                completed_count=completed,
                total_cost=ai_service.cost_tracker.total_cost,
            )
            await db.commit()

            # Small delay to prevent overwhelming API
            await asyncio.sleep(0.1)

        # Job completed
        await _update_job_status(
            db, job_id, "completed",
            completed_at=datetime.utcnow(),
        )
        await db.commit()

        return {
            "status": "completed",
            "completed": completed,
            "success": success_count,
            "failed": failed_count,
            "total_cost": float(ai_service.cost_tracker.total_cost),
        }


# Helper functions for database operations

async def _get_job(db: AsyncSession, job_id: str) -> ReviewJob | None:
    """Get review job by ID."""
    result = await db.execute(
        select(ReviewJob).where(ReviewJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def _get_job_status(db: AsyncSession, job_id: str) -> str | None:
    """Get just the job status (for checking pause/cancel)."""
    result = await db.execute(
        select(ReviewJob.status).where(ReviewJob.id == job_id)
    )
    row = result.first()
    return row[0] if row else None


async def _get_client(db: AsyncSession, client_id: str) -> Client | None:
    """Get client by ID."""
    result = await db.execute(
        select(Client).where(Client.id == client_id)
    )
    return result.scalar_one_or_none()


async def _get_app_settings(db: AsyncSession) -> AppSettings | None:
    """Get app settings."""
    result = await db.execute(
        select(AppSettings).where(AppSettings.id == 1)
    )
    return result.scalar_one_or_none()


async def _get_products_needing_review(db: AsyncSession, client_id: str) -> list[ProductGroup]:
    """Get product groups that need AI review."""
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.status == "generated")
        .where(ProductGroup.ai_review_status.is_(None))
        .order_by(ProductGroup.created_at)
    )
    return list(result.scalars().all())


async def _get_products_for_group(db: AsyncSession, group_id: str) -> list[Product]:
    """Get all products in a product group."""
    result = await db.execute(
        select(Product)
        .where(Product.product_group_id == group_id)
        .order_by(Product.created_at)
    )
    return list(result.scalars().all())


async def _update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    error_message: str | None = None,
) -> None:
    """Update job status atomically."""
    values = {"status": status}
    if started_at:
        values["started_at"] = started_at
    if completed_at:
        values["completed_at"] = completed_at
    if error_message:
        values["error_message"] = error_message

    await db.execute(
        update(ReviewJob)
        .where(ReviewJob.id == job_id)
        .values(**values)
    )


async def _update_job_progress(
    db: AsyncSession,
    job_id: str,
    total_count: int | None = None,
    completed_count: int | None = None,
    total_cost: Decimal | None = None,
) -> None:
    """Update job progress counters."""
    values = {}
    if total_count is not None:
        values["total_count"] = total_count
    if completed_count is not None:
        values["completed_count"] = completed_count
    if total_cost is not None:
        values["total_cost"] = total_cost

    if values:
        await db.execute(
            update(ReviewJob)
            .where(ReviewJob.id == job_id)
            .values(**values)
        )


async def _update_product_group(
    db: AsyncSession,
    product_group_id: str,
    values: dict,
) -> None:
    """Update product group with review data."""
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == product_group_id)
        .values(**values)
    )
