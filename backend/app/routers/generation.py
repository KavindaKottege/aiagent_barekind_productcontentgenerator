"""Generation API endpoints for AI content generation jobs."""

import asyncio
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sse_starlette.sse import EventSourceResponse

from app.database import get_db
from app.models.client import Client
from app.models.generation_job import GenerationJob
from app.models.product_group import ProductGroup
from app.models.settings import AppSettings
from app.models.user import User
from app.schemas.generation import (
    CostCapDialogResponse,
    GenerationJobCreate,
    GenerationJobResponse,
    GenerationProgressResponse,
)
from app.services.job_manager import JobManager
from app.utils.dependencies import get_current_user
from app.utils.auth import decode_access_token
from app.config import settings


router = APIRouter(prefix="/generation", tags=["generation"])


async def get_job_manager(db: AsyncSession = Depends(get_db)) -> JobManager:
    """Dependency to get JobManager instance."""
    return JobManager(db)


@router.post("/start", response_model=GenerationJobResponse)
async def start_generation(
    request: GenerationJobCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Start a new generation job for a client.

    - Validates client exists and belongs to user
    - Validates OpenAI API key is configured
    - Checks no active job already exists for client
    - Creates job and enqueues to background worker

    Returns the created job with pending status.
    """
    # Validate client exists and belongs to user
    result = await db.execute(
        select(Client).where(
            Client.id == request.client_id,
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

    # Check for existing active job
    existing_job = await job_manager.get_active_job_for_client(request.client_id)
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Generation already in progress for this client. Job ID: {existing_job.id}",
        )

    # Count pending products
    result = await db.execute(
        select(ProductGroup)
        .where(ProductGroup.client_id == request.client_id)
        .where(ProductGroup.status == "pending")
    )
    pending_products = result.scalars().all()
    pending_count = len(pending_products)

    if pending_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No pending products to generate. Upload products first or check status filter.",
        )

    # Create job
    job = await job_manager.create_job(
        client_id=request.client_id,
        user_id=current_user.id,
        total_count=pending_count,
    )

    # Enqueue to ARQ
    await job_manager.enqueue_job(job)
    await db.commit()

    return GenerationJobResponse.model_validate(job)


@router.get("/jobs/{job_id}", response_model=GenerationJobResponse)
async def get_job_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """Get status of a generation job."""
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    # Verify user owns this job
    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this job",
        )

    return GenerationJobResponse.model_validate(job)


@router.get("/jobs/{job_id}/progress")
async def stream_job_progress(
    job_id: UUID,
    token: str = Query(..., description="JWT access token for authentication"),
    db: AsyncSession = Depends(get_db),
):
    """
    Stream job progress via Server-Sent Events.

    Events:
    - progress: Regular progress updates (every 500ms while running)
    - complete: Final update when job finishes
    - soft_cap: Sent when cost soft cap is hit
    - error: Sent on errors

    Client should close connection when 'complete' event received.

    Note: Token must be passed as query parameter since EventSource doesn't support headers.
    """
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"SSE progress request for job {job_id}")

    # Authenticate user from query parameter token (EventSource can't send headers)
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    payload = decode_access_token(token)
    if payload is None:
        logger.error("SSE: Token decode failed")
        raise credentials_exception

    user_id_str: str | None = payload.get("sub")
    if user_id_str is None:
        logger.error("SSE: No user_id in token payload")
        raise credentials_exception

    try:
        user_id = UUID(user_id_str)
    except (ValueError, AttributeError):
        logger.error(f"SSE: Invalid user_id format: {user_id_str}")
        raise credentials_exception

    # Fetch user from database
    result = await db.execute(select(User).where(User.id == user_id))
    current_user = result.scalar_one_or_none()

    if current_user is None:
        logger.error(f"SSE: User not found: {user_id}")
        raise credentials_exception

    # Verify job exists and user has access
    job_manager = JobManager(db)
    job = await job_manager.get_job(job_id)

    if not job:
        logger.error(f"SSE: Job not found: {job_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        logger.error(f"SSE: User {current_user.id} not authorized for job {job_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this job",
        )

    logger.info(f"SSE: Starting stream for job {job_id}")

    async def event_generator():
        """Generate SSE events for job progress."""
        # Need a fresh session for the generator (original closes after request setup)
        from app.database import async_session_maker

        try:
            while True:
                async with async_session_maker() as session:
                    manager = JobManager(session)
                    progress = await manager.get_job_progress(job_id)

                    if not progress:
                        yield {
                            "event": "error",
                            "data": json.dumps({"error": "Job not found"}),
                        }
                        break

                    # Check for soft cap pause
                    if (
                        progress["status"] == "paused"
                        and progress.get("status_reason", "").startswith("Cost soft cap")
                    ):
                        yield {
                            "event": "soft_cap",
                            "data": json.dumps({
                                "current_cost": progress["cost"],
                                "projected_cost": progress["projected_cost"],
                                "soft_cap": f"{settings.GENERATION_SOFT_CAP:.2f}",
                                "completed": progress["completed"],
                                "total": progress["total"],
                                "message": "Cost soft cap reached. Continue or stop?",
                            }),
                        }
                        # Don't break - keep streaming until user responds

                    # Send progress update
                    yield {
                        "event": "progress",
                        "data": json.dumps(progress),
                    }

                    # Check for terminal states
                    if progress["status"] in ["completed", "failed", "cancelled"]:
                        yield {
                            "event": "complete",
                            "data": json.dumps({
                                "status": progress["status"],
                                "summary": {
                                    "total_products": progress["total"],
                                    "successful": progress["success"],
                                    "failed": progress["failed"],
                                    "total_cost": progress["cost"],
                                    "elapsed_seconds": progress["elapsed_seconds"],
                                },
                            }),
                        }
                        break

                # Poll every 500ms
                await asyncio.sleep(0.5)

        except asyncio.CancelledError:
            # Client disconnected
            pass

    return EventSourceResponse(
        event_generator(),
        headers={
            "Access-Control-Allow-Origin": settings.FRONTEND_URL,
            "Access-Control-Allow-Credentials": "true",
            "Cache-Control": "no-cache",
        }
    )


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Pause a running generation job.

    The job will stop after completing the current product.
    Already generated products are preserved.
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to pause this job",
        )

    if job.status != "running":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot pause job with status '{job.status}'. Only running jobs can be paused.",
        )

    paused = await job_manager.pause_job(job_id)
    await db.commit()

    if not paused:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to pause job. It may have already completed or been paused.",
        )

    return {"message": "Job pause requested. Will stop after current product."}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Cancel a generation job.

    The job will stop after completing the current product.
    Already generated products are preserved with 'generated' status.
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to cancel this job",
        )

    if job.status in ["completed", "cancelled", "failed"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot cancel job with status '{job.status}'.",
        )

    cancelled = await job_manager.cancel_job(job_id)
    await db.commit()

    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to cancel job.",
        )

    return {"message": "Job cancelled. Already generated products are preserved."}


@router.post("/jobs/{job_id}/resume", response_model=GenerationJobResponse)
async def resume_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Resume a paused generation job.

    Creates a new job that continues from where the paused job stopped.
    Products already generated are skipped (they have 'generated' status).
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to resume this job",
        )

    if job.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot resume job with status '{job.status}'. Only paused jobs can be resumed.",
        )

    # Resume creates a new job
    new_job = await job_manager.resume_job(job)
    await db.commit()

    return GenerationJobResponse.model_validate(new_job)


@router.post("/jobs/{job_id}/soft-cap-continue", response_model=GenerationJobResponse | None)
async def soft_cap_continue(
    job_id: UUID,
    continue_generation: bool,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Handle user response to soft cap dialog.

    Args:
        continue_generation: True to continue despite cost, False to stop

    Returns:
        New job if continuing, None if stopping
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    if job.status != "paused":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Job is not paused at soft cap",
        )

    new_job = await job_manager.acknowledge_soft_cap(job_id, continue_generation)
    await db.commit()

    if new_job:
        return GenerationJobResponse.model_validate(new_job)
    return None


@router.post("/jobs/{job_id}/force-cancel")
async def force_cancel_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Force cancel and clear a job (works on any status including running/pending).

    Marks job as cancelled and resets all products back to pending.
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized",
        )

    # Reset all product groups for this client back to pending
    from sqlalchemy import update
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.client_id == job.client_id)
        .values(status="pending", generated_title=None, generated_description=None)
    )

    # Mark job as cancelled
    await db.execute(
        update(GenerationJob)
        .where(GenerationJob.id == job_id)
        .values(status="cancelled")
    )
    await db.commit()

    return {"message": "Job cancelled and products reset to pending"}


@router.delete("/jobs/{job_id}")
async def delete_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Delete a generation job (for debugging/cleanup).

    Also resets all associated product groups back to 'pending' status.
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this job",
        )

    # Reset all product groups for this client back to pending
    from sqlalchemy import update
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.client_id == job.client_id)
        .where(ProductGroup.status.in_(["failed", "generated"]))
        .values(status="pending", generated_title=None, generated_description=None)
    )

    # Delete the job
    await db.delete(job)
    await db.commit()

    return {"message": "Job deleted and products reset to pending"}


@router.post("/jobs/{job_id}/reset")
async def reset_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Reset a failed/completed job for retry (for debugging).

    Resets job status to pending and all product groups back to pending.
    """
    job = await job_manager.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found",
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to reset this job",
        )

    # Reset all product groups for this client back to pending
    from sqlalchemy import update
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.client_id == job.client_id)
        .values(status="pending", generated_title=None, generated_description=None)
    )

    # Reset job counters
    await db.execute(
        update(GenerationJob)
        .where(GenerationJob.id == job_id)
        .values(
            status="pending",
            completed_count=0,
            success_count=0,
            failed_count=0,
            total_cost=0,
            total_input_tokens=0,
            total_output_tokens=0,
            started_at=None,
            completed_at=None,
            paused_at=None,
            error_message=None,
        )
    )
    await db.commit()

    return {"message": "Job and products reset to pending. You can start generation again."}


