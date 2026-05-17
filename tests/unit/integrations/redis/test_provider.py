"""Unit tests for RedisProvider (no real Redis)."""

from __future__ import annotations

import pytest
from hwhkit.core.contracts.cache import Cache
from hwhkit.core.contracts.kv_store import KvStore
from hwhkit.core.contracts.lock import DistributedLock
from hwhkit.core.contracts.message_bus import MessageBus
from hwhkit.core.errors import RedisConnectionError
from hwhkit.integrations.redis import RedisConfig, RedisProvider


def test_provider_metadata() -> None:
    p = RedisProvider()
    assert p.name == "redis"
    assert p.config_schema is RedisConfig


def test_implements_all_four_contracts() -> None:
    p = RedisProvider()
    impls = set(p.implements)
    assert Cache in impls
    assert KvStore in impls
    assert DistributedLock in impls
    assert MessageBus in impls


def test_client_access_before_setup_raises() -> None:
    p = RedisProvider()
    with pytest.raises(RedisConnectionError, match="before setup"):
        _ = p.client


@pytest.mark.asyncio
async def test_health_check_fails_when_not_ready() -> None:
    p = RedisProvider()
    status = await p.health_check()
    assert status.healthy is False


@pytest.mark.asyncio
async def test_request_not_supported() -> None:
    p = RedisProvider()
    with pytest.raises(NotImplementedError, match="request/reply"):
        await p.request("subj", b"x")
