"""Reusable conformance tests for ``DistributedLock`` contract."""

from __future__ import annotations

import asyncio
from datetime import timedelta
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from hwhkit.core.contracts.lock import DistributedLock


class LockContractTests:
    """Inherit and provide an async ``lock`` fixture."""

    @pytest.mark.asyncio
    async def test_acquire_release(self, lock: DistributedLock) -> None:
        tok = await lock.acquire("k", timedelta(seconds=5), blocking=False)
        assert tok is not None
        assert tok.key == "k"
        ok = await lock.release(tok)
        assert ok is True

    @pytest.mark.asyncio
    async def test_acquire_twice_non_blocking_second_fails(self, lock: DistributedLock) -> None:
        t1 = await lock.acquire("k", timedelta(seconds=5), blocking=False)
        assert t1 is not None
        t2 = await lock.acquire("k", timedelta(seconds=5), blocking=False)
        assert t2 is None
        await lock.release(t1)

    @pytest.mark.asyncio
    async def test_release_after_ttl_expiry_returns_false(self, lock: DistributedLock) -> None:
        tok = await lock.acquire("k", timedelta(milliseconds=50), blocking=False)
        assert tok is not None
        await asyncio.sleep(0.1)
        # After TTL the lock is gone; releasing should still complete without raising
        # but report False (we don't hold it anymore).
        result = await lock.release(tok)
        assert result is False

    @pytest.mark.asyncio
    async def test_extend_existing(self, lock: DistributedLock) -> None:
        tok = await lock.acquire("k", timedelta(seconds=1), blocking=False)
        assert tok is not None
        ok = await lock.extend(tok, timedelta(seconds=5))
        assert ok is True
        await lock.release(tok)

    @pytest.mark.asyncio
    async def test_release_wrong_token_does_not_unlock(self, lock: DistributedLock) -> None:
        """A stolen-token release attempt must NOT unlock someone else's lock."""
        from hwhkit.core.contracts.lock import LockToken

        tok = await lock.acquire("k", timedelta(seconds=5), blocking=False)
        assert tok is not None
        fake = LockToken(key="k", token="not-the-real-token", ttl=timedelta(seconds=5))
        ok = await lock.release(fake)
        assert ok is False
        # Original holder can still release.
        assert await lock.release(tok) is True
