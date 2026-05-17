"""In-memory ``KvStore`` fake."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator


class FakeKvStore:
    """In-memory persistent KV store (no TTL — distinguishes from Cache)."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}
        self._watchers: dict[str, list[asyncio.Queue[bytes | None]]] = {}

    async def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    async def set(self, key: str, value: bytes) -> None:
        self._data[key] = value
        for q in self._watchers.get(key, []):
            q.put_nowait(value)

    async def delete(self, key: str) -> bool:
        existed = key in self._data
        self._data.pop(key, None)
        for q in self._watchers.get(key, []):
            q.put_nowait(None)
        return existed

    async def list_keys(self, prefix: str = "") -> list[str]:
        return sorted(k for k in self._data if k.startswith(prefix))

    async def watch(self, key: str) -> AsyncIterator[bytes | None]:
        q: asyncio.Queue[bytes | None] = asyncio.Queue()
        self._watchers.setdefault(key, []).append(q)
        try:
            while True:
                yield await q.get()
        finally:
            self._watchers.get(key, []).remove(q)


__all__ = ["FakeKvStore"]
