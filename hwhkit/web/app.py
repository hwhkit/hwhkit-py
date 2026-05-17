"""``build_app()`` — FastAPI app factory called by ``bootstrap()``.

Per spec § 3.1 — composes:
1. FastAPI app instance + AppContext on ``app.state.ctx``.
2. Exception handlers (4-tier stack).
3. Middlewares: GZip → CORS → RequestID → Logging → Metrics.
4. Integration-supplied middlewares.
5. System router (/healthz /readyz /version /metrics).
6. Business routers.
7. Integration-supplied admin routers (only if ``web.admin_routes_enabled``).
8. lifespan: drives integrations.setup/shutdown.
"""

from __future__ import annotations

import contextlib
from collections.abc import AsyncIterator, Awaitable, Callable
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from hwhkit.web.exceptions import register_exception_handlers
from hwhkit.web.middleware import LoggingMiddleware, MetricsMiddleware, RequestIDMiddleware
from hwhkit.web.system_router import make_system_router

if TYPE_CHECKING:
    from fastapi import APIRouter

    from hwhkit.core.context import AppContext
    from hwhkit.core.integration import IntegrationProvider

LifecycleHook = Callable[["AppContext"], Awaitable[None]]


def build_app(
    ctx: AppContext,
    *,
    routers: list[APIRouter] | None = None,
    integrations: list[IntegrationProvider] | None = None,
    on_startup: list[LifecycleHook] | None = None,
    on_shutdown: list[LifecycleHook] | None = None,
) -> FastAPI:
    """Construct a fully-wired FastAPI app from an ``AppContext``.

    ``bootstrap()`` is the intended caller; business code should not call this
    directly.
    """
    routers = routers or []
    integrations = integrations or []
    on_startup = on_startup or []
    on_shutdown = on_shutdown or []

    web = ctx.config.web

    @contextlib.asynccontextmanager
    async def _lifespan(_app: FastAPI) -> AsyncIterator[None]:
        # ``integration.setup`` already ran in bootstrap; here we just run
        # user-provided on_startup hooks after the app is loaded, and on_shutdown
        # hooks before integration shutdown.
        for hook in on_startup:
            await hook(ctx)
        try:
            yield
        finally:
            for hook in on_shutdown:
                with contextlib.suppress(Exception):
                    await hook(ctx)

    app = FastAPI(
        title=ctx.config.app.name,
        version=ctx.config.app.version,
        description=ctx.config.app.description,
        docs_url=web.docs_url if web.docs_enabled else None,
        redoc_url=web.redoc_url if web.docs_enabled else None,
        lifespan=_lifespan,
    )
    app.state.ctx = ctx

    # Exception handlers — register before anything else
    register_exception_handlers(app)

    # Middleware stack (outermost-first; FastAPI wraps in reverse-register order)
    app.add_middleware(GZipMiddleware, minimum_size=1024)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=web.cors.allow_origins,
        allow_credentials=web.cors.allow_credentials,
        allow_methods=web.cors.allow_methods,
        allow_headers=web.cors.allow_headers,
        max_age=web.cors.max_age,
    )
    app.add_middleware(RequestIDMiddleware)
    app.add_middleware(LoggingMiddleware)
    app.add_middleware(MetricsMiddleware)

    # Integration-supplied middlewares
    for integ in integrations:
        for mw in integ.fastapi_middlewares():
            app.add_middleware(mw)

    # System router
    app.include_router(make_system_router(ctx))

    # Business routers
    for router in routers:
        app.include_router(router)

    # Integration admin routers (default off)
    if web.admin_routes_enabled:
        for integ in integrations:
            if (r := integ.fastapi_router()) is not None:
                app.include_router(r, prefix=f"/_/{integ.name}", tags=[integ.name])

    return app


__all__ = ["LifecycleHook", "build_app"]
