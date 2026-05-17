"""In-memory ``MessageBus`` fake.

Pure-asyncio implementation; subjects are exact-match (no NATS-style wildcards).
"""

from __future__ import annotations

import asyncio
import secrets
from collections.abc import Awaitable, Callable
from datetime import timedelta

from hwhkit.core.contracts.message_bus import PublishAck


class _FakeMessage:
    """A delivered message satisfying the ``Message`` protocol."""

    def __init__(self, subject: str, payload: bytes, headers: dict[str, str]) -> None:
        self.subject = subject
        self.payload = payload
        self.headers = headers

    async def ack(self) -> None:
        pass  # FakeMessageBus auto-acks; no-op

    async def nack(self, *, requeue: bool = True) -> None:
        pass  # no-op for in-memory bus


class _FakeSubscription:
    def __init__(self, bus: FakeMessageBus, subject: str, handler_id: str) -> None:
        self._bus = bus
        self.subject = subject
        self._handler_id = handler_id

    async def unsubscribe(self) -> None:
        self._bus._unregister(self.subject, self._handler_id)


class FakeMessageBus:
    """In-memory bus. ``request()`` not supported (raises NotImplementedError)."""

    def __init__(self) -> None:
        # subject -> {handler_id: callback}
        self._handlers: dict[str, dict[str, Callable[..., Awaitable[None]]]] = {}
        self._seq = 0
        self._tasks: set[asyncio.Task[None]] = set()

    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        deduplication_key: str | None = None,
    ) -> PublishAck:
        self._seq += 1
        # Fire-and-forget delivery to all handlers; keep references so the GC
        # doesn't cancel them while they're still queued.
        for handler in list(self._handlers.get(subject, {}).values()):
            msg = _FakeMessage(subject, payload, headers or {})
            coro = handler(msg)
            t: asyncio.Task[None] = asyncio.create_task(coro)  # type: ignore[arg-type]
            self._tasks.add(t)
            t.add_done_callback(self._tasks.discard)
        return PublishAck(subject=subject, sequence=self._seq, duplicate=False)

    async def subscribe(
        self,
        subject: str,
        handler: Callable[..., Awaitable[None]],
        *,
        durable: str | None = None,
        manual_ack: bool = False,
        max_in_flight: int = 100,
    ) -> _FakeSubscription:
        handler_id = secrets.token_hex(8)
        self._handlers.setdefault(subject, {})[handler_id] = handler
        return _FakeSubscription(self, subject, handler_id)

    async def request(
        self,
        subject: str,
        payload: bytes,
        timeout: timedelta = timedelta(seconds=5),
    ) -> bytes:
        raise NotImplementedError(
            "FakeMessageBus does not support request/reply; use a real adapter (e.g. NATS)."
        )

    def _unregister(self, subject: str, handler_id: str) -> None:
        self._handlers.get(subject, {}).pop(handler_id, None)


__all__ = ["FakeMessageBus"]
