"""FakeCache must pass the full Cache contract conformance suite."""

from __future__ import annotations

import pytest
from hwhkit.testing.contract_tests.cache import CacheContractTests
from hwhkit.testing.fakes.cache import FakeCache


class TestFakeCacheContract(CacheContractTests):
    @pytest.fixture
    def cache(self) -> FakeCache:
        return FakeCache()
