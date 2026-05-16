"""``bootstrap()`` — single-call framework startup.

Per spec § 2.3 — pipeline (sync front-end + async setup phase):

1. Load config (env → yaml → dotenv → defaults), apply ``config_overrides``.
2. ``setup_otel(config.observability)`` — no-op if disabled.
3. ``configure_logging(...)``.
4. Create ``AppContext`` + register integrations.
5. Run ``integration.setup(ctx)`` concurrently; reverse-shutdown on failure.
6. ``build_app(ctx, routers, integrations, on_startup, on_shutdown)``.
7. Auto-instrument (best-effort, no-op if extras missing).
8. Return FastAPI app.

The caller passes the returned app to an ASGI server (``hwhkit.web.server.run``).
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from typing import TYPE_CHECKING, Any

_logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastapi import APIRouter, FastAPI

    from hwhkit.config.base import Settings
    from hwhkit.core.context import AppContext
    from hwhkit.core.integration import IntegrationProvider

    LifecycleHook = Callable[[AppContext], Awaitable[None]]


async def bootstrap_async(
    *,
    name: str,
    version: str,
    integrations: list[IntegrationProvider] | None = None,
    routers: list[APIRouter] | None = None,
    on_startup: list[LifecycleHook] | None = None,
    on_shutdown: list[LifecycleHook] | None = None,
    config_overrides: dict[str, Any] | None = None,
    settings_cls: type[Settings] | None = None,
) -> FastAPI:
    """Async bootstrap entry point — for embedding inside an existing event loop.

    Most users call ``bootstrap()`` (the sync wrapper), which spins up its own
    loop for the setup phase.
    """
    from hwhkit.config import Settings as DefaultSettings
    from hwhkit.config import load_settings
    from hwhkit.config.schemas import AppConfig
    from hwhkit.core.context import AppContext
    from hwhkit.observability import configure_logging
    from hwhkit.observability.instrumentation import auto_instrument_all
    from hwhkit.observability.otel import setup_otel
    from hwhkit.web.app import build_app

    integrations = integrations or []
    routers = routers or []
    on_startup = on_startup or []
    on_shutdown = on_shutdown or []

    # Step 1: load + force app identity
    settings = load_settings(
        settings_cls or DefaultSettings,
        overrides=config_overrides,
    )
    settings.app = AppConfig(**{**settings.app.model_dump(), "name": name, "version": version})

    # Step 2: OTel SDK
    setup_otel(settings.observability)

    # Step 3: structured logging
    configure_logging(
        level=settings.observability.log.level,
        json_mode=settings.observability.log.json_mode,
        service_name=name,
    )

    # Step 4: AppContext + register integrations
    ctx = AppContext()
    ctx.config = settings
    for integ in integrations:
        ctx.register(integ)

    # Step 5: parallel setup; rollback on any failure
    started: list[IntegrationProvider] = []
    try:
        await asyncio.gather(*(integ.setup(ctx) for integ in integrations))
        started = list(integrations)
    except Exception:
        for integ in reversed(started):
            with contextlib.suppress(Exception):
                await integ.shutdown()
        raise

    # Step 6: build app
    app = build_app(
        ctx,
        routers=routers,
        integrations=integrations,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
    )

    # Step 7: auto-instrument (best-effort)
    if settings.observability.enabled:
        auto_instrument_all(app)

    # Step 8: return
    return app


def bootstrap(
    *,
    name: str,
    version: str,
    integrations: list[IntegrationProvider] | None = None,
    routers: list[APIRouter] | None = None,
    on_startup: list[LifecycleHook] | None = None,
    on_shutdown: list[LifecycleHook] | None = None,
    config_overrides: dict[str, Any] | None = None,
    settings_cls: type[Settings] | None = None,
) -> FastAPI:
    """Synchronous bootstrap — the standard entry point.

    Drives the async setup phase to completion before returning the FastAPI
    app. The app is then passed to an ASGI server.
    """
    return asyncio.run(
        bootstrap_async(
            name=name,
            version=version,
            integrations=integrations,
            routers=routers,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            config_overrides=config_overrides,
            settings_cls=settings_cls,
        )
    )


__all__ = ["bootstrap", "bootstrap_async"]
