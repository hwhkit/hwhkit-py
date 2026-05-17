"""FakeDistributedLock must pass the full DistributedLock contract suite."""

from __future__ import annotations

import pytest
from hwhkit.testing.contract_tests.lock import LockContractTests
from hwhkit.testing.fakes.lock import FakeDistributedLock


class TestFakeLockContract(LockContractTests):
    @pytest.fixture
    def lock(self) -> FakeDistributedLock:
        return FakeDistributedLock()
