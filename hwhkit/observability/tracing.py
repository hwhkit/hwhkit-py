"""Tracing helpers: ``@traced`` decorator + ``span()`` context manager.

Built on the global OTel tracer; works as no-op when OTel is disabled.
"""

from __future__ import annotations

import functools
import inspect
from collections.abc import Awaitable, Callable, Iterator
from contextlib import contextmanager
from typing import Any, TypeVar, cast

F = TypeVar("F", bound=Callable[..., Any])


def _tracer() -> Any:
    """Lazily-bound tracer; reads global TracerProvider at call site."""
    from opentelemetry import trace

    return trace.get_tracer("hwhkit")


@contextmanager
def span(name: str, **attrs: Any) -> Iterator[Any]:
    """Context manager that starts/ends an OTel span.

    Usage:
        with span("portfolio.rebalance", user_id=42):
            ...
    """
    with _tracer().start_as_current_span(name) as s:
        for k, v in attrs.items():
            s.set_attribute(k, v)
        yield s


def traced(
    name: str | None = None,
    *,
    record_exception: bool = True,
) -> Callable[[F], F]:
    """Decorator that wraps the function call in an OTel span.

    Works on both sync and async functions. Span name defaults to
    ``module.qualname``. Function arguments are NOT recorded by default
    (avoid leaking PII); add attributes explicitly inside the body via
    ``trace.get_current_span().set_attribute(...)`` if needed.

    Args:
        name: span name; defaults to ``f.__module__ + "." + f.__qualname__``.
        record_exception: if True, exceptions are recorded on the span before
            re-raising.
    """

    def _decorator(func: F) -> F:
        span_name = name or f"{func.__module__}.{func.__qualname__}"

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def _async_wrap(*args: Any, **kwargs: Any) -> Any:
                with _tracer().start_as_current_span(span_name) as s:
                    try:
                        return await func(*args, **kwargs)
                    except Exception as exc:
                        if record_exception:
                            s.record_exception(exc)
                        raise

            return cast("F", _async_wrap)

        @functools.wraps(func)
        def _sync_wrap(*args: Any, **kwargs: Any) -> Any:
            with _tracer().start_as_current_span(span_name) as s:
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    if record_exception:
                        s.record_exception(exc)
                    raise

        return cast("F", _sync_wrap)

    return _decorator


# ---- public typed alias for "async function returning T" used in decorator ----
AsyncFunc = Callable[..., Awaitable[Any]]

__all__ = ["span", "traced"]
