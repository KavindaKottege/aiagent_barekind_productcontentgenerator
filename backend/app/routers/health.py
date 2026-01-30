"""Health check endpoints for container orchestration.

Provides:
- Liveness probe: GET /health -- confirms the process is alive
- Readiness probe: GET /health/ready -- confirms DB and Redis are reachable
"""

import asyncio

import redis.asyncio as aioredis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.config import settings
from app.database import async_session_maker

router = APIRouter(tags=["health"])

CHECK_TIMEOUT_SECONDS = 5


@router.get("/health")
async def liveness():
    """Liveness probe -- confirms the process is running."""
    return {"status": "healthy"}


@router.get("/health/ready")
async def readiness():
    """Readiness probe -- confirms database and Redis are reachable."""
    checks: dict[str, str] = {}

    # Database check
    try:
        async with async_session_maker() as session:
            await asyncio.wait_for(
                session.execute(text("SELECT 1")),
                timeout=CHECK_TIMEOUT_SECONDS,
            )
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {str(e)}"

    # Redis check
    try:
        r = aioredis.from_url(settings.REDIS_URL)
        try:
            await asyncio.wait_for(
                r.ping(),
                timeout=CHECK_TIMEOUT_SECONDS,
            )
            checks["redis"] = "ok"
        finally:
            await r.aclose()
    except Exception as e:
        checks["redis"] = f"error: {str(e)}"

    all_ok = all(v == "ok" for v in checks.values())

    if all_ok:
        return {"status": "ready", "checks": checks}

    return JSONResponse(
        status_code=503,
        content={"status": "not_ready", "checks": checks},
    )
