"""Tests for hwhkit.web.middleware.metrics."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from hwhkit.observability.metrics import reset_standard_metrics
from hwhkit.web.middleware.metrics import MetricsMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(MetricsMiddleware)

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"id": item_id}

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    return app


def test_records_request_duration_metric() -> None:
    """Smoke: middleware runs without error and produces a 2xx response."""
    reset_standard_metrics()
    client = TestClient(_app())
    r = client.get("/items/3")
    assert r.status_code == 200


def test_healthz_skipped_does_not_crash() -> None:
    reset_standard_metrics()
    client = TestClient(_app())
    r = client.get("/healthz")
    assert r.status_code == 200
