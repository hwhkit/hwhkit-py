"""Tests for hwhkit.web.middleware.request_id."""

from __future__ import annotations

import uuid

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from hwhkit.web.middleware.request_id import REQUEST_ID_HEADER, RequestIDMiddleware


def _app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestIDMiddleware)

    @app.get("/echo")
    def echo(request: Request) -> dict:
        return {"request_id": request.state.request_id}

    return app


def test_generates_request_id_when_absent() -> None:
    client = TestClient(_app())
    r = client.get("/echo")
    assert r.status_code == 200
    body_id = r.json()["request_id"]
    header_id = r.headers[REQUEST_ID_HEADER]
    assert body_id == header_id
    assert len(body_id) >= 16  # uuid4 hex is 32; allow some leniency


def test_propagates_request_id_from_header() -> None:
    client = TestClient(_app())
    incoming = uuid.uuid4().hex
    r = client.get("/echo", headers={REQUEST_ID_HEADER: incoming})
    assert r.headers[REQUEST_ID_HEADER] == incoming
    assert r.json()["request_id"] == incoming


def test_each_request_unique_id() -> None:
    client = TestClient(_app())
    r1 = client.get("/echo")
    r2 = client.get("/echo")
    assert r1.headers[REQUEST_ID_HEADER] != r2.headers[REQUEST_ID_HEADER]
