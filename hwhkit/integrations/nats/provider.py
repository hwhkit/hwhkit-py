"""NatsProvider — JetStream-backed adapter implementing ``MessageBus``.

Uses NATS JetStream when available for durable + at-least-once delivery;
falls back to core NATS pub/sub semantics for ``publish``/``subscribe``
without ``durable`` argument.

Lazy-imports nats-py so module is importable without the ``[nats]`` extra.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from hwhkit.core.contracts.message_bus import PublishAck
from hwhkit.core.errors import NatsConnectionError
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.integrations.nats.config import NatsConfig

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext

_logger = logging.getLogger(__name__)


class NatsProvider(IntegrationProvider):
    """nats-py async adapter implementing ``MessageBus``."""

    name: ClassVar[str] = "nats"
    config_schema: ClassVar[type[BaseModel]] = NatsConfig

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        from hwhkit.core.contracts.message_bus import MessageBus

        return [MessageBus]

    def __init__(self, config: NatsConfig | None = None) -> None:
        self._config = config
        self._nc: Any = None  # nats.aio.Client
        self._js: Any = None  # JetStreamContext
        self._subscriptions: list[Any] = []
        self._is_ready: bool = False

    @property
    def client(self) -> Any:
        if self._nc is None:
            raise NatsConnectionError("NatsProvider.client accessed before setup()")
        return self._nc

    @property
    def js(self) -> Any:
        if self._js is None:
            raise NatsConnectionError("JetStream context not initialized")
        return self._js

    async def setup(self, ctx: AppContext) -> None:
        cfg = self._resolve_config(ctx)
        try:
            import nats
        except ImportError as exc:
            raise ImportError(
                "NatsProvider requires hwhkit[nats] extras: pip install 'hwhkit[nats]'"
            ) from exc

        try:
            self._nc = await nats.connect(
                servers=cfg.servers,
                name=cfg.name,
                max_reconnect_attempts=cfg.max_reconnect_attempts,
                reconnect_time_wait=cfg.reconnect_time_wait,
            )
            self._js = self._nc.jetstream()
        except Exception as exc:
            raise NatsConnectionError(f"Cannot connect to NATS at {cfg.servers}: {exc}") from exc

        if cfg.ensure_stream:
            await self._ensure_stream(cfg.ensure_stream, cfg.ensure_subjects)

        self._is_ready = True

    async def _ensure_stream(self, name: str, subjects: list[str]) -> None:
        """Create the JetStream stream if it doesn't exist."""
        from nats.js.api import StreamConfig

        try:
            await self._js.stream_info(name)
        except Exception:
            await self._js.add_stream(StreamConfig(name=name, subjects=subjects or [name]))

    async def shutdown(self) -> None:
        import contextlib

        for sub in self._subscriptions:
            with contextlib.suppress(Exception):
                await sub.unsubscribe()
        self._subscriptions.clear()
        if self._nc is not None:
            with contextlib.suppress(Exception):
                await self._nc.drain()
            with contextlib.suppress(Exception):
                await self._nc.close()
        self._nc = None
        self._js = None
        self._is_ready = False

    async def health_check(self) -> HealthStatus:
        if not self._is_ready or self._nc is None:
            return HealthStatus.fail("nats provider not ready")
        if self._nc.is_connected:
            return HealthStatus.ok(f"nats connected to {self._nc.connected_url}")
        return HealthStatus.fail("nats not connected")

    # ---- MessageBus contract ---------------------------------------------
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        deduplication_key: str | None = None,
    ) -> PublishAck:
        if not self._is_ready:
            raise NatsConnectionError("NatsProvider not ready")
        msg_headers: dict[str, str] = headers or {}
        if deduplication_key:
            msg_headers["Nats-Msg-Id"] = deduplication_key

        # Prefer JetStream publish (durable + acked); fall back to core publish
        if self._js is not None:
            try:
                ack = await self._js.publish(subject, payload, headers=msg_headers or None)
                return PublishAck(
                    subject=subject,
                    sequence=int(getattr(ack, "seq", 0)),
                    duplicate=bool(getattr(ack, "duplicate", False)),
                )
            except Exception as exc:
                _logger.debug("JetStream publish failed for %s: %s; falling back", subject, exc)

        await self._nc.publish(subject, payload, headers=msg_headers or None)
        return PublishAck(subject=subject, sequence=0, duplicate=False)

    async def subscribe(
        self,
        subject: str,
        handler: Callable[..., Awaitable[None]],
        *,
        durable: str | None = None,
        manual_ack: bool = False,
        max_in_flight: int = 100,
    ) -> _NatsSubscription:
        if not self._is_ready:
            raise NatsConnectionError("NatsProvider not ready")

        if durable is not None and self._js is not None:
            # Durable JetStream consumer
            sub = await self._js.subscribe(subject, durable=durable, manual_ack=manual_ack)
        else:
            # Ephemeral core-NATS subscription
            async def _on_message(msg: Any) -> None:
                await handler(_NatsMessage(msg, manual_ack=manual_ack))

            sub = await self._nc.subscribe(subject, cb=_on_message)

        wrapped = _NatsSubscription(self, subject, sub)
        if durable is not None and self._js is not None:
            # Drain durable consumer in background
            async def _pull_loop() -> None:
                while not wrapped._stopped:
                    try:
                        msgs = await sub.fetch(batch=10, timeout=1.0)
                        for msg in msgs:
                            await handler(_NatsMessage(msg, manual_ack=manual_ack))
                    except TimeoutError:
                        continue
                    except Exception as exc:
                        _logger.warning("nats fetch loop error: %s", exc)
                        await asyncio.sleep(0.5)

            wrapped._task = asyncio.create_task(_pull_loop())

        self._subscriptions.append(wrapped)
        return wrapped

    async def request(
        self,
        subject: str,
        payload: bytes,
        timeout: timedelta = timedelta(seconds=5),
    ) -> bytes:
        if not self._is_ready:
            raise NatsConnectionError("NatsProvider not ready")
        msg = await self._nc.request(subject, payload, timeout=timeout.total_seconds())
        data: bytes = msg.data
        return data

    # ---- internals --------------------------------------------------------
    def _resolve_config(self, ctx: AppContext) -> NatsConfig:
        if self._config is not None:
            return self._config
        cfg = getattr(ctx.config, "nats", None)
        if isinstance(cfg, NatsConfig):
            return cfg
        return NatsConfig()


class _NatsMessage:
    """A delivered NATS message satisfying ``Message`` protocol."""

    def __init__(self, raw_msg: Any, *, manual_ack: bool = False) -> None:
        self._raw = raw_msg
        self._manual_ack = manual_ack
        self.subject = raw_msg.subject
        self.payload: bytes = raw_msg.data
        self.headers: dict[str, str] = dict(raw_msg.headers or {})

    async def ack(self) -> None:
        if self._manual_ack and hasattr(self._raw, "ack"):
            await self._raw.ack()

    async def nack(self, *, requeue: bool = True) -> None:
        if hasattr(self._raw, "nak"):
            await self._raw.nak()


class _NatsSubscription:
    def __init__(self, provider: NatsProvider, subject: str, sub: Any) -> None:
        self._provider = provider
        self.subject = subject
        self._sub = sub
        self._stopped = False
        self._task: asyncio.Task[None] | None = None

    async def unsubscribe(self) -> None:
        import contextlib

        self._stopped = True
        if self._task is not None:
            self._task.cancel()
        with contextlib.suppress(Exception):
            await self._sub.unsubscribe()


__all__ = ["NatsProvider"]
