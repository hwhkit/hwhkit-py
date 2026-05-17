"""Framework-supplied system endpoints.

- ``GET /healthz``    — liveness. Always 200 if the process is up.
- ``GET /readyz``     — readiness. Aggregates all registered integration
                        health_check() calls; 503 if any unhealthy.
- ``GET /version``    — service identity (name / version / environment).
- ``GET /metrics``    — Prometheus-compat scrape, only when
                        ``observability.prometheus_compat_enabled``.

Per spec § 2.3 step 6.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Response, status
from fastapi.responses import JSONResponse

from hwhkit.core.health import HealthAggregator

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext


def make_system_router(ctx: AppContext) -> APIRouter:
    """Build the system endpoints router bound to a specific AppContext."""
    router = APIRouter(tags=["system"])

    @router.get("/healthz")
    async def healthz() -> dict[str, bool]:
        """Liveness — always 200 if the process is up."""
        return {"ok": True}

    @router.get("/readyz")
    async def readyz() -> Response:
        """Readiness — aggregates all integration health checks."""
        agg = HealthAggregator()
        for name, integ in ctx.integrations.items():
            agg.add(name, integ.health_check)
        status_obj = await agg.aggregate()
        code = status.HTTP_200_OK if status_obj.healthy else status.HTTP_503_SERVICE_UNAVAILABLE
        body: dict[str, object] = {
            "healthy": status_obj.healthy,
            "message": status_obj.message,
            **status_obj.details,
        }
        return JSONResponse(status_code=code, content=body)

    @router.get("/version")
    async def version() -> dict[str, str]:
        """Service identity."""
        return {
            "name": ctx.config.app.name,
            "version": ctx.config.app.version,
            "environment": ctx.config.app.environment,
        }

    if ctx.config.observability.prometheus_compat_enabled:
        # Only register /metrics when explicitly enabled.
        @router.get("/metrics", response_class=Response)
        async def metrics() -> Response:
            """Prometheus-compat scrape endpoint."""
            try:
                from prometheus_client import (  # type: ignore[import-not-found]
                    CONTENT_TYPE_LATEST,
                    generate_latest,
                )
            except ImportError:
                return Response(
                    content=b"prometheus_client not installed",
                    status_code=503,
                    media_type="text/plain",
                )
            return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)

    return router


__all__ = ["make_system_router"]
