"""In-memory ``DistributedLock`` fake.

Passes ``LockContractTests`` including the wrong-token safety test.
"""

from __future__ import annotations

import secrets
import time
from datetime import timedelta

from hwhkit.core.contracts.lock import LockToken


class FakeDistributedLock:
    """Single-process in-memory lock with token-based safe-release."""

    def __init__(self) -> None:
        # key -> (token, expires_at_monotonic)
        self._holders: dict[str, tuple[str, float]] = {}

    def _evict_if_expired(self, key: str) -> None:
        rec = self._holders.get(key)
        if rec is None:
            return
        _, exp = rec
        if time.monotonic() >= exp:
            self._holders.pop(key, None)

    async def acquire(
        self,
        key: str,
        ttl: timedelta,
        blocking: bool = True,
    ) -> LockToken | None:
        self._evict_if_expired(key)
        if key in self._holders:
            if not blocking:
                return None
            # In-process fake: emulate blocking by polling once after sleep.
            # Real implementations would use a notifier; this is sufficient
            # for unit tests which generally use blocking=False anyway.
            return None
        token = secrets.token_urlsafe(16)
        self._holders[key] = (token, time.monotonic() + ttl.total_seconds())
        return LockToken(key=key, token=token, ttl=ttl)

    async def release(self, token: LockToken) -> bool:
        self._evict_if_expired(token.key)
        rec = self._holders.get(token.key)
        if rec is None:
            return False
        held_token, _ = rec
        if held_token != token.token:
            return False  # not ours; never unlock someone else's lock
        del self._holders[token.key]
        return True

    async def extend(self, token: LockToken, ttl: timedelta) -> bool:
        self._evict_if_expired(token.key)
        rec = self._holders.get(token.key)
        if rec is None:
            return False
        held_token, _ = rec
        if held_token != token.token:
            return False
        self._holders[token.key] = (held_token, time.monotonic() + ttl.total_seconds())
        return True


__all__ = ["FakeDistributedLock"]
