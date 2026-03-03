"""Pytest fixtures for the backend test suite.

Session-scope:
  engine          — shared AsyncEngine for the whole test run
  apply_migrations — creates all tables before tests, drops them after

Function-scope (per test):
  db     — AsyncSession inside an uncommitted transaction; rolls back after test
  client — httpx.AsyncClient wired to the FastAPI app with get_db overridden
"""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine

import app.core.models  # noqa: F401 — registers all ORM models with Base.metadata
from app.core.config import settings
from app.core.database import Base, get_db
from app.main import app


@pytest.fixture(scope="session")
def engine() -> AsyncEngine:
    return create_async_engine(settings.DATABASE_URL, echo=False)


@pytest.fixture(scope="session", autouse=True)
async def apply_migrations(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db(engine: AsyncEngine) -> AsyncGenerator[AsyncSession, None]:
    async with engine.connect() as conn:
        await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)
        try:
            yield session
        finally:
            await session.close()
            await conn.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
