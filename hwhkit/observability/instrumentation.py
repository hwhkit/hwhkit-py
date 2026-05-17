"""Auto-instrumentation entry point.

Each call to ``auto_instrument`` is a no-op if the corresponding instrumentation
extras are not installed. Lets users selectively install OTel auto-instrumentation
packages without forcing them all.

See spec § 4.4.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI


# Paths to exclude from instrumentation (avoid noise from internal endpoints).
EXCLUDED_URLS = "/healthz,/readyz,/metrics,/version"


def auto_instrument_fastapi(app: FastAPI) -> bool:
    """Attempt to instrument a FastAPI app. Returns True on success.

    Excludes ``/healthz``, ``/readyz``, ``/metrics``, ``/version`` to avoid
    flooding traces.
    """
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    except ImportError:
        return False
    FastAPIInstrumentor.instrument_app(app, excluded_urls=EXCLUDED_URLS)
    return True


def auto_instrument_httpx() -> bool:
    """Instrument outbound httpx calls. No-op if package missing."""
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    except ImportError:
        return False
    HTTPXClientInstrumentor().instrument()
    return True


def auto_instrument_sqlalchemy(engine: Any) -> bool:
    try:
        from opentelemetry.instrumentation.sqlalchemy import (
            SQLAlchemyInstrumentor,
        )
    except ImportError:
        return False
    SQLAlchemyInstrumentor().instrument(engine=engine)
    return True


def auto_instrument_asyncpg() -> bool:
    try:
        from opentelemetry.instrumentation.asyncpg import AsyncPGInstrumentor
    except ImportError:
        return False
    AsyncPGInstrumentor().instrument()  # type: ignore[no-untyped-call]
    return True


def auto_instrument_redis() -> bool:
    try:
        from opentelemetry.instrumentation.redis import RedisInstrumentor
    except ImportError:
        return False
    RedisInstrumentor().instrument()
    return True


def auto_instrument_all(app: FastAPI | None = None) -> dict[str, bool]:
    """Best-effort: try every available instrumentation. Returns a result map.

    Safe to call multiple times — each instrumentor is idempotent.
    """
    results: dict[str, bool] = {}
    if app is not None:
        results["fastapi"] = auto_instrument_fastapi(app)
    results["httpx"] = auto_instrument_httpx()
    results["asyncpg"] = auto_instrument_asyncpg()
    results["redis"] = auto_instrument_redis()
    return results


__all__ = [
    "EXCLUDED_URLS",
    "auto_instrument_all",
    "auto_instrument_asyncpg",
    "auto_instrument_fastapi",
    "auto_instrument_httpx",
    "auto_instrument_redis",
    "auto_instrument_sqlalchemy",
]
