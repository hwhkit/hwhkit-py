"""Common decorators: ``@retry`` / ``@timed`` / ``@safe_execute``."""

from __future__ import annotations

import asyncio
import functools
import inspect
import logging
import random
import time
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, cast, overload

_logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])
T = TypeVar("T")


# ---- @retry ---------------------------------------------------------------


def retry(
    *,
    attempts: int = 3,
    exceptions: type[Exception] | tuple[type[Exception], ...] = Exception,
    backoff: float = 0.5,
    max_backoff: float = 30.0,
    jitter: bool = True,
) -> Callable[[F], F]:
    """Decorator: re-invoke on listed exceptions with exponential backoff.

    Works on both sync and async functions.

    Args:
        attempts: total tries (1 = no retry).
        exceptions: exception classes that trigger retry; others propagate.
        backoff: base wait in seconds between attempts (doubles each time).
        max_backoff: cap.
        jitter: add +/- 25% randomization (avoid thundering herd).
    """
    if attempts < 1:
        raise ValueError("attempts must be >= 1")

    def _wait(attempt_idx: int) -> float:
        d: float = min(backoff * (2 ** (attempt_idx - 1)), max_backoff)
        if jitter:
            d = d * (0.75 + random.random() * 0.5)  # noqa: S311  not for crypto
        return d

    def _decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def _async_wrap(*args: Any, **kwargs: Any) -> Any:
                last_exc: Exception | None = None
                for attempt in range(1, attempts + 1):
                    try:
                        return await func(*args, **kwargs)
                    except exceptions as exc:
                        last_exc = exc
                        if attempt == attempts:
                            break
                        await asyncio.sleep(_wait(attempt))
                assert last_exc is not None
                raise last_exc

            return cast("F", _async_wrap)

        @functools.wraps(func)
        def _sync_wrap(*args: Any, **kwargs: Any) -> Any:
            last_exc: Exception | None = None
            for attempt in range(1, attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exc = exc
                    if attempt == attempts:
                        break
                    time.sleep(_wait(attempt))
            assert last_exc is not None
            raise last_exc

        return cast("F", _sync_wrap)

    return _decorator


# ---- @timed ---------------------------------------------------------------


def timed(label: str | None = None) -> Callable[[F], F]:
    """Decorator: log a debug line with function execution time in ms.

    Args:
        label: optional override for the log message; defaults to qualname.
    """

    def _decorator(func: F) -> F:
        log_label = label or f"{func.__module__}.{func.__qualname__}"

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def _async_wrap(*args: Any, **kwargs: Any) -> Any:
                start = time.perf_counter()
                try:
                    return await func(*args, **kwargs)
                finally:
                    elapsed_ms = (time.perf_counter() - start) * 1000
                    _logger.debug("%s took %.2fms", log_label, elapsed_ms)

            return cast("F", _async_wrap)

        @functools.wraps(func)
        def _sync_wrap(*args: Any, **kwargs: Any) -> Any:
            start = time.perf_counter()
            try:
                return func(*args, **kwargs)
            finally:
                elapsed_ms = (time.perf_counter() - start) * 1000
                _logger.debug("%s took %.2fms", log_label, elapsed_ms)

        return cast("F", _sync_wrap)

    return _decorator


# ---- @safe_execute --------------------------------------------------------


@overload
def safe_execute(
    *, default: T, log_exceptions: bool = True
) -> Callable[[Callable[..., T | Awaitable[T]]], Callable[..., T | Awaitable[T]]]: ...


@overload
def safe_execute(
    *, default: None = None, log_exceptions: bool = True
) -> Callable[[Callable[..., T | Awaitable[T]]], Callable[..., T | None | Awaitable[T | None]]]: ...


def safe_execute(*, default: Any = None, log_exceptions: bool = True) -> Any:
    """Decorator: swallow exceptions and return ``default`` instead.

    Use sparingly — it hides errors. Good fit for non-critical fire-and-forget
    side effects (e.g. analytics emit).
    """

    def _decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def _async_wrap(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except Exception as exc:
                    if log_exceptions:
                        _logger.exception("safe_execute caught: %s", exc)
                    return default

            return _async_wrap

        @functools.wraps(func)
        def _sync_wrap(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as exc:
                if log_exceptions:
                    _logger.exception("safe_execute caught: %s", exc)
                return default

        return _sync_wrap

    return _decorator


__all__ = ["retry", "safe_execute", "timed"]
