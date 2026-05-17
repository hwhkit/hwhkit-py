"""E2E smoke tests against tests/e2e/sample_app/main.py.

These boot the framework via ``bootstrap()`` and exercise the HTTP surface
via ``TestClient`` (no real server process).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.e2e


@pytest.fixture
def client() -> TestClient:
    from tests.e2e.sample_app.main import make_app

    return TestClient(make_app())  # type: ignore[arg-type]


class TestSystemEndpoints:
    def test_healthz(self, client: TestClient) -> None:
        r = client.get("/healthz")
        assert r.status_code == 200
        assert r.json() == {"ok": True}

    def test_readyz_no_integrations(self, client: TestClient) -> None:
        r = client.get("/readyz")
        assert r.status_code == 200
        body = r.json()
        assert body["healthy"] is True
        assert body["checks"] == {}

    def test_version(self, client: TestClient) -> None:
        r = client.get("/version")
        assert r.status_code == 200
        body = r.json()
        assert body["name"] == "sample"
        assert body["version"] == "0.0.1"
        assert body["environment"] == "dev"


class TestBusinessRoutes:
    def test_create_then_get(self, client: TestClient) -> None:
        # POST creates
        r = client.post("/items", json={"name": "widget"})
        assert r.status_code == 201
        body = r.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "widget"
        new_id = body["data"]["id"]
        assert isinstance(new_id, int)

        # GET retrieves
        r = client.get(f"/items/{new_id}")
        assert r.status_code == 200
        body = r.json()
        assert body["code"] == 0
        assert body["data"]["name"] == "widget"

    def test_get_missing_returns_404_envelope(self, client: TestClient) -> None:
        r = client.get("/items/999")
        assert r.status_code == 404
        body = r.json()
        assert body["code"] == 100404
        assert "999" in body["message"]


class TestEnvelopeProperties:
    def test_success_envelope_shape(self, client: TestClient) -> None:
        client.post("/items", json={"name": "x"})
        r = client.get("/items/1")
        body = r.json()
        # Required envelope fields present
        assert {"code", "message", "data", "trace_id"} <= set(body.keys())
        assert body["code"] == 0
        assert body["message"] == "ok"

    def test_error_envelope_shape(self, client: TestClient) -> None:
        r = client.get("/items/999")
        body = r.json()
        assert {"code", "message", "data", "trace_id"} <= set(body.keys())


class TestExceptionHandling:
    def test_unhandled_exception_500_no_traceback_leak(self, client: TestClient) -> None:
        # Need raise_server_exceptions=False so TestClient doesn't re-raise
        from tests.e2e.sample_app.main import make_app

        c = TestClient(make_app(), raise_server_exceptions=False)  # type: ignore[arg-type]
        r = c.get("/boom")
        assert r.status_code == 500
        body = r.json()
        assert body["code"] == 500000
        # Critical: traceback / exception message must NOT leak
        assert "internal-secret-detail" not in body["message"]
        assert "RuntimeError" not in body["message"]
