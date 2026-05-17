"""MessageBus contract — unified pub/sub + request/reply abstraction.

Implementations:
- NATS JetStream (P1)
- Redis pub/sub (via RedisProvider, P0 partial)
- Kafka / RabbitMQ / Redis Streams (future)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PublishAck:
    """Acknowledgement returned by ``publish``."""

    subject: str
    sequence: int
    duplicate: bool


@runtime_checkable
class Message(Protocol):
    """A delivered message."""

    subject: str
    payload: bytes
    headers: dict[str, str]

    async def ack(self) -> None: ...

    async def nack(self, *, requeue: bool = True) -> None: ...


@runtime_checkable
class Subscription(Protocol):
    """A live subscription. Cancel by calling ``unsubscribe``."""

    subject: str

    async def unsubscribe(self) -> None: ...


@runtime_checkable
class MessageBus(Protocol):
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        deduplication_key: str | None = None,
    ) -> PublishAck: ...

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[Message], Awaitable[None]],
        *,
        durable: str | None = None,
        manual_ack: bool = False,
        max_in_flight: int = 100,
    ) -> Subscription: ...

    async def request(
        self,
        subject: str,
        payload: bytes,
        timeout: timedelta = timedelta(seconds=5),
    ) -> bytes: ...


__all__ = ["Message", "MessageBus", "PublishAck", "Subscription"]
