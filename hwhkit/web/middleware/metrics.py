"""MetricsMiddleware — OTel histogram of HTTP request duration.

Records ``http.server.request.duration`` with labels:
- ``http.method``        (GET/POST/...)
- ``http.route``         (parameterized path, e.g. ``/users/{id}``)
- ``http.response.status_code``

Skips noisy paths (`/healthz`, `/readyz`, `/metrics`, `/version`).
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING

from starlette.middleware.base import BaseHTTPMiddleware

from hwhkit.observability.metrics import standard_metrics

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

_SKIP_PATHS = frozenset({"/healthz", "/readyz", "/metrics", "/version"})


class MetricsMiddleware(BaseHTTPMiddleware):
    """Emit OTel histogram for each request."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        if request.url.path in _SKIP_PATHS:
            return await call_next(request)

        start = time.perf_counter()
        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        finally:
            duration_ms = (time.perf_counter() - start) * 1000.0
            route = request.scope.get("route")
            route_path = getattr(route, "path", request.url.path) if route else request.url.path
            standard_metrics().http_request_duration.record(
                duration_ms,
                {
                    "http.method": request.method,
                    "http.route": route_path,
                    "http.response.status_code": status_code,
                },
            )


__all__ = ["MetricsMiddleware"]
