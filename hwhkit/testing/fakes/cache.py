"""In-memory ``Cache`` fake — passes ``CacheContractTests``."""

from __future__ import annotations

import asyncio
import contextlib
import time
from datetime import timedelta


class FakeCache:
    """Process-local in-memory Cache. TTL via expiry timestamps + background sweep.

    Not thread-safe; concurrency model is asyncio single-loop.
    """

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}
        self._expires_at: dict[str, float] = {}

    def _evict_if_expired(self, key: str) -> None:
        exp = self._expires_at.get(key)
        if exp is not None and time.monotonic() >= exp:
            self._data.pop(key, None)
            self._expires_at.pop(key, None)

    async def get(self, key: str) -> bytes | None:
        self._evict_if_expired(key)
        return self._data.get(key)

    async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None:
        self._data[key] = value
        if ttl is not None:
            self._expires_at[key] = time.monotonic() + ttl.total_seconds()
        else:
            self._expires_at.pop(key, None)

    async def delete(self, key: str) -> bool:
        self._evict_if_expired(key)
        existed = key in self._data
        self._data.pop(key, None)
        self._expires_at.pop(key, None)
        return existed

    async def exists(self, key: str) -> bool:
        self._evict_if_expired(key)
        return key in self._data

    async def incr(self, key: str, delta: int = 1) -> int:
        self._evict_if_expired(key)
        raw = self._data.get(key, b"0")
        with contextlib.suppress(ValueError):
            new = int(raw.decode()) + delta
            self._data[key] = str(new).encode()
            return new
        # Not numeric — start fresh
        self._data[key] = str(delta).encode()
        return delta

    async def expire(self, key: str, ttl: timedelta) -> bool:
        self._evict_if_expired(key)
        if key not in self._data:
            return False
        self._expires_at[key] = time.monotonic() + ttl.total_seconds()
        return True


# Smoke: avoid unused warnings for asyncio import (it's used elsewhere in fakes module).
_ = asyncio

__all__ = ["FakeCache"]
