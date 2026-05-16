"""hwhkit error taxonomy — 6-digit codes following the XYYZZZ scheme.

Code format: ``XYYZZZ``
    X    大类:1=客户端 / 5=服务端 / 9=外部依赖 / 6-8=业务自留
    YY   模块:00=core, 01=auth, 10=postgres, 11=redis, 12=nats, 13=scheduler,
              14=llm, 15=web, 20-99=业务保留
    ZZZ  具体错误:模块内自编

See spec § 3.3.
"""

from __future__ import annotations

from typing import Any, ClassVar


class ApiError(Exception):
    """Base for all framework / business errors.

    Subclasses override ``code`` and ``http_status`` as class attributes;
    instances carry ``message`` and optional ``details``.
    """

    code: ClassVar[int] = 500000
    http_status: ClassVar[int] = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(code={self.code}, http_status={self.http_status}, "
            f"message={self.message!r})"
        )


# ---- 4xx 客户端类(X=1, YY=00 core) --------------------------------------
class UnauthorizedError(ApiError):
    code = 100401
    http_status = 401


class ForbiddenError(ApiError):
    code = 100403
    http_status = 403


class NotFoundError(ApiError):
    code = 100404
    http_status = 404


class ConflictError(ApiError):
    code = 100409
    http_status = 409


class ValidationError(ApiError):
    code = 100422
    http_status = 422


class RateLimitError(ApiError):
    code = 100429
    http_status = 429


# ---- 5xx 服务端类(X=5) ---------------------------------------------------
class InternalError(ApiError):
    code = 500000
    http_status = 500


class IntegrationError(ApiError):
    """Generic downstream / integration failure."""

    code = 500001
    http_status = 503


# ---- 5xx 集成具体(X=5, YY=integration code) -----------------------------
class DbConnectionError(IntegrationError):
    code = 510001
    http_status = 503


class RedisConnectionError(IntegrationError):
    code = 511001
    http_status = 503


class NatsConnectionError(IntegrationError):
    code = 512001
    http_status = 503


__all__ = [
    "ApiError",
    "ConflictError",
    "DbConnectionError",
    "ForbiddenError",
    "IntegrationError",
    "InternalError",
    "NatsConnectionError",
    "NotFoundError",
    "RateLimitError",
    "RedisConnectionError",
    "UnauthorizedError",
    "ValidationError",
]
