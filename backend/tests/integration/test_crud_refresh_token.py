"""Integration tests for refresh token CRUD (with DB)."""

from datetime import datetime, timedelta, timezone

import pytest_asyncio

from app.core.security import hash_refresh_token
from app.crud import refresh_token as crud_refresh_token
from tests.factories import UserFactory


@pytest_asyncio.fixture
async def user_id(db):
    """Create a user and return its id (same session, flushed)."""
    user = UserFactory()
    db.add(user)
    await db.flush()
    return user.id


async def test_create_refresh_token(db, user_id):
    """Created record must be persisted in DB."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    token_hash = hash_refresh_token("random-token-string")
    rt = await crud_refresh_token.create(
        db,
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        device_name="Chrome",
        ip_address="127.0.0.1",
        user_agent="Mozilla/5.0",
    )
    await db.commit()
    assert rt.id is not None
    assert rt.user_id == user_id
    assert rt.token_hash == token_hash
    assert rt.revoked is False


async def test_get_by_hash_found(db, user_id):
    """get_by_hash must return the record when hash exists."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    token_hash = hash_refresh_token("unique-token")
    await crud_refresh_token.create(
        db, user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
    await db.commit()
    found = await crud_refresh_token.get_by_hash(db, token_hash)
    assert found is not None
    assert found.token_hash == token_hash


async def test_get_by_hash_not_found(db):
    """get_by_hash must return None when hash does not exist."""
    found = await crud_refresh_token.get_by_hash(
        db, "a" * 64
    )  # valid hex length, no such row
    assert found is None


async def test_revoke_sets_revoked_flag(db, user_id):
    """revoke must set revoked=True and revoked_at."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    token_hash = hash_refresh_token("revoke-me")
    rt = await crud_refresh_token.create(
        db, user_id=user_id, token_hash=token_hash, expires_at=expires_at
    )
    await db.commit()
    await crud_refresh_token.revoke(db, rt.id)
    await db.commit()
    await db.refresh(rt)
    assert rt.revoked is True
    assert rt.revoked_at is not None


async def test_revoke_all_for_user(db, user_id):
    """All tokens for the user must be revoked."""
    expires_at = datetime.now(timezone.utc) + timedelta(days=30)
    h1 = hash_refresh_token("t1")
    h2 = hash_refresh_token("t2")
    await crud_refresh_token.create(db, user_id=user_id, token_hash=h1, expires_at=expires_at)
    await crud_refresh_token.create(db, user_id=user_id, token_hash=h2, expires_at=expires_at)
    await db.commit()
    count = await crud_refresh_token.revoke_all_for_user(db, user_id)
    await db.commit()
    assert count == 2
    r1 = await crud_refresh_token.get_by_hash(db, h1)
    r2 = await crud_refresh_token.get_by_hash(db, h2)
    assert r1.revoked and r2.revoked


async def test_delete_expired_removes_only_expired(db, user_id):
    """Only expired tokens must be deleted; active ones remain."""
    past = datetime.now(timezone.utc) - timedelta(days=1)
    future = datetime.now(timezone.utc) + timedelta(days=30)
    expired_hash = hash_refresh_token("expired-token")
    active_hash = hash_refresh_token("active-token")
    await crud_refresh_token.create(db, user_id=user_id, token_hash=expired_hash, expires_at=past)
    await crud_refresh_token.create(db, user_id=user_id, token_hash=active_hash, expires_at=future)
    await db.commit()
    deleted = await crud_refresh_token.delete_expired(db)
    await db.commit()
    assert deleted == 1
    assert await crud_refresh_token.get_by_hash(db, expired_hash) is None
    assert await crud_refresh_token.get_by_hash(db, active_hash) is not None
