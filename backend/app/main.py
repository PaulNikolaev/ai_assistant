"""FastAPI application factory.

Configures middleware, exception handlers, and mounts the API router.
Logging is initialised first so that all subsequent startup messages
are captured in the configured format.
"""

import asyncio
import time
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

import structlog
from alembic import command as alembic_command
from alembic.config import Config as AlembicConfig
from alembic.script import ScriptDirectory
from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # pyright: ignore[reportMissingImports]
from pydantic import BaseModel
from sqlalchemy import text
from starlette.middleware.base import RequestResponseEndpoint
from structlog.contextvars import get_contextvars

from app.api.middleware.trace_id import TraceIDMiddleware
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.logging import configure_logging
from app.core.qdrant import check_qdrant, close_qdrant, init_qdrant
from app.core.redis import close_redis_pool, create_redis_pool, get_redis_client
from app.core.seed import seed_superadmin
from app.core.storage import get_storage, init_storage

configure_logging(settings.APP_ENV)

logger = structlog.get_logger(__name__)

ServiceStatus = Literal["ok", "degraded"]

_ALEMBIC_INI: Path = Path(__file__).parent.parent / "alembic.ini"


def _run_alembic_upgrade() -> None:
    """Run ``alembic upgrade head`` synchronously (safe to call in a thread)."""
    cfg = AlembicConfig(str(_ALEMBIC_INI))
    alembic_command.upgrade(cfg, "head")


async def _check_migrations_current() -> bool:
    """Return True when the database revision matches the alembic head."""
    cfg = AlembicConfig(str(_ALEMBIC_INI))
    script = ScriptDirectory.from_config(cfg)
    heads: set[str] = set(script.get_heads())

    async with AsyncSessionLocal() as session:
        # noinspection SqlNoDataSourceInspection
        result = await session.execute(
            text("SELECT version_num FROM alembic_version")
        )
        current: set[str] = {row[0] for row in result}

    return current == heads


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    if settings.APP_ENV == "development":
        await asyncio.to_thread(_run_alembic_upgrade)
        logger.info("alembic migrations applied")
        async with AsyncSessionLocal() as db:
            await seed_superadmin(db)
    elif settings.APP_ENV == "production":
        try:
            is_current = await _check_migrations_current()
            if not is_current:
                logger.warning("Pending migrations detected, apply manually!")
        except Exception as exc:
            logger.warning("could not check migration status", exc_info=exc)

    await create_redis_pool()
    init_qdrant()
    init_storage()
    logger.info("application startup", env=settings.APP_ENV)
    yield
    logger.info("application shutdown")
    await close_redis_pool()
    await close_qdrant()


app = FastAPI(
    title="AI Assistant",
    lifespan=lifespan,
    root_path=settings.ROOT_PATH,
)

# ── Middleware ────────────────────────────────────────────────────────────
# Execution order: log_requests → TraceIDMiddleware → CORSMiddleware → route.
# log_requests logs after call_next, so trace_id is already bound by TraceIDMiddleware.

# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# noinspection PyTypeChecker
app.add_middleware(TraceIDMiddleware)


# ── Request logging ───────────────────────────────────────────────────────


@app.middleware("http")
async def log_requests(request: Request, call_next: RequestResponseEndpoint) -> Response:
    start = time.perf_counter()
    response: Response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 1)
    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


# ── Exception handlers ────────────────────────────────────────────────────


@app.exception_handler(RequestValidationError)
async def validation_error_handler(
    _request: Request, exc: RequestValidationError
) -> JSONResponse:
    trace_id = get_contextvars().get("trace_id")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": exc.errors(),
            "code": "validation_error",
            "trace_id": trace_id,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    _request: Request, exc: HTTPException
) -> JSONResponse:
    trace_id = get_contextvars().get("trace_id")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "http_error",
            "status": exc.status_code,
            "trace_id": trace_id,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(
    _request: Request, exc: Exception
) -> JSONResponse:
    trace_id = get_contextvars().get("trace_id")
    logger.exception("unhandled error", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "internal_error",
            "trace_id": trace_id,
        },
    )


# ── Health check helpers ──────────────────────────────────────────────────


async def _check_postgres() -> ServiceStatus:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return "ok"
    except Exception as exc:
        logger.warning("postgres health check failed", exc_info=exc)
        return "degraded"


async def _check_redis() -> ServiceStatus:
    client = get_redis_client()
    if client is None:
        return "degraded"
    try:
        result = await client.ping()
        return "ok" if result else "degraded"
    except Exception as exc:
        logger.warning("redis health check failed", exc_info=exc)
        return "degraded"


async def _check_qdrant() -> ServiceStatus:
    ok = await check_qdrant()
    return "ok" if ok else "degraded"


async def _check_minio() -> ServiceStatus:
    try:
        ok = await get_storage().check()
        return "ok" if ok else "degraded"
    except RuntimeError:
        # Storage not initialised (lifespan not yet run or test env) — degrade silently.
        return "degraded"
    except Exception as exc:
        logger.warning("minio health check failed", exc_info=exc)
        return "degraded"


async def _check_worker() -> ServiceStatus:
    client = get_redis_client()
    if client is None:
        return "degraded"
    try:
        val = await client.get("worker:heartbeat")
        return "ok" if val is not None else "degraded"
    except Exception as exc:
        logger.warning("worker health check failed", exc_info=exc)
        return "degraded"


# ── Routes ────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Response schema for the /health endpoint with per-service statuses."""

    status: ServiceStatus
    postgres: ServiceStatus
    redis: ServiceStatus
    qdrant: ServiceStatus
    minio: ServiceStatus
    worker: ServiceStatus


@app.get("/health", response_model=HealthResponse)
async def health(response: Response) -> HealthResponse:
    results = await asyncio.gather(
        _check_postgres(),
        _check_redis(),
        _check_qdrant(),
        _check_minio(),
        _check_worker(),
        return_exceptions=True,
    )

    def _to_status(r: ServiceStatus | BaseException) -> ServiceStatus:
        return "degraded" if isinstance(r, BaseException) else r

    postgres, redis, qdrant, minio, worker = (_to_status(r) for r in results)

    critical_ok = postgres == "ok" and qdrant == "ok"
    if not critical_ok:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return HealthResponse(
        status="ok" if critical_ok else "degraded",
        postgres=postgres,
        redis=redis,
        qdrant=qdrant,
        minio=minio,
        worker=worker,
    )


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
