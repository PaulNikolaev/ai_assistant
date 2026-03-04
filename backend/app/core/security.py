"""Security utilities: password hashing, JWT access tokens, refresh token helpers."""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(plain: str) -> str:
    """Hash a plain-text password with bcrypt."""
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


async def hash_password_async(plain: str) -> str:
    """Hash password in a thread pool (use from async code to avoid blocking)."""
    return await asyncio.to_thread(hash_password, plain)


def verify_password(plain: str, hashed: str) -> bool:
    """Return True if plain password matches the bcrypt hash."""
    return bcrypt.checkpw(plain.encode(), hashed.encode())


def create_access_token(
    data: dict,
    expire_delta: timedelta | None = None,
) -> str:
    """Encode a JWT access token with optional custom expiration."""
    to_encode = data.copy()
    if expire_delta is not None:
        expire = datetime.now(timezone.utc) + expire_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode["exp"] = int(expire.timestamp())
    return jwt.encode(
        to_encode,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_token(token: str) -> dict:
    """Decode and validate JWT; raise HTTPException 401 on invalid or expired token."""
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from None


def create_refresh_token() -> str:
    """Generate a cryptographically secure random refresh token (URL-safe, ≥32 chars)."""
    return secrets.token_urlsafe(32)


def hash_refresh_token(token: str) -> str:
    """Return SHA-256 hex digest of the token for storage."""
    return hashlib.sha256(bytearray(token, "utf-8")).hexdigest()
