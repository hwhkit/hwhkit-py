"""KvStore contract — persistent key-value storage (vs. ephemeral Cache).

Implementations: Redis (P0), etcd / Consul (future).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class KvStore(Protocol):
    async def get(self, key: str) -> bytes | None: ...

    async def set(self, key: str, value: bytes) -> None: ...

    async def delete(self, key: str) -> bool: ...

    async def list_keys(self, prefix: str = "") -> list[str]: ...

    def watch(self, key: str) -> AsyncIterator[bytes | None]: ...


__all__ = ["KvStore"]