@router.post("/retry-failed/{client_id}", response_model=GenerationJobResponse)
async def retry_failed_products(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Reset all failed products to pending and start a new generation job.

    - Validates client exists and belongs to user
    - Checks no active job already exists
    - Resets all 'failed' products to 'pending'
    - Creates and enqueues a new generation job
    """
    from sqlalchemy import update, func

    # Validate client exists and belongs to user
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

    # Check for existing active job
    existing_job = await job_manager.get_active_job_for_client(client_id)
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Generation already in progress for this client. Job ID: {existing_job.id}",
        )

    # Count failed products
    result = await db.execute(
        select(func.count(ProductGroup.id))
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.status == "failed")
    )
    failed_count = result.scalar() or 0

    if failed_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No failed products to retry.",
        )

    # Reset failed products to pending
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.client_id == client_id)
        .where(ProductGroup.status == "failed")
        .values(
            status="pending",
            generated_title=None,
            generated_description=None,
        )
    )

    # Create job for the failed (now pending) products
    job = await job_manager.create_job(
        client_id=client_id,
        user_id=current_user.id,
        total_count=failed_count,
    )

    # Enqueue to ARQ
    await job_manager.enqueue_job(job)
    await db.commit()

    return GenerationJobResponse.model_validate(job)


@router.post("/product/{product_group_id}", response_model=GenerationJobResponse)
async def generate_single_product(
    product_group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Generate/regenerate content for a single product.

    - Validates product exists and user owns it
    - Checks no active job already exists for the client
    - Resets product to 'pending' status and clears generated content
    - Creates a job targeting this specific product
    """
    from sqlalchemy import update

    # Get product group and verify ownership
    result = await db.execute(
        select(ProductGroup).where(ProductGroup.id == product_group_id)
    )
    product_group = result.scalar_one_or_none()

    if not product_group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )

    # Verify user owns the client
    result = await db.execute(
        select(Client).where(
            Client.id == product_group.client_id,
            Client.user_id == current_user.id,
        )
    )
    client = result.scalar_one_or_none()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to generate for this product",
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

    # Check for existing active job
    existing_job = await job_manager.get_active_job_for_client(product_group.client_id)
    if existing_job:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Generation already in progress for this client. Job ID: {existing_job.id}",
        )

    # Reset product to pending
    await db.execute(
        update(ProductGroup)
        .where(ProductGroup.id == product_group_id)
        .values(
            status="pending",
            generated_title=None,
            generated_description=None,
        )
    )

    # Create job targeting this specific product
    job = await job_manager.create_job(
        client_id=product_group.client_id,
        user_id=current_user.id,
        total_count=1,
        target_product_group_id=product_group_id,
    )

    # Enqueue to ARQ
    await job_manager.enqueue_job(job)
    await db.commit()

    return GenerationJobResponse.model_validate(job)


@router.get("/client/{client_id}/jobs")
async def get_all_jobs_for_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Get all generation jobs for a client (for debugging).
    """
    from sqlalchemy import select

    # Verify client belongs to user
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

    # Get all jobs for this client
    result = await db.execute(
        select(GenerationJob)
        .where(GenerationJob.client_id == client_id)
        .order_by(GenerationJob.created_at.desc())
    )
    jobs = result.scalars().all()

    return [
        {
            "id": str(j.id),
            "status": j.status,
            "created_at": j.created_at.isoformat() if j.created_at else None,
            "completed": j.completed_count,
            "total": j.total_count,
        }
        for j in jobs
    ]


@router.get("/client/{client_id}/active", response_model=GenerationJobResponse | None)
async def get_active_job_for_client(
    client_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    job_manager: JobManager = Depends(get_job_manager),
):
    """
    Get the active generation job for a client, if any.

    Returns the running/pending job, or None if no active job.
    Useful for checking if generation is in progress before uploading.
    """
    # Verify client belongs to user
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

    job = await job_manager.get_active_job_for_client(client_id)

    if job:
        return GenerationJobResponse.model_validate(job)
    return None
