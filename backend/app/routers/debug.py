"""Admin-only debug API endpoints for viewing generation audit logs."""

from datetime import datetime
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.generation_audit import GenerationAudit
from app.models.generation_job import GenerationJob
from app.models.user import User
from app.schemas.debug import DebugLogEntry
from app.utils.dependencies import get_current_admin

router = APIRouter(prefix="/debug", tags=["debug"])


def _audit_to_entry(audit: GenerationAudit) -> DebugLogEntry:
    """Convert a GenerationAudit ORM object to a DebugLogEntry response."""
    return DebugLogEntry(
        id=str(audit.id),
        job_id=str(audit.job_id),
        product_group_id=str(audit.product_group_id),
        attempt_number=audit.attempt_number,
        prompt_used=audit.prompt_used,
        model_version=audit.model_version,
        temperature=float(audit.temperature),
        input_tokens=audit.input_tokens,
        output_tokens=audit.output_tokens,
        cost=str(audit.cost),
        duration_ms=audit.duration_ms,
        success=audit.success,
        error_message=audit.error_message,
        generated_title=audit.generated_title,
        generated_description=audit.generated_description,
        title_length=audit.title_length,
        description_length=audit.description_length,
        created_at=audit.created_at.isoformat(),
    )


@router.get("/logs/{job_id}", response_model=list[DebugLogEntry])
async def get_debug_logs(
    job_id: UUID,
    _admin: Annotated[User, Depends(get_current_admin)],
    since: datetime | None = Query(None, description="Only return logs after this timestamp (ISO 8601)"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    db: AsyncSession = Depends(get_db),
) -> list[DebugLogEntry]:
    """Get generation audit logs for a specific job.

    Admin-only endpoint. Supports incremental polling via the `since` parameter.
    Returns entries ordered by created_at ASC.
    """
    stmt = select(GenerationAudit).where(GenerationAudit.job_id == job_id)

    if since is not None:
        stmt = stmt.where(GenerationAudit.created_at > since)

    stmt = stmt.order_by(GenerationAudit.created_at.asc()).limit(limit)

    result = await db.execute(stmt)
    audits = result.scalars().all()

    return [_audit_to_entry(a) for a in audits]


@router.get("/logs/client/{client_id}/latest", response_model=list[DebugLogEntry])
async def get_debug_logs_for_client_latest(
    client_id: UUID,
    _admin: Annotated[User, Depends(get_current_admin)],
    since: datetime | None = Query(None, description="Only return logs after this timestamp (ISO 8601)"),
    limit: int = Query(50, ge=1, le=200, description="Max entries to return"),
    db: AsyncSession = Depends(get_db),
) -> list[DebugLogEntry]:
    """Get audit logs for the most recent generation job of a client.

    Admin-only endpoint. Useful when the debug panel opens mid-generation and
    the frontend does not yet know the job_id. Returns an empty list if no
    job exists for the client.
    """
    # Find the most recent job for this client
    job_stmt = (
        select(GenerationJob.id)
        .where(GenerationJob.client_id == client_id)
        .order_by(GenerationJob.created_at.desc())
        .limit(1)
    )
    job_result = await db.execute(job_stmt)
    latest_job_id = job_result.scalar_one_or_none()

    if latest_job_id is None:
        return []

    # Fetch audit entries for that job
    stmt = select(GenerationAudit).where(GenerationAudit.job_id == latest_job_id)

    if since is not None:
        stmt = stmt.where(GenerationAudit.created_at > since)

    stmt = stmt.order_by(GenerationAudit.created_at.asc()).limit(limit)

    result = await db.execute(stmt)
    audits = result.scalars().all()

    return [_audit_to_entry(a) for a in audits]
