"""Detailed exception-handler coverage — RequestValidationError + HTTPException paths."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from hwhkit.web.exceptions import (
    _derive_code_from_status,
    register_exception_handlers,
)
from pydantic import BaseModel


class _Body(BaseModel):
    name: str
    age: int


def _app() -> FastAPI:
    app = FastAPI()
    register_exception_handlers(app)

    @app.post("/validate")
    async def validate(body: _Body) -> dict:
        return {"ok": True, "name": body.name}

    @app.get("/forbid")
    async def forbid() -> None:
        raise HTTPException(status_code=403, detail="no entry")

    @app.get("/teapot")
    async def teapot() -> None:
        raise HTTPException(status_code=418, detail="I'm a teapot")

    return app


def test_validation_error_returns_422_envelope() -> None:
    client = TestClient(_app())
    r = client.post("/validate", json={"name": "x"})  # age missing
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == 100422
    assert body["message"] == "validation failed"
    assert "errors" in body["data"]


def test_validation_error_invalid_type() -> None:
    client = TestClient(_app())
    r = client.post("/validate", json={"name": "x", "age": "not-int"})
    assert r.status_code == 422
    body = r.json()
    assert body["code"] == 100422


def test_http_exception_403() -> None:
    client = TestClient(_app())
    r = client.get("/forbid")
    assert r.status_code == 403
    body = r.json()
    assert body["code"] == 100403  # derived from status
    assert body["message"] == "no entry"


def test_http_exception_unusual_status() -> None:
    client = TestClient(_app())
    r = client.get("/teapot")
    assert r.status_code == 418
    body = r.json()
    assert body["code"] == 100418  # 4xx → 100000 + status
    assert "teapot" in body["message"]


def test_derive_code_from_status_4xx() -> None:
    assert _derive_code_from_status(404) == 100404
    assert _derive_code_from_status(401) == 100401
    assert _derive_code_from_status(429) == 100429


def test_derive_code_from_status_5xx() -> None:
    assert _derive_code_from_status(500) == 500000
    assert _derive_code_from_status(502) == 502000
    assert _derive_code_from_status(503) == 503000


def test_derive_code_from_status_unknown() -> None:
    """Out-of-range status defaults to 500000."""
    assert _derive_code_from_status(200) == 500000
    assert _derive_code_from_status(700) == 500000
