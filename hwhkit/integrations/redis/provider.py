"""RedisProvider — async Redis adapter implementing Cache + KvStore + Lock + MessageBus.

Lazy-imports redis.asyncio so the module is importable without the ``[redis]``
extra installed.
"""

from __future__ import annotations

import asyncio
import logging
import secrets
from collections.abc import AsyncIterator, Awaitable, Callable
from datetime import timedelta
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

from hwhkit.core.contracts.lock import LockToken
from hwhkit.core.contracts.message_bus import PublishAck
from hwhkit.core.errors import RedisConnectionError
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.integrations.redis.config import RedisConfig

if TYPE_CHECKING:
    from hwhkit.core.context import AppContext

_logger = logging.getLogger(__name__)

# Lua: only delete the key if its value matches our token (safe-release).
_SAFE_RELEASE_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
else
    return 0
end
"""

# Lua: only PEXPIRE if value matches our token (safe-extend).
_SAFE_EXTEND_LUA = """
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('PEXPIRE', KEYS[1], ARGV[2])
else
    return 0
end
"""


class RedisProvider(IntegrationProvider):
    """Multi-contract Redis adapter.

    Single redis.asyncio.Redis connection pool serves all four contracts.
    Pub/Sub uses a separate connection per active subscription (Redis pub/sub
    semantics require this).
    """

    name: ClassVar[str] = "redis"
    config_schema: ClassVar[type[BaseModel]] = RedisConfig

    @property
    def implements(self) -> list[type]:  # type: ignore[override]
        from hwhkit.core.contracts.cache import Cache
        from hwhkit.core.contracts.kv_store import KvStore
        from hwhkit.core.contracts.lock import DistributedLock
        from hwhkit.core.contracts.message_bus import MessageBus

        return [Cache, KvStore, DistributedLock, MessageBus]

    def __init__(self, config: RedisConfig | None = None) -> None:
        self._config = config
        self._client: Any = None  # redis.asyncio.Redis
        self._subscriptions: list[asyncio.Task[None]] = []
        self._is_ready: bool = False

    @property
    def client(self) -> Any:
        """Underlying redis.asyncio.Redis client (escape hatch)."""
        if self._client is None:
            raise RedisConnectionError("RedisProvider.client accessed before setup()")
        return self._client

    async def setup(self, ctx: AppContext) -> None:
        cfg = self._resolve_config(ctx)
        try:
            from redis.asyncio import Redis
        except ImportError as exc:
            raise ImportError(
                "RedisProvider requires hwhkit[redis] extras: pip install 'hwhkit[redis]'"
            ) from exc

        self._client = Redis.from_url(
            cfg.url,
            max_connections=cfg.max_connections,
            socket_timeout=cfg.socket_timeout,
            socket_connect_timeout=cfg.socket_connect_timeout,
            health_check_interval=cfg.health_check_interval,
            decode_responses=cfg.decode_responses,
        )
        # Verify connectivity
        try:
            result: Any = self._client.ping()
            if hasattr(result, "__await__"):
                await result
        except Exception as exc:
            raise RedisConnectionError(f"Cannot connect to Redis at {cfg.url}: {exc}") from exc
        self._is_ready = True

        try:
            from hwhkit.observability.instrumentation import (
                auto_instrument_redis,
            )

            auto_instrument_redis()
        except Exception as exc:
            _logger.debug("Redis auto-instrumentation skipped: %s", exc)

    async def shutdown(self) -> None:
        for task in self._subscriptions:
            task.cancel()
        self._subscriptions.clear()
        if self._client is not None:
            await self._client.aclose()
            self._client = None
        self._is_ready = False

    async def health_check(self) -> HealthStatus:
        if not self._is_ready or self._client is None:
            return HealthStatus.fail("redis provider not ready")
        try:
            result: Any = self._client.ping()
            pong = await result if hasattr(result, "__await__") else result
            if pong:
                return HealthStatus.ok("redis reachable")
            return HealthStatus.fail("redis ping returned falsy")
        except Exception as exc:
            return HealthStatus.fail(f"redis unreachable: {exc}")

    # ---- Cache contract ----------------------------------------------------
    async def get(self, key: str) -> bytes | None:
        result: bytes | None = await self.client.get(key)
        return result

    async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None:
        if ttl is not None:
            await self.client.set(key, value, px=int(ttl.total_seconds() * 1000))
        else:
            await self.client.set(key, value)

    async def delete(self, key: str) -> bool:
        deleted: int = await self.client.delete(key)
        return deleted > 0

    async def exists(self, key: str) -> bool:
        exists: int = await self.client.exists(key)
        return exists > 0

    async def incr(self, key: str, delta: int = 1) -> int:
        result: int = await self.client.incrby(key, delta)
        return result

    async def expire(self, key: str, ttl: timedelta) -> bool:
        result: bool = await self.client.expire(key, int(ttl.total_seconds()))
        return bool(result)

    # ---- KvStore contract (overlaps with Cache but no TTL semantics) ------
    async def list_keys(self, prefix: str = "") -> list[str]:
        pattern = f"{prefix}*" if prefix else "*"
        keys: list[bytes | str] = await self.client.keys(pattern)
        return [k.decode() if isinstance(k, bytes) else k for k in keys]

    async def watch(self, key: str) -> AsyncIterator[bytes | None]:
        """Yield new values as they arrive on key-space notifications.

        Requires Redis ``notify-keyspace-events`` config to include 'g' (or 'KEA').
        """
        pubsub = self.client.pubsub()
        channel = f"__keyspace@0__:{key}"
        await pubsub.subscribe(channel)
        try:
            async for msg in pubsub.listen():
                if msg["type"] != "message":
                    continue
                action = msg["data"]
                if isinstance(action, bytes):
                    action = action.decode()
                if action in {"set", "hset"}:
                    yield await self.get(key)
                elif action in {"del", "expired"}:
                    yield None
        finally:
            await pubsub.unsubscribe(channel)
            await pubsub.aclose()

    # ---- DistributedLock contract -----------------------------------------
    async def acquire(
        self,
        key: str,
        ttl: timedelta,
        blocking: bool = True,
    ) -> LockToken | None:
        token = secrets.token_urlsafe(16)
        # Atomic SET NX EX
        ok = await self.client.set(
            key,
            token,
            px=int(ttl.total_seconds() * 1000),
            nx=True,
        )
        if ok:
            return LockToken(key=key, token=token, ttl=ttl)
        if not blocking:
            return None
        # Best-effort polling for blocking acquires; bounded by TTL.
        deadline = ttl.total_seconds()
        elapsed = 0.0
        while elapsed < deadline:
            await asyncio.sleep(min(0.05, deadline - elapsed))
            elapsed += 0.05
            ok = await self.client.set(
                key,
                token,
                px=int(ttl.total_seconds() * 1000),
                nx=True,
            )
            if ok:
                return LockToken(key=key, token=token, ttl=ttl)
        return None

    async def release(self, token: LockToken) -> bool:
        result: int = await self.client.eval(_SAFE_RELEASE_LUA, 1, token.key, token.token)
        return result == 1

    async def extend(self, token: LockToken, ttl: timedelta) -> bool:
        result: int = await self.client.eval(
            _SAFE_EXTEND_LUA,
            1,
            token.key,
            token.token,
            int(ttl.total_seconds() * 1000),
        )
        return result == 1

    # ---- MessageBus contract (pub/sub — not durable) ----------------------
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        deduplication_key: str | None = None,
    ) -> PublishAck:
        # Redis pub/sub doesn't have headers or dedup; we drop them silently.
        await self.client.publish(subject, payload)
        return PublishAck(subject=subject, sequence=0, duplicate=False)

    async def subscribe(
        self,
        subject: str,
        handler: Callable[..., Awaitable[None]],
        *,
        durable: str | None = None,
        manual_ack: bool = False,
        max_in_flight: int = 100,
    ) -> _RedisSubscription:
        pubsub = self.client.pubsub()
        await pubsub.subscribe(subject)
        sub = _RedisSubscription(self, subject, pubsub)
        task = asyncio.create_task(sub._run(handler))
        self._subscriptions.append(task)
        return sub

    async def request(
        self,
        subject: str,
        payload: bytes,
        timeout: timedelta = timedelta(seconds=5),
    ) -> bytes:
        raise NotImplementedError(
            "RedisProvider does not support request/reply; use NATS for that semantic."
        )

    # ---- internals --------------------------------------------------------
    def _resolve_config(self, ctx: AppContext) -> RedisConfig:
        if self._config is not None:
            return self._config
        cfg = getattr(ctx.config, "redis", None)
        if isinstance(cfg, RedisConfig):
            return cfg
        return RedisConfig()


class _RedisMessage:
    """A delivered pub/sub message."""

    def __init__(self, subject: str, payload: bytes) -> None:
        self.subject = subject
        self.payload = payload
        self.headers: dict[str, str] = {}

    async def ack(self) -> None:
        pass  # Redis pub/sub auto-acks

    async def nack(self, *, requeue: bool = True) -> None:
        pass  # No-op for non-durable pub/sub


class _RedisSubscription:
    def __init__(self, provider: RedisProvider, subject: str, pubsub: Any) -> None:
        self._provider = provider
        self.subject = subject
        self._pubsub = pubsub
        self._stopped = False

    async def _run(self, handler: Callable[..., Awaitable[None]]) -> None:
        try:
            async for msg in self._pubsub.listen():
                if self._stopped:
                    return
                if msg["type"] != "message":
                    continue
                payload = msg["data"] if isinstance(msg["data"], bytes) else msg["data"].encode()
                await handler(_RedisMessage(self.subject, payload))
        except asyncio.CancelledError:
            return
        except Exception as exc:
            _logger.exception("redis subscription crashed: %s", exc)

    async def unsubscribe(self) -> None:
        self._stopped = True
        await self._pubsub.unsubscribe(self.subject)
        await self._pubsub.aclose()


__all__ = ["RedisProvider"]
