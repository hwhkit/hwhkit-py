"""JWT verifier with JWKS caching.

For OAuth2/OIDC providers (Auth0, Cognito, Keycloak, ...) where public keys
are published at /.well-known/jwks.json.

Hardened against common JWT pitfalls: `alg: none`, key confusion,
expired tokens, wrong audience/issuer.
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING, Any

import jwt as pyjwt
from jwt.exceptions import InvalidTokenError

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

# Never include "none". Asymmetric only.
ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]


class JwtVerifyError(Exception):
    """JWT verification failed."""


class JwksCache:
    """TTL-cached JWKS document fetcher."""

    def __init__(
        self,
        fetch: Callable[[], Awaitable[dict[str, Any]]],
        *,
        ttl: float = 3600.0,
    ) -> None:
        self._fetch = fetch
        self._ttl = ttl
        self._cached: dict[str, Any] | None = None
        self._cached_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self) -> dict[str, Any]:
        async with self._lock:
            now = time.monotonic()
            if self._cached and now - self._cached_at < self._ttl:
                return self._cached
            self._cached = await self._fetch()
            self._cached_at = now
            return self._cached


class JwtVerifier:
    """Verify a Bearer token's signature + claims using a JWKS cache."""

    def __init__(
        self,
        *,
        jwks_cache: JwksCache,
        issuer: str,
        audience: str,
        algorithms: list[str] | None = None,
        leeway: int = 30,
    ) -> None:
        self._jwks = jwks_cache
        self._issuer = issuer
        self._audience = audience
        self._algorithms = algorithms or ALLOWED_ALGORITHMS
        self._leeway = leeway

    async def verify(self, token: str) -> dict[str, Any]:
        try:
            header = pyjwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg")
            if alg not in self._algorithms:
                raise JwtVerifyError(f"disallowed algorithm: {alg!r}")
            jwks = await self._jwks.get()
            jwk = self._find_key(jwks, kid)
            if not jwk:
                raise JwtVerifyError(f"no JWKS key matched kid={kid!r}")
            public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(jwk)
            decoded: dict[str, Any] = pyjwt.decode(
                token,
                key=public_key,  # type: ignore[arg-type]
                algorithms=self._algorithms,
                issuer=self._issuer,
                audience=self._audience,
                leeway=self._leeway,
                options={"require": ["exp", "iss", "aud"]},
            )
            return decoded
        except InvalidTokenError as exc:
            raise JwtVerifyError(str(exc)) from exc

    @staticmethod
    def _find_key(jwks: dict[str, Any], kid: str | None) -> dict[str, Any] | None:
        keys: list[dict[str, Any]] = jwks.get("keys", [])
        for key in keys:
            if kid is None or key.get("kid") == kid:
                return key
        return None


__all__ = ["ALLOWED_ALGORITHMS", "JwksCache", "JwtVerifier", "JwtVerifyError"]
