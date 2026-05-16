"""DistributedLock contract — cross-process / cross-host mutual exclusion.

Implementations: Redis Redlock (P0), etcd / ZooKeeper (future).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class LockToken:
    """Opaque handle returned by ``acquire``; required for ``release`` / ``extend``."""

    key: str
    token: str
    ttl: timedelta


@runtime_checkable
class DistributedLock(Protocol):
    async def acquire(
        self,
        key: str,
        ttl: timedelta,
        blocking: bool = True,
    ) -> LockToken | None: ...

    async def release(self, token: LockToken) -> bool: ...

    async def extend(self, token: LockToken, ttl: timedelta) -> bool: ...


__all__ = ["DistributedLock", "LockToken"]
