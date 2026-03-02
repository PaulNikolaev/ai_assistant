"""MinIO storage backend via boto3.

StorageBackend wraps a synchronous boto3 S3 client and runs all
blocking calls in a thread pool executor so they don't block the
async event loop. Use get_storage() as a FastAPI dependency.
"""

import asyncio
import io
import logging
from functools import partial
from typing import Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.core.config import settings

logger = logging.getLogger(__name__)


class StorageBackend:
    """S3-compatible storage client backed by MinIO."""

    def __init__(self) -> None:
        self._client: Any = boto3.client(
            "s3",
            endpoint_url=settings.MINIO_ENDPOINT,
            aws_access_key_id=settings.MINIO_ACCESS_KEY,
            aws_secret_access_key=settings.MINIO_SECRET_KEY,
            region_name="us-east-1",
        )
        self._bucket = settings.MINIO_BUCKET

    # ── Internal helpers ──────────────────────────────────────────

    @staticmethod
    async def _run(func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute a blocking boto3 call in the default thread pool."""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(func, *args, **kwargs))

    # ── Public API ────────────────────────────────────────────────

    def ensure_bucket_exists(self) -> None:
        """Create the configured bucket if it does not already exist.

        Called once at application startup. Errors are logged but do
        not raise so that the app can start even with degraded storage.
        """
        try:
            self._client.head_bucket(Bucket=self._bucket)
        except ClientError as exc:
            code = exc.response["Error"]["Code"]
            if code in ("404", "NoSuchBucket"):
                self._client.create_bucket(Bucket=self._bucket)
                logger.info("Created MinIO bucket: %s", self._bucket)
            else:
                logger.error("MinIO bucket check failed: %s", exc)
        except BotoCoreError as exc:
            logger.error("MinIO unreachable during bucket check: %s", exc)

    async def upload_file(
        self,
        file_data: bytes,
        key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload bytes to the bucket and return the object key.

        Args:
            file_data: Raw file bytes to upload.
            key: Object key (path) inside the bucket.
            content_type: MIME type stored as object metadata.

        Returns:
            The object key on success.

        Raises:
            ClientError: When the upload fails on the storage side.
        """
        await self._run(
            self._client.upload_fileobj,
            io.BytesIO(file_data),  # type: ignore[arg-type]
            self._bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        logger.debug("Uploaded file to MinIO: %s", key)
        return key

    async def delete_file(self, key: str) -> None:
        """Delete an object from the bucket.

        Args:
            key: Object key to delete.
        """
        await self._run(
            self._client.delete_object,
            Bucket=self._bucket,
            Key=key,
        )
        logger.debug("Deleted file from MinIO: %s", key)

    async def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate a pre-signed GET URL for the given object key.

        Args:
            key: Object key to generate a URL for.
            expires_in: URL validity duration in seconds (default 1 hour).

        Returns:
            Pre-signed URL string.
        """
        url: str = await self._run(
            self._client.generate_presigned_url,
            "get_object",
            Params={"Bucket": self._bucket, "Key": key},
            ExpiresIn=expires_in,
        )
        return url

    async def check(self) -> bool:
        """Return True if MinIO is reachable and the bucket exists."""
        try:
            await self._run(self._client.head_bucket, Bucket=self._bucket)
            return True
        except (ClientError, BotoCoreError):
            return False


_storage: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """Return the shared StorageBackend instance.

    Initialised once at application startup via init_storage().
    Raises RuntimeError if called before initialisation.
    """
    if _storage is None:
        raise RuntimeError("Storage backend is not initialised. Call init_storage() first.")
    return _storage


def init_storage() -> StorageBackend:
    """Create the shared StorageBackend and ensure the bucket exists."""
    global _storage
    _storage = StorageBackend()
    _storage.ensure_bucket_exists()
    return _storage
