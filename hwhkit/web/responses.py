"""Unified response envelope: ``ApiResponse[T]`` + ``PageResponse[T]``.

Per spec § 3.2:
- Default: every response wrapped in ``ApiResponse`` envelope with
  ``code: int``, ``message: str``, ``data: T | None``, ``trace_id: str | None``.
- ``trace_id`` auto-populated from current OTel span when active.
- Opt-out: routes can declare ``@raw_response`` to skip wrapping (use for
  Prometheus /metrics, third-party webhook compatibility, etc.).
"""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")

# Sentinel attribute name set by ``@raw_response`` on the wrapped function.
RAW_RESPONSE_ATTR = "__hwhkit_raw_response__"


def _current_trace_id() -> str | None:
    """Return current OTel span's trace_id as hex, or None if no active span."""
    try:
        from opentelemetry import trace
    except ImportError:
        return None
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx is None or not ctx.is_valid:
        return None
    return format(ctx.trace_id, "032x")


class ApiResponse(BaseModel, Generic[T]):
    """Standard success envelope.

    Example::

        @router.get("/users/{id}", response_model=ApiResponse[User])
        async def get_user(id: int) -> ApiResponse[User]:
            user = await load_user(id)
            return ApiResponse(data=user)
    """

    code: int = 0
    """Business code; ``0`` means success. Non-zero follows the 6-digit XYYZZZ
    scheme defined in hwhkit.core.errors."""

    message: str = "ok"
    data: T | None = None
    trace_id: str | None = Field(default=None)

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        if self.trace_id is None:
            self.trace_id = _current_trace_id()


class PageResponse(BaseModel, Generic[T]):
    """Paginated payload — used as the ``data`` of a wrapping ``ApiResponse[PageResponse[T]]``."""

    items: list[T] = Field(default_factory=list)
    total: int = 0
    page: int = 1
    page_size: int = 20
    has_next: bool = False


def raw_response(func: Any) -> Any:
    """Decorator: mark a route to skip ``ApiResponse`` envelope wrapping.

    Use for: Prometheus /metrics, third-party webhook responses, file downloads.

    Example::

        @router.get("/metrics")
        @raw_response
        async def metrics() -> Response:
            return Response(content=registry.encode(), media_type="text/plain")
    """
    setattr(func, RAW_RESPONSE_ATTR, True)
    return func


def is_raw_response(func: Any) -> bool:
    """Check whether a function was marked with ``@raw_response``."""
    return bool(getattr(func, RAW_RESPONSE_ATTR, False))


__all__ = [
    "RAW_RESPONSE_ATTR",
    "ApiResponse",
    "PageResponse",
    "is_raw_response",
    "raw_response",
]
