# Testing

hwhkit ships its own testing utilities in `hwhkit.testing`. Three pieces:

1. **Fakes** — in-memory contract implementations for unit tests
2. **Contract test suites** — reusable conformance tests
3. **OtelRecorder** — capture spans / metrics / logs without an SDK exporter

## Fakes

For every P0/P1 contract, an in-memory impl with the same semantics:

```python
from hwhkit.testing.fakes import (
    FakeCache,
    FakeKvStore,
    FakeDistributedLock,
    FakeMessageBus,
    FakeRelationalDb,
    FakeScheduler,
)
```

Wire them into your service constructors:

```python
import pytest
from hwhkit.testing.fakes import FakeCache, FakeRelationalDb

@pytest.mark.asyncio
async def test_portfolio_service() -> None:
    service = PortfolioService(
        db=FakeRelationalDb(),
        cache=FakeCache(),
    )
    ...
```

Fakes pass the same contract test suites as the real adapters, so your unit
tests catch real semantic bugs (TTL expiry, lock-not-held errors, etc.).

## Contract test suites

Reusable abstract test classes:

```python
import pytest
from hwhkit.testing.contract_tests.cache import CacheContractTests
from hwhkit.testing.fakes import FakeCache


class TestMyCacheLayer(CacheContractTests):
    @pytest.fixture
    def cache(self) -> FakeCache:
        return FakeCache()
```

That single class runs **all 11 Cache conformance tests** against your
fixture. The real `RedisProvider` runs the same suite — see
`tests/integration/redis/test_contract_conformance.py`.

Available suites:

- `CacheContractTests` (11 tests)
- `LockContractTests` (5 tests — including the wrong-token-can't-unlock
  safety test)
- `MessageBusContractTests` (3 tests)
- `RelationalDbContractTests` (3 tests)

## OtelRecorder

Drop-in fake `Tracer` / `Meter` / `LogEmitter` for assertions:

```python
from hwhkit.testing.otel_recorder import OtelRecorder

def test_records_span() -> None:
    rec = OtelRecorder()
    with rec.span("op-1") as span:
        span.set_attribute("k", "v")
    assert len(rec.spans) == 1
    assert rec.spans[0].attributes["k"] == "v"
```

## Test pyramid

| Layer | Target % | Time budget | Trigger |
|---|---|---|---|
| Unit (`tests/unit/`) | 70% | <30s full run | every commit |
| Integration (`tests/integration/`) | 20% | <3min | every PR (Docker required) |
| E2E (`tests/e2e/`) | 5% | <5min | every PR |
| Benchmark (`tests/benchmark/`) | 3% | <10min | every PR (compare baseline) |
| Chaos (`tests/chaos/`) | 1% | <15min | weekly cron |

Integration tests use **testcontainers** — see
`tests/integration/conftest.py` for the auto-managed Postgres + Redis
fixtures.
