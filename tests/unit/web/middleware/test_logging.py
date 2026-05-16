"""Tests for hwhkit.web.middleware.logging."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stdout

import structlog
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hwhkit.observability.logging import configure_logging
from hwhkit.web.middleware.logging import LoggingMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(LoggingMiddleware)

    @app.get("/items/{item_id}")
    def get_item(item_id: int) -> dict:
        return {"id": item_id}

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    return app


def test_logs_one_record_per_request() -> None:
    configure_logging(level="INFO", json_mode=True)
    client = TestClient(_app())
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = client.get("/items/42")
    assert r.status_code == 200

    json_lines = [line for line in buf.getvalue().splitlines() if line.strip().startswith("{")]
    http_records = [json.loads(line) for line in json_lines if "http_request" in line]
    assert len(http_records) == 1
    rec = http_records[0]
    assert rec["method"] == "GET"
    assert rec["status"] == 200
    assert "duration_ms" in rec
    structlog.reset_defaults()


def test_healthz_skipped() -> None:
    configure_logging(level="INFO", json_mode=True)
    client = TestClient(_app())
    buf = io.StringIO()
    with redirect_stdout(buf):
        r = client.get("/healthz")
    assert r.status_code == 200
    http_records = [line for line in buf.getvalue().splitlines() if "http_request" in line]
    assert http_records == []
    structlog.reset_defaults()
