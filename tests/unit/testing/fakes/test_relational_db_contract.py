"""FakeRelationalDb must pass the RelationalDb contract suite."""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
from hwhkit.testing.contract_tests.relational_db import RelationalDbContractTests
from hwhkit.testing.fakes.relational_db import FakeRelationalDb


class TestFakeRelationalDbContract(RelationalDbContractTests):
    @pytest.fixture
    async def db(self) -> AsyncIterator[FakeRelationalDb]:
        d = FakeRelationalDb()
        yield d
        await d.aclose()
