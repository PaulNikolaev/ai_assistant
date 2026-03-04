"""CRUD operations for RefreshToken model."""

import uuid
from datetime import datetime, timezone
from typing import cast

from sqlalchemy import delete, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.refresh_token import RefreshToken


async def create(
    db: AsyncSession,
    user_id: uuid.UUID,
    token_hash: str,
    expires_at: datetime,
    device_name: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> RefreshToken:
    """Create and persist a refresh token record. Caller should commit."""
    rt = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_name=device_name,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(rt)
    await db.flush()
    await db.refresh(rt)
    return rt


async def get_by_hash(db: AsyncSession, token_hash: str) -> RefreshToken | None:
    """Return the refresh token record for the given hash, or None."""
    result = await db.execute(
        select(RefreshToken).where(RefreshToken.token_hash == token_hash)
    )
    return result.scalar_one_or_none()


async def revoke(db: AsyncSession, token_id: uuid.UUID) -> None:
    """Mark the token as revoked and set revoked_at. Caller should commit."""
    now = datetime.now(timezone.utc)
    await db.execute(
        update(RefreshToken)
        .where(RefreshToken.id == token_id)
        .values(revoked=True, revoked_at=now),
        execution_options={"synchronize_session": False},
    )


async def revoke_all_for_user(db: AsyncSession, user_id: uuid.UUID) -> int:
    """Revoke all refresh tokens for the user (e.g. on token theft). Returns count updated."""
    now = datetime.now(timezone.utc)
    result = cast(
        CursorResult,
        await db.execute(
            update(RefreshToken)
            .where(RefreshToken.user_id == user_id)
            .values(revoked=True, revoked_at=now),
            execution_options={"synchronize_session": False},
        ),
    )
    return result.rowcount or 0


async def delete_expired(db: AsyncSession) -> int:
    """Delete tokens with expires_at < now(). Returns number of deleted rows."""
    now = datetime.now(timezone.utc)
    result = cast(
        CursorResult,
        await db.execute(delete(RefreshToken).where(RefreshToken.expires_at < now)),
    )
    return result.rowcount or 0
