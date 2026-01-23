"""ARQ worker settings configuration."""

from arq.connections import RedisSettings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.config import settings


async def startup(ctx: dict) -> None:
    """
    Initialize worker context on startup.

    Creates database connection pool for use during job execution.
    """
    # Create async engine with connection pooling
    engine = create_async_engine(
        settings.DATABASE_URL,
        pool_size=5,
        max_overflow=10,
        pool_pre_ping=True,
        pool_recycle=3600,  # Recycle connections every hour
    )

    # Create session factory
    session_factory = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    ctx["db_engine"] = engine
    ctx["db_session_factory"] = session_factory


async def shutdown(ctx: dict) -> None:
    """
    Cleanup worker resources on shutdown.

    Properly disposes of database connection pool.
    """
    engine = ctx.get("db_engine")
    if engine:
        await engine.dispose()


def get_redis_settings() -> RedisSettings:
    """Parse REDIS_URL into RedisSettings."""
    url = settings.REDIS_URL
    # Parse redis://host:port format
    if url.startswith("redis://"):
        url = url[8:]  # Remove redis://
    if ":" in url:
        host, port = url.split(":")
        return RedisSettings(host=host, port=int(port))
    return RedisSettings(host=url)


class WorkerSettings:
    """ARQ worker configuration."""

    # Redis connection
    redis_settings = get_redis_settings()

    # Worker functions to register
    functions = [
        "app.workers.generation_worker.generation_worker",
        "app.workers.review_worker.batch_ai_review_worker",
    ]

    # Lifecycle hooks
    on_startup = startup
    on_shutdown = shutdown

    # Worker behavior
    max_jobs = 5  # Max concurrent jobs per worker
    job_timeout = 7200  # 2 hour max per job (for large batches)
    keep_result = 3600  # Keep job results for 1 hour
    poll_delay = 0.5  # Poll Redis every 500ms

    # Health check
    health_check_interval = 30  # Seconds between health checks
