"""Redis connection pool with graceful degradation.

If Redis is unavailable at startup or during a request, the dependency
returns None instead of raising — callers must handle the None case.
Features that require Redis (caching, rate limiting, worker heartbeat)
will be silently skipped rather than breaking the entire request.
"""

import logging
from collections.abc import AsyncGenerator

from redis.asyncio import Redis
from redis.asyncio import from_url as redis_from_url
from redis.exceptions import RedisError

from app.core.config import settings

logger = logging.getLogger(__name__)

_redis: Redis | None = None


async def create_redis_pool() -> Redis | None:
    """Create and return a Redis connection pool, or None on failure."""
    global _redis
    try:
        client: Redis = redis_from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
        await client.ping()
        _redis = client
        return _redis
    except RedisError as exc:
        logger.warning("Redis unavailable, degraded mode active: %s", exc)
        return None


async def close_redis_pool() -> None:
    """Close the Redis connection pool if it was opened."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def get_redis() -> AsyncGenerator[Redis | None, None]:
    """Yield the shared Redis client, or None when Redis is unavailable."""
    if _redis is None:
        logger.warning("Redis is not available, skipping for this request")
    yield _redis
