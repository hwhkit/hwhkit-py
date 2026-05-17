"""Tests for hwhkit.web.middleware.auth.AuthMiddleware."""

from __future__ import annotations

import json
import time
from typing import Any
from unittest.mock import AsyncMock

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI
from fastapi.testclient import TestClient
from hwhkit.core.jwt import JwksCache, JwtVerifier
from hwhkit.web.middleware.auth import AuthMiddleware, public_endpoint
from jwt.algorithms import RSAAlgorithm


def _make_jwks() -> tuple[Any, dict[str, Any]]:
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(priv.public_key()))
    jwk["kid"] = "test-kid"
    jwk["use"] = "sig"
    return priv, {"keys": [jwk]}


@pytest.fixture
def verifier() -> tuple[JwtVerifier, Any]:
    priv, jwks = _make_jwks()
    v = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://issuer",
        audience="api",
    )
    return v, priv


def _app(verifier: JwtVerifier) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        AuthMiddleware,
        verifier=verifier,
        exclude_paths=["/public-data"],
        exclude_prefixes=["/public-tree/"],
    )

    @app.get("/private")
    def private() -> dict:
        return {"ok": True}

    @app.get("/healthz")
    def healthz() -> dict:
        return {"ok": True}

    @app.get("/public-data")
    @public_endpoint
    def public_data() -> dict:
        return {"ok": True}

    @app.get("/public-tree/anything")
    def public_tree() -> dict:
        return {"ok": True}

    return app


def test_no_token_returns_401(verifier: tuple[JwtVerifier, Any]) -> None:
    client = TestClient(_app(verifier[0]))
    r = client.get("/private")
    assert r.status_code == 401
    body = r.json()
    assert body["code"] == 100401


def test_bad_token_returns_401(verifier: tuple[JwtVerifier, Any]) -> None:
    client = TestClient(_app(verifier[0]))
    r = client.get("/private", headers={"Authorization": "Bearer garbage"})
    assert r.status_code == 401


def test_valid_token_passes(verifier: tuple[JwtVerifier, Any]) -> None:
    v, priv = verifier
    token = pyjwt.encode(
        {
            "iss": "https://issuer",
            "aud": "api",
            "sub": "u-1",
            "exp": int(time.time()) + 60,
        },
        priv,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    client = TestClient(_app(v))
    r = client.get("/private", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200


def test_healthz_always_public(verifier: tuple[JwtVerifier, Any]) -> None:
    client = TestClient(_app(verifier[0]))
    r = client.get("/healthz")
    assert r.status_code == 200


def test_exclude_paths_skips_auth(verifier: tuple[JwtVerifier, Any]) -> None:
    client = TestClient(_app(verifier[0]))
    r = client.get("/public-data")
    assert r.status_code == 200


def test_exclude_prefixes_skips_auth(verifier: tuple[JwtVerifier, Any]) -> None:
    client = TestClient(_app(verifier[0]))
    r = client.get("/public-tree/anything")
    assert r.status_code == 200
