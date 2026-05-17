"""Tests for hwhkit.core.contracts.cache — Cache & TypedCache."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import Any

import pytest
from hwhkit.core.contracts.cache import Cache, JsonCodec, PickleCodec, TypedCache


class InMemoryRawCache:
    """Minimal in-memory Cache impl used for contract-level tests only."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    async def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None:
        self._data[key] = value
        if ttl:

            async def _expire() -> None:
                await asyncio.sleep(ttl.total_seconds())
                self._data.pop(key, None)

            asyncio.create_task(_expire())

    async def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        return key in self._data

    async def incr(self, key: str, delta: int = 1) -> int:
        cur = int(self._data.get(key, b"0").decode())
        new = cur + delta
        self._data[key] = str(new).encode()
        return new

    async def expire(self, key: str, ttl: timedelta) -> bool:
        return key in self._data


class TestCacheProtocol:
    def test_is_runtime_checkable_positive(self) -> None:
        assert isinstance(InMemoryRawCache(), Cache)

    def test_is_runtime_checkable_negative(self) -> None:
        class Partial:
            async def get(self, key: str) -> bytes | None:
                return None

        assert not isinstance(Partial(), Cache)


class TestTypedCache:
    @pytest.mark.asyncio
    async def test_get_returns_none_when_missing(self) -> None:
        cache: TypedCache[dict[str, Any]] = TypedCache(raw=InMemoryRawCache())
        assert await cache.get("missing") is None

    @pytest.mark.asyncio
    async def test_set_then_get_roundtrip_json(self) -> None:
        cache: TypedCache[dict[str, Any]] = TypedCache(raw=InMemoryRawCache())
        await cache.set("k", {"a": 1, "b": "two"})
        assert await cache.get("k") == {"a": 1, "b": "two"}

    @pytest.mark.asyncio
    async def test_set_then_get_roundtrip_pickle(self) -> None:
        cache: TypedCache[tuple[int, int, int]] = TypedCache(
            raw=InMemoryRawCache(), codec=PickleCodec()
        )
        await cache.set("k", (1, 2, 3))
        assert await cache.get("k") == (1, 2, 3)

    @pytest.mark.asyncio
    async def test_delete(self) -> None:
        cache: TypedCache[dict[str, Any]] = TypedCache(raw=InMemoryRawCache())
        await cache.set("k", {"x": 1})
        assert await cache.delete("k") is True
        assert await cache.get("k") is None

    @pytest.mark.asyncio
    async def test_exists(self) -> None:
        cache: TypedCache[dict[str, Any]] = TypedCache(raw=InMemoryRawCache())
        assert await cache.exists("k") is False
        await cache.set("k", {"x": 1})
        assert await cache.exists("k") is True


def test_json_codec_roundtrip() -> None:
    codec = JsonCodec()
    raw = codec.encode({"a": 1})
    assert codec.decode(raw) == {"a": 1}
