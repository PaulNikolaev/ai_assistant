"""Qdrant async client initialisation and health check.

A single AsyncQdrantClient instance is created at application startup
via init_qdrant() and shared across all requests through get_qdrant().
"""

import logging

from qdrant_client import AsyncQdrantClient
from qdrant_client.http.exceptions import UnexpectedResponse

from app.core.config import settings

logger = logging.getLogger(__name__)

_client: AsyncQdrantClient | None = None


def init_qdrant() -> AsyncQdrantClient:
    """Create and store the shared AsyncQdrantClient instance."""
    global _client
    _client = AsyncQdrantClient(url=settings.QDRANT_URL)
    logger.info("Qdrant client initialised: %s", settings.QDRANT_URL)
    return _client


async def close_qdrant() -> None:
    """Close the Qdrant client connection on application shutdown."""
    global _client
    if _client is not None:
        await _client.close()
        _client = None


def get_qdrant() -> AsyncQdrantClient:
    """Return the shared Qdrant client instance.

    Raises:
        RuntimeError: If called before init_qdrant().
    """
    if _client is None:
        raise RuntimeError("Qdrant client is not initialised. Call init_qdrant() first.")
    return _client


async def check_qdrant() -> bool:
    """Return True if Qdrant is reachable and responds to list_collections."""
    if _client is None:
        return False
    try:
        await _client.get_collections()
        return True
    except (UnexpectedResponse, Exception) as exc:
        logger.warning("Qdrant health check failed: %s", exc)
        return False
