"""LoggingMiddleware — structured access log per HTTP request.

Logs: method, path template, status, duration_ms, request_id.
Skips noisy paths (`/healthz`, `/readyz`, `/metrics`, `/version`).

Body is NEVER logged (privacy / PII safety).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from hwhkit.observability.logging import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

_SKIP_PATHS = frozenset({"/healthz", "/readyz", "/metrics", "/version"})

_logger = get_logger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Emit one structured log record per request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code: int = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            _logger.info(
                "http_request",
                method=request.method,
                path=_route_template(request),
                status=status_code,
                duration_ms=round(duration_ms, 3),
            )


def _route_template(request: Request) -> str:
    """Return the route template (``/users/{id}``) rather than the literal path."""
    route = request.scope.get("route")
    return getattr(route, "path", request.url.path) if route else request.url.path


__all__ = ["LoggingMiddleware"]
