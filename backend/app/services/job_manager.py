"""Job manager service for generation job lifecycle management."""

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID, uuid4

from arq import create_pool
from arq.connections import ArqRedis, RedisSettings
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.generation_job import GenerationJob


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into RedisSettings."""
    url = settings.REDIS_URL
    if url.startswith("redis://"):
        url = url[8:]
    if ":" in url:
        host, port = url.split(":")
        return RedisSettings(host=host, port=int(port))
    return RedisSettings(host=url)


class JobManager:
    """
    Manages generation job lifecycle.

    Handles job creation, enqueueing to ARQ, status updates,
    and provides methods for pause/cancel/resume operations.
    """

    def __init__(self, db: AsyncSession):
        """Initialize job manager with database session."""
        self.db = db
        self._redis_pool: ArqRedis | None = None

    async def get_redis_pool(self) -> ArqRedis:
        """Get or create Redis connection pool."""
        if self._redis_pool is None:
            self._redis_pool = await create_pool(get_redis_settings())
        return self._redis_pool

    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._redis_pool:
            await self._redis_pool.close()
            self._redis_pool = None

    async def create_job(
        self,
        client_id: UUID,
        user_id: UUID,
        total_count: int = 0,
    ) -> GenerationJob:
        """
        Create a new generation job in pending state.

        Args:
            client_id: Client to generate content for
            user_id: User who initiated the job
            total_count: Number of products to generate

        Returns:
            Created GenerationJob instance
        """
        job = GenerationJob(
            id=uuid4(),
            client_id=client_id,
            user_id=user_id,
            status="pending",
            total_count=total_count,
        )
        self.db.add(job)
        await self.db.flush()  # Get the ID without committing
        return job

    async def enqueue_job(self, job: GenerationJob) -> str:
        """
        Enqueue a job to ARQ for background processing.

        Args:
            job: The GenerationJob to enqueue

        Returns:
            ARQ job ID
        """
        pool = await self.get_redis_pool()

        arq_job = await pool.enqueue_job(
            "generation_worker",
            str(job.id),
            str(job.client_id),
            str(job.user_id),
            _job_id=str(job.id),  # Use our UUID as ARQ job ID
        )

        return arq_job.job_id

    async def get_job(self, job_id: UUID) -> GenerationJob | None:
        """Get a job by ID."""
        result = await self.db.execute(
            select(GenerationJob).where(GenerationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def get_active_job_for_client(self, client_id: UUID) -> GenerationJob | None:
        """
        Get active (running/pending) job for a client.

        Returns None if no active job exists.
        """
        result = await self.db.execute(
            select(GenerationJob)
            .where(GenerationJob.client_id == client_id)
            .where(GenerationJob.status.in_(["pending", "running"]))
            .order_by(GenerationJob.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def pause_job(self, job_id: UUID) -> bool:
        """
        Request job pause.

        Sets status to 'paused' - worker checks this before each product
        and will stop processing.

        Returns True if job was running and is now being paused.
        """
        result = await self.db.execute(
            update(GenerationJob)
            .where(
                GenerationJob.id == job_id,
                GenerationJob.status == "running",
            )
            .values(
                status="paused",
                paused_at=datetime.now(timezone.utc),
                status_reason="Paused by user",
            )
        )
        return result.rowcount > 0

    async def cancel_job(self, job_id: UUID) -> bool:
        """
        Request job cancellation.

        Sets status to 'cancelled' - worker checks this before each product
        and will stop processing. Already generated products are kept.

        Returns True if job was active and is now being cancelled.
        """
        result = await self.db.execute(
            update(GenerationJob)
            .where(
                GenerationJob.id == job_id,
                GenerationJob.status.in_(["pending", "running", "paused"]),
            )
            .values(
                status="cancelled",
                completed_at=datetime.now(timezone.utc),
                status_reason="Cancelled by user",
            )
        )
        return result.rowcount > 0

    async def resume_job(self, job: GenerationJob) -> GenerationJob:
        """
        Resume a paused job.

        Creates a NEW job that continues from where the paused job left off.
        The original job remains paused for audit trail.

        Workers automatically skip products with 'generated' status,
        so resume effectively continues from where it stopped.

        Args:
            job: The paused job to resume from

        Returns:
            New GenerationJob instance
        """
        # Create new job continuing from the paused one
        new_job = GenerationJob(
            id=uuid4(),
            client_id=job.client_id,
            user_id=job.user_id,
            status="pending",
            total_count=job.total_count,
            # Carry over existing counts (will be updated by worker)
            completed_count=job.completed_count,
            success_count=job.success_count,
            failed_count=job.failed_count,
            total_cost=job.total_cost,
            total_input_tokens=job.total_input_tokens,
            total_cached_input_tokens=job.total_cached_input_tokens,
            total_output_tokens=job.total_output_tokens,
            # Carry over cost breakdown
            total_input_cost=job.total_input_cost,
            total_cached_input_cost=job.total_cached_input_cost,
            total_output_cost=job.total_output_cost,
            # Preserve cumulative elapsed time
            elapsed_seconds=job.elapsed_seconds,
        )
        self.db.add(new_job)
        await self.db.flush()

        # Enqueue the new job
        await self.enqueue_job(new_job)

        return new_job

    async def acknowledge_soft_cap(self, job_id: UUID, continue_generation: bool) -> GenerationJob | None:
        """
        Handle user response to soft cap dialog.

        Args:
            job_id: ID of the paused job
            continue_generation: True to continue, False to keep paused

        Returns:
            New job if continuing, None if staying paused
        """
        job = await self.get_job(job_id)
        if not job or job.status != "paused":
            return None

        if not continue_generation:
            # User chose to stop - update reason
            await self.db.execute(
                update(GenerationJob)
                .where(GenerationJob.id == job_id)
                .values(status_reason="Stopped at soft cap by user")
            )
            return None

        # User chose to continue - resume job
        return await self.resume_job(job)

    async def get_job_progress(self, job_id: UUID) -> dict | None:
        """
        Get current job progress for SSE stream.

        Returns dict with progress info or None if job not found.
        """
        job = await self.get_job(job_id)
        if not job:
            return None

        # Calculate elapsed time
        elapsed_seconds = 0
        if job.started_at:
            end_time = job.completed_at or job.paused_at or datetime.now(timezone.utc)
            elapsed_seconds = int((end_time - job.started_at).total_seconds())

        # Estimate remaining time based on average
        estimated_remaining = None
        if job.completed_count > 0 and job.total_count > job.completed_count:
            avg_time_per_product = elapsed_seconds / job.completed_count
            remaining_products = job.total_count - job.completed_count
            estimated_remaining = int(avg_time_per_product * remaining_products)

        # Calculate projected cost
        projected_cost = job.total_cost
        if job.completed_count > 0 and job.total_count > job.completed_count:
            avg_cost = job.total_cost / Decimal(job.completed_count)
            remaining = job.total_count - job.completed_count
            projected_cost = job.total_cost + (avg_cost * Decimal(remaining))

        return {
            "status": job.status,
            "completed": job.completed_count,
            "total": job.total_count,
            "success": job.success_count,
            "failed": job.failed_count,
            "cost": f"{job.total_cost:.2f}",
            "projected_cost": f"{projected_cost:.2f}",
            "elapsed_seconds": elapsed_seconds,
            "estimated_remaining_seconds": estimated_remaining,
            "status_reason": job.status_reason,
        }
