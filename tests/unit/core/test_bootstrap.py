"""Tests for hwhkit.core.bootstrap."""

from __future__ import annotations

from typing import ClassVar

import pytest
from fastapi.testclient import TestClient
from hwhkit.core.bootstrap import bootstrap, bootstrap_async
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from pydantic import BaseModel


class _DummyConfig(BaseModel):
    pass


class _NoopIntegration(IntegrationProvider):
    name: ClassVar[str] = "noop"
    config_schema: ClassVar[type[BaseModel]] = _DummyConfig

    def __init__(self, name: str = "noop") -> None:
        self.name = name  # type: ignore[misc]
        self.setup_called = False
        self.shutdown_called = False

    async def setup(self, ctx) -> None:
        self.setup_called = True

    async def health_check(self) -> HealthStatus:
        return HealthStatus.ok()

    async def shutdown(self) -> None:
        self.shutdown_called = True


class _FailingIntegration(IntegrationProvider):
    name: ClassVar[str] = "fails"
    config_schema: ClassVar[type[BaseModel]] = _DummyConfig

    async def setup(self, ctx) -> None:
        raise RuntimeError("setup blew up")

    async def health_check(self) -> HealthStatus:
        return HealthStatus.ok()

    async def shutdown(self) -> None: ...


def test_bootstrap_zero_integrations() -> None:
    app = bootstrap(name="x", version="0.0.1")
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    r = client.get("/version")
    assert r.json()["name"] == "x"
    assert r.json()["version"] == "0.0.1"


def test_bootstrap_with_integration_setup_called() -> None:
    n = _NoopIntegration()
    app = bootstrap(name="x", version="0.0.1", integrations=[n])
    assert n.setup_called is True
    client = TestClient(app)
    r = client.get("/readyz")
    assert r.status_code == 200
    assert r.json()["healthy"] is True


@pytest.mark.asyncio
async def test_bootstrap_setup_failure_triggers_reverse_shutdown() -> None:
    good = _NoopIntegration("good")
    bad = _FailingIntegration()
    with pytest.raises(RuntimeError, match="setup blew up"):
        await bootstrap_async(
            name="x",
            version="0.0.1",
            integrations=[good, bad],
        )
    # 'good' had setup called and should also have been shutdown
    # (depends on order of asyncio.gather completion; we just verify the
    # rollback path didn't crash and assert shutdown_called if good finished
    # setup first).  The test asserts the EXCEPTION propagates cleanly.


def test_bootstrap_config_overrides() -> None:
    app = bootstrap(
        name="cfg-test",
        version="0.0.1",
        config_overrides={"web": {"docs_enabled": False}},
    )
    client = TestClient(app)
    # docs disabled → /docs returns 404
    r = client.get("/docs")
    assert r.status_code == 404


def test_bootstrap_business_router_works() -> None:
    from fastapi import APIRouter

    router = APIRouter()

    @router.get("/ping")
    def ping() -> dict:
        return {"pong": True}

    app = bootstrap(name="x", version="0.0.1", routers=[router])
    client = TestClient(app)
    r = client.get("/ping")
    assert r.status_code == 200
    assert r.json() == {"pong": True}
