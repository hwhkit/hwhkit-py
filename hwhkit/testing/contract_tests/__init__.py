"""Reusable contract conformance test suites.

Each module defines an abstract test class that future adapters inherit and
bind a fixture for their adapter. The same tests run against fakes and real
adapters, ensuring semantic equivalence.

Usage::

    # tests/integration/redis/test_contract_conformance.py
    import pytest
    from hwhkit.testing.contract_tests.cache import CacheContractTests

    class TestRedisCacheContract(CacheContractTests):
        @pytest.fixture
        async def cache(self, redis_provider):
            yield redis_provider
"""
