"""FakeMessageBus must pass the full MessageBus contract suite."""

from __future__ import annotations

import pytest
from hwhkit.testing.contract_tests.message_bus import MessageBusContractTests
from hwhkit.testing.fakes.message_bus import FakeMessageBus


class TestFakeMessageBusContract(MessageBusContractTests):
    @pytest.fixture
    def bus(self) -> FakeMessageBus:
        return FakeMessageBus()
