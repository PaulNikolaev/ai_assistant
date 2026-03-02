"""Middleware that ensures every request carries a trace ID.

Reads X-Trace-ID from the incoming request or generates a new UUID4.
Binds the value to structlog's context-local storage so it appears in
every log record emitted during that request, then echoes it back in
the response header.
"""

import uuid

import structlog
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = structlog.get_logger(__name__)

TRACE_ID_HEADER = "X-Trace-ID"


class TraceIDMiddleware(BaseHTTPMiddleware):
    """Attach a trace ID to every request/response cycle."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        trace_id = request.headers.get(TRACE_ID_HEADER) or str(uuid.uuid4())

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(trace_id=trace_id)

        response: Response = await call_next(request)
        response.headers[TRACE_ID_HEADER] = trace_id
        return response
