"""AuthMiddleware — validates Bearer JWT, injects ``request.state.user``.

Per spec § 3.4. Routes can opt out via the ``__hwhkit_public__`` attribute set
by the ``@public_endpoint`` decorator. Built-in system routes (``/healthz``,
``/readyz``, ``/version``, ``/metrics``) are always public.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse

from hwhkit.core.jwt import JwtVerifier, JwtVerifyError
from hwhkit.web.responses import ApiResponse

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from starlette.requests import Request
    from starlette.responses import Response

PUBLIC_ATTR = "__hwhkit_public__"
_ALWAYS_PUBLIC = frozenset({"/healthz", "/readyz", "/version", "/metrics"})


def public_endpoint(func: Any) -> Any:
    """Decorator marking a route exempt from JwtAuth checking."""
    setattr(func, PUBLIC_ATTR, True)
    return func


class AuthMiddleware(BaseHTTPMiddleware):
    """JWT Bearer token authentication.

    On success, sets ``request.state.user`` to the decoded claims dict.
    On failure, returns 401 + ApiResponse(code=100401).

    Path-based exclusion is the reliable mechanism (BaseHTTPMiddleware runs
    BEFORE routing, so a decorator-on-endpoint marker is not visible here).
    Built-in system paths (``/healthz`` / ``/readyz`` / ``/version`` /
    ``/metrics``) are always public.
    """

    def __init__(
        self,
        app: Any,
        *,
        verifier: JwtVerifier,
        exclude_paths: list[str] | None = None,
        exclude_prefixes: list[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._verifier = verifier
        self._exclude_paths = frozenset(_ALWAYS_PUBLIC | set(exclude_paths or []))
        self._exclude_prefixes = tuple(exclude_prefixes or [])

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        path = request.url.path
        if path in self._exclude_paths:
            return await call_next(request)
        if self._exclude_prefixes and path.startswith(self._exclude_prefixes):
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return self._unauth("missing Bearer token")
        token = auth_header[len("Bearer ") :]
        try:
            claims = await self._verifier.verify(token)
        except JwtVerifyError as exc:
            return self._unauth(f"token invalid: {exc}")
        request.state.user = claims
        return await call_next(request)

    @staticmethod
    def _unauth(message: str) -> JSONResponse:
        payload: ApiResponse[Any] = ApiResponse(code=100401, message=message)
        return JSONResponse(status_code=401, content=payload.model_dump(mode="json"))


__all__ = ["PUBLIC_ATTR", "AuthMiddleware", "public_endpoint"]
