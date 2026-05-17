"""Real RedisProvider must pass the Cache + Lock + MessageBus contracts.

Reuses the abstract test classes from hwhkit.testing.contract_tests; the
fixture supplies the real adapter (set up via testcontainers in conftest.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hwhkit.testing.contract_tests.cache import CacheContractTests
from hwhkit.testing.contract_tests.lock import LockContractTests
from hwhkit.testing.contract_tests.message_bus import MessageBusContractTests

if TYPE_CHECKING:
    from hwhkit.integrations.redis import RedisProvider

pytestmark = pytest.mark.integration


class TestRedisCacheContract(CacheContractTests):
    @pytest.fixture
    def cache(self, redis_provider: RedisProvider) -> RedisProvider:
        return redis_provider


class TestRedisLockContract(LockContractTests):
    @pytest.fixture
    def lock(self, redis_provider: RedisProvider) -> RedisProvider:
        return redis_provider


class TestRedisMessageBusContract(MessageBusContractTests):
    @pytest.fixture
    def bus(self, redis_provider: RedisProvider) -> RedisProvider:
        return redis_provider
