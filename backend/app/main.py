"""FastAPI application factory.

Configures middleware, exception handlers, and mounts the API router.
Logging is initialised first so that all subsequent startup messages
are captured in the configured format.
"""

import time
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest  # pyright: ignore[reportMissingImports]
from pydantic import BaseModel
from starlette.middleware.base import RequestResponseEndpoint
from structlog.contextvars import get_contextvars

from app.api.middleware.trace_id import TraceIDMiddleware
from app.core.config import settings
from app.core.logging import configure_logging

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging(settings.APP_ENV)
    logger.info("application startup", env=settings.APP_ENV)
    yield
    logger.info("application shutdown")


app = FastAPI(title="AI Assistant", lifespan=lifespan)

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
        status_code=500,
        content={
            "detail": "Internal server error",
            "code": "internal_error",
            "trace_id": trace_id,
        },
    )


# ── Routes ────────────────────────────────────────────────────────────────


class HealthResponse(BaseModel):
    """Response schema for the liveness probe endpoint."""

    status: str


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@app.get("/metrics")
async def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
