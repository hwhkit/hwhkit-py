# AppContext

`AppContext` is the framework's runtime container. It holds:

- All registered integrations
- Contract → Provider bindings
- The loaded `Settings` instance
- (Implicit) the OTel tracer/meter via global providers

Business code reaches integrations through `AppContext`.

## Where to get it

Inside a FastAPI route:

```python
from fastapi import Request

@router.get("/items/{id}")
async def get_item(id: int, request: Request):
    ctx = request.app.state.ctx
    ...
```

In a `bootstrap()` `on_startup` hook:

```python
async def register_jobs(ctx: AppContext) -> None:
    scheduler = ctx.get_typed(SchedulerProvider)
    scheduler.add_cron_job("hourly", "0 * * * *", ...)

app = bootstrap(..., on_startup=[register_jobs])
```

In a `@scheduled_task` callback (W4 scheduler):

```python
from hwhkit.scheduler import scheduled_task

@scheduled_task(cron="0 * * * *", lock_key="my-job")
async def my_job(ctx: AppContext) -> None:
    db = ctx.resolve(RelationalDb)
    ...
```

## Three lookup styles

### 1. By contract — preferred

```python
from hwhkit.core.contracts import Cache, MessageBus

cache = ctx.resolve(Cache)
bus = ctx.resolve(MessageBus)
```

Business code stays contract-bound; adapter is invisible.

### 2. By name — for dynamic scenarios

```python
provider = ctx.get("postgres")
```

Use when you don't know the type at compile time (rare).

### 3. By concrete type — escape hatch

```python
from hwhkit.integrations.postgres import PostgresProvider

pg = ctx.get_typed(PostgresProvider)
async with pg.engine.connect() as conn:
    ...
```

Use when you need adapter-specific features (SQLAlchemy's `engine`,
NATS's `js`, etc.).

## Explicit binding

If two adapters implement the same contract:

```python
# Both implement MessageBus
app = bootstrap(integrations=[RedisProvider(), NatsProvider()])

# In bootstrap on_startup:
async def bind_bus(ctx: AppContext) -> None:
    ctx.bind_contract(MessageBus, "nats")  # canonical bus
```

Now `ctx.resolve(MessageBus)` returns the NATS Provider; Redis remains
available for its other contracts (Cache, KvStore, …).
