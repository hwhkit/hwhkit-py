"""Tests for hwhkit.core.jwt — JWKS cache + Claims extractor."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any
from unittest.mock import AsyncMock

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa
from hwhkit.core.jwt import JwksCache, JwtVerifier, JwtVerifyError
from jwt.algorithms import RSAAlgorithm


def _make_rsa_keypair() -> tuple[Any, dict[str, Any]]:
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    jwk = json.loads(RSAAlgorithm.to_jwk(priv.public_key()))
    jwk["kid"] = "test-kid"
    jwk["use"] = "sig"
    return priv, {"keys": [jwk]}


@pytest.mark.asyncio
async def test_verify_valid_token() -> None:
    priv, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://issuer",
        audience="api",
    )
    token = pyjwt.encode(
        {
            "iss": "https://issuer",
            "aud": "api",
            "sub": "user-1",
            "exp": int(time.time()) + 60,
        },
        priv,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    claims = await verifier.verify(token)
    assert claims["sub"] == "user-1"


@pytest.mark.asyncio
async def test_jwks_cache_hits() -> None:
    _, jwks = _make_rsa_keypair()
    fetcher = AsyncMock(return_value=jwks)
    cache = JwksCache(fetch=fetcher, ttl=300.0)
    await cache.get()
    await cache.get()
    fetcher.assert_awaited_once()


@pytest.mark.asyncio
async def test_jwks_cache_refresh_after_ttl() -> None:
    _, jwks = _make_rsa_keypair()
    fetcher = AsyncMock(return_value=jwks)
    cache = JwksCache(fetch=fetcher, ttl=0.01)
    await cache.get()
    await asyncio.sleep(0.02)
    await cache.get()
    assert fetcher.await_count == 2


@pytest.mark.asyncio
async def test_reject_expired_token() -> None:
    priv, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://issuer",
        audience="api",
    )
    token = pyjwt.encode(
        {
            "iss": "https://issuer",
            "aud": "api",
            "sub": "u",
            "exp": int(time.time()) - 60,
        },
        priv,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    with pytest.raises(JwtVerifyError):
        await verifier.verify(token)


@pytest.mark.asyncio
async def test_reject_alg_none() -> None:
    _, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://issuer",
        audience="api",
    )
    bad = pyjwt.encode({"sub": "x"}, key="", algorithm="none")  # type: ignore[arg-type]
    with pytest.raises(JwtVerifyError):
        await verifier.verify(bad)


@pytest.mark.asyncio
async def test_reject_wrong_issuer() -> None:
    priv, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://expected",
        audience="api",
    )
    token = pyjwt.encode(
        {
            "iss": "https://OTHER",
            "aud": "api",
            "sub": "u",
            "exp": int(time.time()) + 60,
        },
        priv,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    with pytest.raises(JwtVerifyError):
        await verifier.verify(token)
