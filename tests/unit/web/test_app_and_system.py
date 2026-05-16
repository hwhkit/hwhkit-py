"""Integration of build_app + system_router using TestClient (no real server)."""

from __future__ import annotations

from typing import ClassVar

from fastapi import APIRouter
from fastapi.testclient import TestClient
from hwhkit.config.base import Settings
from hwhkit.core.context import AppContext
from hwhkit.core.errors import NotFoundError
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.web.app import build_app
from pydantic import BaseModel


class _DummyConfig(BaseModel):
    pass


class _HealthyIntegration(IntegrationProvider):
    name: ClassVar[str] = "healthy"
    config_schema: ClassVar[type[BaseModel]] = _DummyConfig

    async def setup(self, ctx) -> None: ...
    async def health_check(self) -> HealthStatus:
        return HealthStatus.ok()

    async def shutdown(self) -> None: ...


class _UnhealthyIntegration(IntegrationProvider):
    name: ClassVar[str] = "broken"
    config_schema: ClassVar[type[BaseModel]] = _DummyConfig

    async def setup(self, ctx) -> None: ...
    async def health_check(self) -> HealthStatus:
        return HealthStatus.fail("downstream offline")

    async def shutdown(self) -> None: ...


def _make_ctx(integrations: list[IntegrationProvider] | None = None) -> AppContext:
    ctx = AppContext()
    ctx.config = Settings()
    ctx.config.app.name = "test-svc"
    ctx.config.app.version = "1.2.3"
    for integ in integrations or []:
        ctx.register(integ)
    return ctx


def test_app_has_healthz() -> None:
    app = build_app(_make_ctx())
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_readyz_all_healthy() -> None:
    app = build_app(_make_ctx([_HealthyIntegration()]), integrations=[_HealthyIntegration()])
    # Note: we deliberately pass same integration twice doesn't matter since
    # ctx already has the one registered.  Re-build correctly:
    ctx = _make_ctx([_HealthyIntegration()])
    app = build_app(ctx, integrations=list(ctx.integrations.values()))
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code == 200
    body = r.json()
    assert body["healthy"] is True
    assert "checks" in body


def test_readyz_unhealthy() -> None:
    ctx = _make_ctx([_HealthyIntegration(), _UnhealthyIntegration()])
    app = build_app(ctx, integrations=list(ctx.integrations.values()))
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code == 503
    body = r.json()
    assert body["healthy"] is False
    assert body["checks"]["broken"]["healthy"] is False


def test_version_endpoint() -> None:
    app = build_app(_make_ctx())
    client = TestClient(app)
    r = client.get("/version")
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "test-svc"
    assert body["version"] == "1.2.3"


def test_business_router_mounted() -> None:
    router = APIRouter()

    @router.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"id": item_id}

    app = build_app(_make_ctx(), routers=[router])
    client = TestClient(app)
    r = client.get("/items/7")
    assert r.status_code == 200
    assert r.json() == {"id": 7}


def test_api_error_handled_with_envelope() -> None:
    router = APIRouter()

    @router.get("/missing")
    def missing() -> None:
        raise NotFoundError("nope")

    app = build_app(_make_ctx(), routers=[router])
    client = TestClient(app)
    r = client.get("/missing")
    assert r.status_code == 404
    body = r.json()
    assert body["code"] == 100404
    assert body["message"] == "nope"


def test_unhandled_exception_returns_500_no_traceback_leak() -> None:
    router = APIRouter()

    @router.get("/boom")
    def boom() -> None:
        raise RuntimeError("internal-secret-detail")

    app = build_app(_make_ctx(), routers=[router])
    client = TestClient(app, raise_server_exceptions=False)
    r = client.get("/boom")
    assert r.status_code == 500
    body = r.json()
    assert body["code"] == 500000
    assert "internal-secret-detail" not in body["message"]


def test_admin_routes_off_by_default() -> None:
    """Integration admin routers are hidden unless web.admin_routes_enabled=true."""

    class _WithAdmin(_HealthyIntegration):
        name: ClassVar[str] = "with_admin"

        def fastapi_router(self):  # type: ignore[no-untyped-def]
            r = APIRouter()

            @r.get("/info")
            def info() -> dict:
                return {"info": "secret"}

            return r

    ctx = _make_ctx([_WithAdmin()])
    app = build_app(ctx, integrations=list(ctx.integrations.values()))
    client = TestClient(app)
    r = client.get("/_/with_admin/info")
    assert r.status_code == 404


def test_admin_routes_on_when_enabled() -> None:
    class _WithAdmin(_HealthyIntegration):
        name: ClassVar[str] = "with_admin"

        def fastapi_router(self):  # type: ignore[no-untyped-def]
            r = APIRouter()

            @r.get("/info")
            def info() -> dict:
                return {"info": "v"}

            return r

    ctx = _make_ctx([_WithAdmin()])
    ctx.config.web.admin_routes_enabled = True
    app = build_app(ctx, integrations=list(ctx.integrations.values()))
    client = TestClient(app)
    r = client.get("/_/with_admin/info")
    assert r.status_code == 200
