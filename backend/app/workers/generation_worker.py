"""ARQ worker function for AI content generation."""

import asyncio
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.client import Client
from app.models.generation_job import GenerationJob
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.schemas.regeneration import RegenerationContext
from app.services.ai_generation import AIGenerationService
from app.services.cost_tracker import CostTracker
from app.config import settings


async def generation_worker(
    ctx: dict,
    job_id: str,
    client_id: str,
    user_id: str,
    target_product_group_id: str | None = None,
) -> dict:
    """
    ARQ worker function for processing AI generation jobs.

    Args:
        ctx: Worker context with database connection
        job_id: UUID of the GenerationJob to process
        client_id: UUID of the client
        user_id: UUID of the user who started the job
        target_product_group_id: If set, generate only this specific product (for single-product jobs)

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

        # Get pending products (or single targeted product)
        products = await _get_pending_products(db, client_id, target_product_group_id)

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

        # For new jobs (soft_cap_threshold == 0), initialize threshold to soft_cap from settings
        # For resumed jobs, soft_cap_threshold is already set to current_cost + soft_cap
        soft_cap_threshold = job.soft_cap_threshold if job.soft_cap_threshold > 0 else soft_cap
        print(f"[Worker] Using soft cap: ${soft_cap}, threshold: ${soft_cap_threshold}, model: {app_settings.ai_model or settings.AI_MODEL}")

        for product_group in products:
            # Set current product name and reset attempt tracking for UI
            await _update_current_task(
                db, job_id,
                current_product_name=product_group.product_name,
                current_task=None,
                task1_attempts=[],
                task2_attempts=[],
            )
            await db.commit()

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

            # Check soft cap against threshold (not raw soft_cap)
            # For new jobs: threshold = soft_cap from settings
            # For resumed jobs: threshold = previous_cost + soft_cap (set when user acknowledged)
            current_cost = ai_service.cost_tracker.total_cost
            print(f"[Worker] Soft cap check: current=${current_cost}, threshold=${soft_cap_threshold}, exceeded={current_cost >= soft_cap_threshold}")
            if current_cost >= soft_cap_threshold:
                await _update_job_status(
                    db, job_id, "paused",
                    paused_at=datetime.now(timezone.utc),
                    status_reason=f"Cost soft cap reached (${current_cost:.2f})"
                )
                await db.commit()
                return {
                    "status": "paused",
                    "reason": "soft_cap",
                    "current_cost": float(current_cost),
                    "soft_cap": float(soft_cap),
                    "completed": completed,
                    "success": success_count,
                    "failed": failed_count,
                }

            # Get primary product for accessing description/images fields
            primary_product = product_group.products[0] if product_group.products else None
            if not primary_product:
                print(f"[Worker] No products found for product group {product_group.id}, marking as failed")
                await _update_product_group(db, product_group.id, status="failed")
                failed_count += 1
                completed += 1
                continue

            # Build regeneration context if this is a regeneration
            regeneration_context = None
            if product_group.regeneration_count > 0:
                regeneration_context = RegenerationContext(
                    previous_title=product_group.generated_title,
                    previous_description=product_group.generated_description,
                    rejection_reasons=product_group.rejection_reasons or [],
                    ai_review_flags=product_group.ai_review_safety_flags or [],
                    regeneration_count=product_group.regeneration_count,
                )
                print(f"[Worker] Building regeneration context: count={product_group.regeneration_count}, reasons={product_group.rejection_reasons}")

            # === TASK 1: Generate Title ===
            # Set current task and create callback for attempt tracking
            await _update_current_task(db, job_id, current_task="title")
            await db.commit()

            async def on_title_attempt(attempt: int, success: bool, error: str | None) -> None:
                """Callback to track title generation attempts."""
                await _append_task_attempt(db, job_id, task=1, success=success, error=error)
                await db.commit()

            try:
                title_result, title_audit = await ai_service.generate_title(
                    product_group=product_group,
                    primary_product=primary_product,
                    client=client,
                    job=job,
                    app_settings=app_settings,
                    on_attempt=on_title_attempt,
                    regeneration_context=regeneration_context,
                )

                if not title_result:
                    # Title generation failed after retries
                    print(f"[Worker] Title generation failed for product {product_group.id}. Audit error: {title_audit.error_message if title_audit else 'No audit'}")
                    await _update_product_group(db, product_group.id, status="failed")
                    failed_count += 1
                    completed += 1
                    # Update progress and continue to next product
                    current_elapsed = base_elapsed_seconds + int((datetime.now(timezone.utc) - run_start_time).total_seconds())
                    await _update_job_progress(
                        db, job_id,
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
                    continue

                # Store title immediately (partial update)
                await _update_product_group(
                    db, product_group.id,
                    status="pending",  # Still pending until description completes
                    generated_title=title_result.title,
                )
                print(f"[Worker] Successfully generated TITLE for product {product_group.id}")

            except Exception as e:
                print(f"[Worker] Error generating title for product {product_group.id}: {e}")
                import traceback
                traceback.print_exc()
                await _update_product_group(db, product_group.id, status="failed")
                failed_count += 1
                completed += 1
                continue

            # === TASK 2: Generate Description ===
            # Set current task and create callback for attempt tracking
            await _update_current_task(db, job_id, current_task="description")
            await db.commit()

            async def on_desc_attempt(attempt: int, success: bool, error: str | None) -> None:
                """Callback to track description generation attempts."""
                await _append_task_attempt(db, job_id, task=2, success=success, error=error)
                await db.commit()

            try:
                desc_result, desc_audit = await ai_service.generate_description(
                    product_group=product_group,
                    primary_product=primary_product,
                    client=client,
                    job=job,
                    app_settings=app_settings,
                    on_attempt=on_desc_attempt,
                    regeneration_context=regeneration_context,
                )

                if desc_result:
                    # Both tasks successful
                    await _update_product_group(
                        db, product_group.id,
                        status="generated",
                        generated_description=desc_result.description,
                    )
                    success_count += 1
                    print(f"[Worker] Successfully generated DESCRIPTION for product {product_group.id}")
                else:
                    # Description failed - title was saved but mark as failed
                    print(f"[Worker] Description generation failed for product {product_group.id}. Audit error: {desc_audit.error_message if desc_audit else 'No audit'}")
                    await _update_product_group(db, product_group.id, status="failed")
                    failed_count += 1

            except Exception as e:
                print(f"[Worker] Error generating description for product {product_group.id}: {e}")
                import traceback
                traceback.print_exc()
                await _update_product_group(db, product_group.id, status="failed")
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


async def _get_pending_products(
    db: AsyncSession,
    client_id: str,
    target_product_group_id: str | None = None,
) -> list[ProductGroup]:
    """Get pending product groups for client with eager-loaded products.

    Args:
        db: Database session
        client_id: Client ID to filter by
        target_product_group_id: If set, get only this specific product (for single-product jobs)
    """
    query = (
        select(ProductGroup)
        .options(selectinload(ProductGroup.products))  # Eager load products for description/images
        .where(ProductGroup.client_id == client_id)
    )

    if target_product_group_id:
        # Single-product job: get the specific product regardless of status
        # (it was already reset to pending by the endpoint)
        query = query.where(ProductGroup.id == target_product_group_id)
    else:
        # Batch job: get all pending products
        query = query.where(ProductGroup.status == "pending")

    query = query.order_by(ProductGroup.created_at)
    result = await db.execute(query)
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
    status: str | None = None,
    generated_title: str | None = None,
    generated_description: str | None = None,
) -> None:
    """Update product group with generated content."""
    values = {}
    if status is not None:
        values["status"] = status
    if generated_title is not None:
        values["generated_title"] = generated_title
    if generated_description is not None:
        values["generated_description"] = generated_description

    if values:
        await db.execute(
            update(ProductGroup)
            .where(ProductGroup.id == product_group_id)
            .values(**values)
        )


async def _update_current_task(
    db: AsyncSession,
    job_id: str,
    current_product_name: str | None = None,
    current_task: str | None = None,
    task1_attempts: list | None = None,
    task2_attempts: list | None = None,
) -> None:
    """Update current task tracking fields for real-time UI updates."""
    values = {}
    if current_product_name is not None:
        values["current_product_name"] = current_product_name
    # Always set current_task even if None (to clear it)
    values["current_task"] = current_task
    if task1_attempts is not None:
        values["task1_attempts"] = task1_attempts
    if task2_attempts is not None:
        values["task2_attempts"] = task2_attempts

    if values:
        await db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(**values)
        )


async def _append_task_attempt(
    db: AsyncSession,
    job_id: str,
    task: int,  # 1 or 2
    success: bool,
    error: str | None,
) -> None:
    """Append an attempt result to the appropriate task attempts array."""
    print(f"[Worker] _append_task_attempt called: task={task}, success={success}, error={error}")

    # First, get current attempts
    result = await db.execute(
        select(GenerationJob.task1_attempts, GenerationJob.task2_attempts)
        .where(GenerationJob.id == job_id)
    )
    row = result.first()
    if not row:
        print(f"[Worker] _append_task_attempt: No row found for job_id={job_id}")
        return

    task1_attempts = row[0] or []
    task2_attempts = row[1] or []
    print(f"[Worker] _append_task_attempt: Current task1_attempts={task1_attempts}, task2_attempts={task2_attempts}")

    # Create attempt record
    attempt_record = {"success": success, "error": error}

    # Append to appropriate list
    if task == 1:
        task1_attempts = task1_attempts + [attempt_record]
        print(f"[Worker] _append_task_attempt: Updating task1_attempts to {task1_attempts}")
        await db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(task1_attempts=task1_attempts)
        )
    else:
        task2_attempts = task2_attempts + [attempt_record]
        print(f"[Worker] _append_task_attempt: Updating task2_attempts to {task2_attempts}")
        await db.execute(
            update(GenerationJob)
            .where(GenerationJob.id == job_id)
            .values(task2_attempts=task2_attempts)
        )
    print(f"[Worker] _append_task_attempt: Update executed, ready for commit")
