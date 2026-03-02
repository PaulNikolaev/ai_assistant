"""ARQ background worker — cron jobs and async task execution.

Manages its own database and Redis connections independently of the
FastAPI application. The heartbeat cron writes a liveness key to Redis
so the /health endpoint can confirm the worker is running.
"""

import os
from typing import Any, cast

import structlog
from arq import cron
from arq.connections import RedisSettings
from arq.typing import WorkerCoroutine
from sqlalchemy import delete, func, text

from app.core.database import AsyncSessionLocal, engine
from app.core.models.refresh_token import RefreshToken

logger = structlog.get_logger(__name__)


async def heartbeat(ctx: dict[str, Any]) -> None:
    """Write a liveness key to Redis, renewed every 30 seconds."""
    await ctx["redis"].set("worker:heartbeat", "1", ex=60)


async def cleanup_expired_tokens(_ctx: dict[str, Any]) -> None:
    """Delete expired refresh tokens to keep the table lean."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            delete(RefreshToken).where(RefreshToken.expires_at < func.now())
        )
        await session.commit()
        logger.info("expired refresh tokens removed", count=result.rowcount)


async def on_startup(_ctx: dict[str, Any]) -> None:
    """Verify database connectivity before the worker starts accepting jobs."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("worker startup: database connection ok")
    except Exception as exc:
        logger.error("worker startup: database connection failed", exc_info=exc)
        raise


async def on_shutdown(_ctx: dict[str, Any]) -> None:
    """Close the SQLAlchemy engine connection pool on worker shutdown."""
    await engine.dispose()
    logger.info("worker shutdown: database connections closed")


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(
        os.getenv("REDIS_URL", "redis://redis:6379")
    )
    functions = [cleanup_expired_tokens]
    cron_jobs = [
        cron(cast(WorkerCoroutine, heartbeat), second={0, 30}),
        cron(cast(WorkerCoroutine, cleanup_expired_tokens), hour=3, minute=0),
    ]
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = 10
    job_timeout = 300
