"""Redis connection pool with graceful degradation.

If Redis is unavailable at startup or during a request, the dependency
returns None instead of raising — callers must handle the None case.
Features that require Redis (caching, rate limiting, worker heartbeat)
will be silently skipped rather than breaking the entire request.
"""

from collections.abc import AsyncGenerator

import structlog
from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url
from redis.exceptions import RedisError

from app.core.config import settings

logger = structlog.get_logger(__name__)

_redis: Redis | None = None


async def create_redis_pool() -> Redis | None:
    """Create and return a Redis connection pool, or None on failure."""
    global _redis
    try:
        client: Redis = redis_from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
            max_connections=20,
            socket_connect_timeout=2,
            socket_timeout=2,
        )
        await client.ping()
        _redis = client
        return _redis
    except RedisError as exc:
        logger.warning("Redis unavailable, degraded mode active", exc_info=exc)
        return None


async def close_redis_pool() -> None:
    """Close the Redis connection pool if it was opened."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


def get_redis_client() -> Redis | None:
    """Return the shared Redis client, or None when Redis is unavailable."""
    return _redis


async def get_redis() -> AsyncGenerator[Redis | None, None]:
    """Yield the shared Redis client, or None when Redis is unavailable."""
    yield _redis
