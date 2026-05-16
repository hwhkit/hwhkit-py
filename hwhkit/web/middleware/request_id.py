"""RequestIDMiddleware — ensures every request has X-Request-ID for correlation.

Reads ``X-Request-ID`` from incoming header; if absent, generates a UUID4.
Sets it on:
- ``request.state.request_id`` (for downstream handlers/middleware).
- ``X-Request-ID`` response header (so clients can correlate).
- structlog ``contextvars`` so all log records in this request have it.

Per spec § 3.4 — must be outermost in the custom middleware stack.
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

import structlog
from starlette.middleware.base import BaseHTTPMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Generate or propagate per-request correlation IDs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        request.state.request_id = request_id

        # Bind to structlog context so all log lines inherit it
        structlog.contextvars.bind_contextvars(request_id=request_id)
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.unbind_contextvars("request_id")
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


__all__ = ["REQUEST_ID_HEADER", "RequestIDMiddleware"]
