"""Graceful shutdown manager.

Callbacks run in reverse registration order (LIFO), each subject to a per-call
timeout. A failing callback logs but doesn't block subsequent callbacks.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable

ShutdownCallback = Callable[[], None | Awaitable[None]]

_logger = logging.getLogger(__name__)


class ShutdownTimeout(Exception):
    """Raised when one or more callbacks exceed the configured timeout."""


class GracefulShutdown:
    """LIFO-order shutdown executor with per-callback timeout."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._callbacks: list[tuple[str, ShutdownCallback]] = []

    def register(self, name: str, cb: ShutdownCallback) -> None:
        self._callbacks.append((name, cb))

    async def run(self) -> None:
        timeouts: list[str] = []
        for name, cb in reversed(self._callbacks):
            try:
                result = cb()
                if inspect.isawaitable(result):
                    await asyncio.wait_for(result, timeout=self._timeout)
            except TimeoutError:
                timeouts.append(name)
                _logger.error("Shutdown callback %r exceeded timeout %.1fs", name, self._timeout)
            except Exception as exc:
                _logger.exception("Shutdown callback %r failed: %s", name, exc)
        if timeouts:
            raise ShutdownTimeout(f"callbacks exceeded timeout: {timeouts}")


__all__ = ["GracefulShutdown", "ShutdownCallback", "ShutdownTimeout"]
