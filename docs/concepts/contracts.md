# Contracts & Adapters

hwhkit follows the **ports and adapters** pattern (also called
hexagonal architecture):

- **Contracts** (`hwhkit.core.contracts.*`) are `typing.Protocol`
  definitions. Business code imports from here only.
- **Adapters** (`hwhkit.integrations.*`) are concrete implementations.
  They live behind the contract.

Result: business code depends on `Cache`, not on `RedisProvider`. Swap the
adapter, code unchanged.

## The 12 contracts

| Contract | Methods | First adapter |
|---|---|---|
| `Cache` | get/set/delete/exists/incr/expire | Redis |
| `KvStore` | get/set/delete/list_keys/watch | Redis |
| `DistributedLock` | acquire/release/extend | Redis (Lua-safe) |
| `RelationalDb` | session/ping | Postgres |
| `MessageBus` | publish/subscribe/request | NATS (JetStream) |
| `ObjectStore` | put/get/stream/delete/presigned_url | S3 (W6 P2) |
| `VectorStore` | upsert/search | Qdrant (W6 P2) |
| `Scheduler` | add_cron/interval/oneshot | APScheduler |
| `LlmClient` | chat/chat_stream | litellm |
| `EmbeddingClient` | embed | litellm |
| `SecretsProvider` | get | env-var (default) |
| `Telemetry` | tracer/meter/log emitter | OTel SDK |
| `Notifier` | notify | Feishu webhook |

## Using a contract in business code

```python
from hwhkit.core.contracts import Cache, RelationalDb


class PortfolioService:
    def __init__(self, db: RelationalDb, cache: Cache) -> None:
        self.db = db
        self.cache = cache

    async def get_position(self, user_id: int, symbol: str) -> Position:
        if cached := await self.cache.get(f"pos:{user_id}:{symbol}"):
            return Position.from_bytes(cached)
        async with self.db.session() as s:
            ...
```

No imports from `hwhkit.integrations.*`. The service can be unit-tested with
`FakeCache` + `FakeRelationalDb` (see [Testing](testing.md)).

## Wiring contracts to adapters

`AppContext.resolve(Contract)` returns whichever Provider declares
`implements = [Contract]`:

```python
from hwhkit.integrations.postgres import PostgresProvider
from hwhkit.integrations.redis import RedisProvider

# bootstrap registers these:
app = bootstrap(integrations=[PostgresProvider(), RedisProvider()])

# inside a request:
@router.get("/positions/{symbol}")
async def handler(symbol: str, request: Request):
    ctx = request.app.state.ctx
    db = ctx.resolve(RelationalDb)        # → PostgresProvider
    cache = ctx.resolve(Cache)             # → RedisProvider
    service = PortfolioService(db, cache)
    return await service.get_position(user_id, symbol)
```

If multiple Providers implement the same contract (e.g. you registered
both Redis and Memcached as Cache), `resolve` raises `LookupError`. Use
`bind_contract(Cache, "redis")` to disambiguate.

## When to bypass a contract

For vendor-specific features (Postgres JSONB, NATS JetStream KV, Qdrant
filters), grab the underlying adapter directly:

```python
postgres = ctx.get_typed(PostgresProvider)
async with postgres.engine.connect() as conn:
    await conn.execute(text("SELECT * FROM t WHERE data @> '{\"x\": 1}'"))
```

Convention: name such code `*_pg_specific.py` (or `*_nats_specific.py` etc.)
so it's auditable when you ever want to swap adapters.
