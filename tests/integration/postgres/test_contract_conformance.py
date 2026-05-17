"""Real PostgresProvider must pass the RelationalDb contract suite."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from hwhkit.testing.contract_tests.relational_db import RelationalDbContractTests

if TYPE_CHECKING:
    from hwhkit.integrations.postgres import PostgresProvider

pytestmark = pytest.mark.integration


class TestPostgresRelationalDbContract(RelationalDbContractTests):
    @pytest.fixture
    def db(self, postgres_provider: PostgresProvider) -> PostgresProvider:
        return postgres_provider
