# Trading service skeleton

Typical layout: HTTP API + Postgres state + Redis cache + NATS event bus +
APScheduler for end-of-day reports.

## Generate

```bash
hwhkit init trading-svc
cd trading-svc
hwhkit add postgres redis nats scheduler otel
```

## Project layout (after init + adds)

```
trading-svc/
├── pyproject.toml
├── Makefile
├── Dockerfile
├── docker-compose.yml          # postgres / redis / nats commented in
├── .env.example
├── trading_svc/
│   ├── main.py                 # bootstrap() + integrations
│   ├── config.py               # AppSettings with postgres / redis / nats sections
│   ├── api/                    # FastAPI routers
│   ├── services/               # business logic (depends on contracts only)
│   ├── domain/                 # SQLAlchemy models, value objects
│   └── adapters/               # project-specific external integrations
└── tests/
    ├── conftest.py
    └── unit/
```

## main.py (post-add)

```python
from hwhkit import bootstrap
from hwhkit.integrations.postgres import PostgresProvider
from hwhkit.integrations.redis import RedisProvider
from hwhkit.integrations.nats import NatsProvider
from hwhkit.scheduler import SchedulerProvider, register_scheduled_tasks

from trading_svc.api import api_router
from trading_svc.config import AppSettings

# Import for side-effect: registers @scheduled_task functions
from trading_svc import jobs  # noqa: F401

app = bootstrap(
    name="trading-svc",
    version="0.1.0",
    settings_cls=AppSettings,
    integrations=[
        PostgresProvider(),
        RedisProvider(),
        NatsProvider(),
        SchedulerProvider(),
    ],
    routers=[api_router],
    on_startup=[register_scheduled_tasks],
)
```

## A service depending on contracts

```python
# trading_svc/services/portfolio.py
from hwhkit.core.contracts import Cache, MessageBus, RelationalDb


class PortfolioService:
    def __init__(self, db: RelationalDb, cache: Cache, bus: MessageBus):
        self.db = db
        self.cache = cache
        self.bus = bus

    async def execute_trade(self, user_id: int, symbol: str, qty: int) -> Trade:
        async with self.db.session() as s:
            trade = Trade(user_id=user_id, symbol=symbol, qty=qty)
            s.add(trade)
            await s.commit()
            await s.refresh(trade)

        # Invalidate cached position
        await self.cache.delete(f"pos:{user_id}:{symbol}")

        # Publish event for downstream consumers
        await self.bus.publish(
            "trades.executed",
            trade.to_bytes(),
            deduplication_key=f"trade-{trade.id}",
        )
        return trade
```

## A handler wiring contracts via AppContext

```python
# trading_svc/api/trades.py
from fastapi import APIRouter, Request

from hwhkit.core.contracts import Cache, MessageBus, RelationalDb
from trading_svc.services.portfolio import PortfolioService

router = APIRouter(prefix="/trades")


@router.post("")
async def execute(symbol: str, qty: int, request: Request):
    ctx = request.app.state.ctx
    service = PortfolioService(
        db=ctx.resolve(RelationalDb),
        cache=ctx.resolve(Cache),
        bus=ctx.resolve(MessageBus),
    )
    user_id = request.state.user["sub"]   # set by AuthMiddleware
    return await service.execute_trade(user_id, symbol, qty)
```

## A scheduled job

```python
# trading_svc/jobs.py
from hwhkit.core.contracts import RelationalDb
from hwhkit.core.context import AppContext
from hwhkit.scheduler import scheduled_task


@scheduled_task(cron="0 17 * * 1-5", lock_key="eod-report")
async def end_of_day_report(ctx: AppContext) -> None:
    """Daily 17:00 weekday — only one replica runs."""
    db = ctx.resolve(RelationalDb)
    async with db.session() as s:
        ...
```

`lock_key` ensures multi-replica deployment doesn't double-fire — Redis
DistributedLock guards the execution.

## Unit-testing the service

```python
import pytest
from hwhkit.testing.fakes import FakeCache, FakeMessageBus, FakeRelationalDb

from trading_svc.services.portfolio import PortfolioService


@pytest.mark.asyncio
async def test_execute_trade_publishes_event():
    bus = FakeMessageBus()
    svc = PortfolioService(
        db=FakeRelationalDb(),
        cache=FakeCache(),
        bus=bus,
    )
    # ... arrange schema in db ...
    await svc.execute_trade(user_id=1, symbol="AAPL", qty=10)
    # assert bus saw the event
```

No Docker, no Postgres, no NATS — just contracts. Integration tests
catch the real-adapter bugs separately.
