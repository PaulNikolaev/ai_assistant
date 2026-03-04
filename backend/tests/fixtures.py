"""Shared pytest fixtures for DB-backed tests (API and integration).

Import these into conftest.py files that need database access:

    from tests.fixtures import engine, apply_migrations, db, client

Root cause of the old fixture design issue:
    `await conn.begin()` + `AsyncSession(bind=conn)` caused asyncpg to see
    two transaction starts on the same connection, raising:
    "cannot perform operation: another operation is in progress"

Fix: use AsyncSession(engine) directly with NullPool so each test gets a
fresh connection and SQLAlchemy manages the transaction lifecycle internally.
"""

from collections.abc import AsyncGenerator
from typing import Any, cast

import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy.pool import NullPool
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

import app.core.models  # noqa: F401 — registers all ORM models with Base.metadata
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app as _app

fastapi_app: FastAPI = cast(FastAPI, _app)


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    """Session-scoped engine with NullPool — each connect() gets a fresh connection."""
    return create_async_engine(settings.DATABASE_URL, echo=False, poolclass=NullPool)


@pytest_asyncio.fixture(scope="session")
async def apply_migrations(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Create all tables before the session; drop them after."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(apply_migrations: None, engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    """Per-test AsyncSession; uncommitted changes are rolled back after the test."""
    async with AsyncSession(engine, expire_on_commit=False) as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """httpx AsyncClient wired to the FastAPI app with get_db overridden."""
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    cast(Any, fastapi_app).dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as ac:
        yield ac
    cast(Any, fastapi_app).dependency_overrides.clear()
