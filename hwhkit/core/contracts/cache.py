"""Cache contract — byte-level key-value cache abstraction.

Implementations:
- ``hwhkit.integrations.redis.RedisProvider`` (production)
- ``hwhkit.testing.fakes.cache.FakeCache`` (testing)
"""

from __future__ import annotations

import json
import pickle
from datetime import timedelta
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Cache(Protocol):
    """Byte-level key-value cache. Codec is the caller's concern."""

    async def get(self, key: str) -> bytes | None: ...

    async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None: ...

    async def delete(self, key: str) -> bool: ...

    async def exists(self, key: str) -> bool: ...

    async def incr(self, key: str, delta: int = 1) -> int: ...

    async def expire(self, key: str, ttl: timedelta) -> bool: ...


class Codec(Protocol[T]):
    """Encoder/decoder for typed cache values."""

    def encode(self, value: T) -> bytes: ...

    def decode(self, raw: bytes) -> T: ...


class JsonCodec:
    """Default codec: JSON (UTF-8)."""

    def encode(self, value: Any) -> bytes:
        return json.dumps(value).encode("utf-8")

    def decode(self, raw: bytes) -> Any:
        return json.loads(raw.decode("utf-8"))


class PickleCodec:
    """Use for non-JSON-serializable types. Unsafe across trust boundaries."""

    def encode(self, value: Any) -> bytes:
        return pickle.dumps(value)

    def decode(self, raw: bytes) -> Any:
        return pickle.loads(raw)  # noqa: S301


class TypedCache(Generic[T]):
    """High-level typed cache wrapping any ``Cache`` adapter with a codec."""

    def __init__(self, raw: Cache, codec: Codec[T] | None = None) -> None:
        self._raw = raw
        self._codec: Codec[T] = codec if codec is not None else JsonCodec()

    async def get(self, key: str) -> T | None:
        raw = await self._raw.get(key)
        if raw is None:
            return None
        return self._codec.decode(raw)

    async def set(self, key: str, value: T, ttl: timedelta | None = None) -> None:
        await self._raw.set(key, self._codec.encode(value), ttl)

    async def delete(self, key: str) -> bool:
        return await self._raw.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._raw.exists(key)


__all__ = ["Cache", "Codec", "JsonCodec", "PickleCodec", "TypedCache"]
