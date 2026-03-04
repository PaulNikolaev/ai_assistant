"""Unit tests for security utilities (no DB)."""

from datetime import timedelta

import pytest
from fastapi import HTTPException

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    hash_refresh_token,
    verify_password,
)


def test_hash_password_produces_bcrypt_hash():
    """Hashed password must have bcrypt prefix $2b$."""
    hashed = hash_password("secret123")
    assert hashed.startswith("$2b$")


def test_verify_password_correct():
    """Correct password returns True."""
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed) is True


def test_verify_password_wrong():
    """Wrong password returns False."""
    hashed = hash_password("secret123")
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token():
    """Decoded access token payload must contain sub."""
    payload = {"sub": "user-123"}
    token = create_access_token(data=payload)
    decoded = decode_token(token)
    assert decoded["sub"] == "user-123"


def test_decode_expired_token_raises_401():
    """Expired token must raise HTTPException 401."""
    payload = {"sub": "user-123"}
    token = create_access_token(data=payload, expire_delta=-timedelta(minutes=5))
    with pytest.raises(HTTPException) as exc_info:
        decode_token(token)
    assert exc_info.value.status_code == 401


def test_decode_invalid_token_raises_401():
    """Invalid token must raise HTTPException 401."""
    with pytest.raises(HTTPException) as exc_info:
        decode_token("invalid.jwt.token")
    assert exc_info.value.status_code == 401


def test_create_refresh_token_length():
    """Refresh token must be at least 32 characters."""
    token = create_refresh_token()
    assert len(token) >= 32


def test_hash_refresh_token_is_hex_64():
    """SHA-256 hex digest of refresh token must be 64 characters."""
    token = create_refresh_token()
    digest = hash_refresh_token(token)
    assert len(digest) == 64
    assert all(c in "0123456789abcdef" for c in digest)
