"""ARQ worker function for AI content generation."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.client import Client
from app.models.generation_job import GenerationJob
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.services.ai_generation import AIGenerationService
from app.services.cost_tracker import CostTracker
from app.config import settings


async def generation_worker(
    ctx: dict,
    job_id: str,
    client_id: str,
    user_id: str,
) -> dict:
    """
    ARQ worker function for processing AI generation jobs.

    Args:
        ctx: Worker context with database connection
        job_id: UUID of the GenerationJob to process
        client_id: UUID of the client
        user_id: UUID of the user who started the job

    Returns:
        Dictionary with job completion summary
    """
    session_factory = ctx["db_session_factory"]

    async with session_factory() as db:
        # Load job
        job = await _get_job(db, job_id)
        if not job:
            return {"status": "error", "message": "Job not found"}

        # Mark job as running (only set started_at if not already set - for resumed jobs)
        started_at = datetime.now(timezone.utc) if not job.started_at else None
        await _update_job_status(db, job_id, "running", started_at=started_at)
        await db.commit()

        # Load client and app settings
        client = await _get_client(db, client_id)
        app_settings = await _get_app_settings(db)

        if not client:
            await _update_job_status(db, job_id, "failed", status_reason="Client not found")
            await db.commit()
            return {"status": "error", "message": "Client not found"}

        if not app_settings or not app_settings.openai_api_key:
            await _update_job_status(db, job_id, "failed", status_reason="OpenAI API key not configured")
            await db.commit()
            return {"status": "error", "message": "OpenAI API key not configured"}

        # Get pending products
        products = await _get_pending_products(db, client_id)

        if not products:
            await _update_job_status(
                db, job_id, "completed",
                completed_at=datetime.now(timezone.utc),
                status_reason="No pending products to generate"
            )
            await db.commit()
            return {"status": "completed", "message": "No pending products"}

        # Update total count
        await _update_job_progress(db, job_id, total_count=len(products))
        await db.commit()

        # Initialize AI service - use database settings, fallback to config
        ai_service = AIGenerationService(
            db=db,
            api_key=app_settings.openai_api_key,
            model=app_settings.ai_model or settings.AI_MODEL,
            temperature=float(app_settings.ai_temperature) if app_settings.ai_temperature else settings.AI_TEMPERATURE,
        )

        # For resumed jobs, initialize cost tracker with existing values
        if job.total_cost > 0:
            ai_service.cost_tracker.total_input_tokens = job.total_input_tokens
            ai_service.cost_tracker.total_cached_input_tokens = job.total_cached_input_tokens
            ai_service.cost_tracker.total_output_tokens = job.total_output_tokens
            ai_service.cost_tracker.total_cost = job.total_cost
            ai_service.cost_tracker.total_input_cost = job.total_input_cost
            ai_service.cost_tracker.total_cached_input_cost = job.total_cached_input_cost
            ai_service.cost_tracker.total_output_cost = job.total_output_cost
            ai_service.cost_tracker.total_generations = job.completed_count
            print(f"[Worker] Resumed with existing costs: ${job.total_cost}")

        # Time tracking - record start of this run and base elapsed from previous runs
        run_start_time = datetime.now(timezone.utc)
        base_elapsed_seconds = job.elapsed_seconds or 0

        # Process each product
        completed = job.completed_count  # Start from existing count for resumed jobs
        success_count = job.success_count
        failed_count = job.failed_count
        soft_cap = app_settings.generation_soft_cap if app_settings.generation_soft_cap else Decimal(str(settings.GENERATION_SOFT_CAP))
        print(f"[Worker] Using soft cap: ${soft_cap}, model: {app_settings.ai_model or settings.AI_MODEL}")

        for product in products:
            # Check job status before each product (for pause/cancel)
            current_status = await _get_job_status(db, job_id)

            if current_status == "cancelled":
                await _update_job_status(
                    db, job_id, "cancelled",
                    completed_at=datetime.now(timezone.utc),
                    status_reason="Cancelled by user"
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
                    paused_at=datetime.now(timezone.utc),
                    status_reason="Paused by user"
                )
                await db.commit()
                return {
                    "status": "paused",
                    "completed": completed,
                    "success": success_count,
                    "failed": failed_count,
                }

            # Check soft cap
            current_cost = ai_service.cost_tracker.total_cost
            print(f"[Worker] Soft cap check: current=${current_cost}, cap=${soft_cap}, exceeded={current_cost >= soft_cap}")
            if ai_service.cost_tracker.check_soft_cap(soft_cap):
                await _update_job_status(
                    db, job_id, "paused",
                    paused_at=datetime.now(timezone.utc),
                    status_reason=f"Cost soft cap reached (${ai_service.cost_tracker.total_cost:.2f})"
                )
                await db.commit()
                return {
                    "status": "paused",
                    "reason": "soft_cap",
                    "current_cost": float(ai_service.cost_tracker.total_cost),
                    "soft_cap": float(soft_cap),
                    "completed": completed,
                    "success": success_count,
                    "failed": failed_count,
                }

            # Generate content for this product
            try:
                result, audit = await ai_service.generate_content(
                    product_group=product,
                    client=client,
                    job=job,
                    app_settings=app_settings,
                )

                if result:
                    # Success - update product group
                    await _update_product_group(
                        db,
                        product.id,
                        status="generated",
                        generated_title=result.title,
                        generated_description=result.description,
                    )
                    success_count += 1
                    print(f"[Worker] Successfully generated content for product {product.id}")
                else:
                    # Failed after retries
                    print(f"[Worker] Generation failed for product {product.id} after retries. Audit error: {audit.error_message if audit else 'No audit'}")
                    await _update_product_group(
                        db,
                        product.id,
                        status="failed",
                    )
                    failed_count += 1

            except Exception as e:
                # Unexpected error - mark product as failed
                print(f"[Worker] Error generating content for product {product.id}: {e}")
                import traceback
                traceback.print_exc()
                await _update_product_group(db, product.id, status="failed")
                failed_count += 1

            completed += 1

            # Calculate cumulative elapsed time (base + current run)
            current_elapsed = base_elapsed_seconds + int((datetime.now(timezone.utc) - run_start_time).total_seconds())

            # Update job progress
            await _update_job_progress(
                db,
                job_id,
                completed_count=completed,
                success_count=success_count,
                failed_count=failed_count,
                total_cost=ai_service.cost_tracker.total_cost,
                total_input_tokens=ai_service.cost_tracker.total_input_tokens,
                total_cached_input_tokens=ai_service.cost_tracker.total_cached_input_tokens,
                total_output_tokens=ai_service.cost_tracker.total_output_tokens,
                total_input_cost=ai_service.cost_tracker.total_input_cost,
                total_cached_input_cost=ai_service.cost_tracker.total_cached_input_cost,
                total_output_cost=ai_service.cost_tracker.total_output_cost,
                elapsed_seconds=current_elapsed,
            )
            await db.commit()

            # Small delay to prevent overwhelming API
            await asyncio.sleep(0.1)

        # Job completed
        await _update_job_status(
            db, job_id, "completed",
            completed_at=datetime.now(timezone.utc),
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

async def _get_job(db: AsyncSession, job_id: str) -> GenerationJob | None:
    """Get generation job by ID."""
    result = await db.execute(
        select(GenerationJob).where(GenerationJob.id == job_id)
    )
    return result.scalar_one_or_none()


async def _get_job_status(db: AsyncSession, job_id: str) -> str | None:
    """Get just the job status (for checking pause/cancel)."""
    result = await db.execute(
        select(GenerationJob.status).where(GenerationJob.id == job_id)
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


async def _get_pending_products(db: AsyncSession, client_id: str) -> list[ProductGroup]:
    """Get pending product groups for client."""
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.status == "pending")
        .order_by(ProductGroup.created_at)
    )
    return list(result.scalars().all())


async def _update_job_status(
    db: AsyncSession,
    job_id: str,
    status: str,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
    paused_at: datetime | None = None,
    status_reason: str | None = None,
) -> None:
    """Update job status atomically."""
    values = {"status": status}
    if started_at:
        values["started_at"] = started_at
    if completed_at:
        values["completed_at"] = completed_at
    if paused_at:
        values["paused_at"] = paused_at
    if status_reason:
        values["status_reason"] = status_reason

    await db.execute(
        update(GenerationJob)
        .where(GenerationJob.id == job_id)
        .values(**values)
    )


async def _update_job_progress(
    db: AsyncSession,
    job_id: str,
    total_count: int | None = None,
    completed_count: int | None = None,
    success_count: int | None = None,
    failed_count: int | None = None,
    total_cost: Decimal | None = None,
    total_input_tokens: int | None = None,
    total_cached_input_tokens: int | None = None,
    total_output_tokens: int | None = None,
    total_input_cost: Decimal | None = None,
    total_cached_input_cost: Decimal | None = None,
    total_output_cost: Decimal | None = None,
    elapsed_seconds: int | None = None,
) -> None:
    """Update job progress counters."""
    values = {}
    if total_count is not None:
        values["total_count"] = total_count
    if completed_count is not None:
        values["completed_count"] = completed_count
    if success_count is not None:
        values["success_count"] = success_count
    if failed_count is not None:
        values["failed_count"] = failed_count
    if total_cost is not None:
        values["total_cost"] = total_cost
    if total_input_tokens is not None:
        values["total_input_tokens"] = total_input_tokens
    if total_cached_input_tokens is not None:
        values["total_cached_input_tokens"] = total_cached_input_tokens
    if total_output_tokens is not None:
        values["total_output_tokens"] = total_output_tokens
    if total_input_cost is not None:
        values["total_input_cost"] = total_input_cost
    if total_cached_input_cost is not None:
        values["total_cached_input_cost"] = total_cached_input_cost
    if total_output_cost is not None:
        values["total_output_cost"] = total_output_cost
    if elapsed_seconds is not None:
        values["elapsed_seconds"] = elapsed_seconds

    if values:
        await db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(**values)
        )


async def _update_product_group(
    db: AsyncSession,
    product_group_id: UUID,
    status: str,
    generated_title: str | None = None,
    generated_description: str | None = None,
) -> None:
    """Update product group with generated content."""
    values = {"status": status}
    if generated_title is not None:
        values["generated_title"] = generated_title
    if generated_description is not None:
        values["generated_description"] = generated_description

    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == product_group_id)
        .values(**values)
    )
