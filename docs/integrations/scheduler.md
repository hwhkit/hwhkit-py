# Scheduler

`hwhkit.scheduler.SchedulerProvider` wraps APScheduler in async mode and
implements the `Scheduler` contract.

## Install

```bash
hwhkit add scheduler
```

## Configuration

```bash
HWHKIT_SCHEDULER__TIMEZONE=UTC
```

## Three ways to schedule

### 1. @scheduled_task decorator (preferred)

```python
from datetime import timedelta
from hwhkit.scheduler import scheduled_task
from hwhkit.core.context import AppContext


@scheduled_task(cron="0 */1 * * *", lock_key="hourly-aggregate")
async def hourly_aggregate(ctx: AppContext) -> None:
    db = ctx.resolve(RelationalDb)
    ...


@scheduled_task(interval=timedelta(seconds=30))
async def heartbeat(ctx: AppContext) -> None:
    log.info("alive")
```

Register them once in `bootstrap()`:

```python
from hwhkit.scheduler import register_scheduled_tasks

app = bootstrap(
    name="trading",
    version="1.0.0",
    integrations=[SchedulerProvider(), RedisProvider()],
    on_startup=[register_scheduled_tasks],
)
```

### 2. Programmatic

```python
scheduler = ctx.get_typed(SchedulerProvider)
scheduler.add_cron_job(
    "daily-report", "0 9 * * 1-5", send_report,
    lock_key="daily-report",
)
await scheduler.start()
```

### 3. One-shot

```python
from datetime import datetime
scheduler.add_oneshot_job("send-reminder", datetime(2026, 6, 1, 9, 0), my_func)
```

## Distributed-safe via `lock_key`

When you pass `lock_key`, the scheduler wraps the function with
`DistributedLock.acquire()` — only one instance across N replicas executes
each fire. If no `DistributedLock` Provider is registered, the wrap is a
no-op (with a warning log).

Pair with `RedisProvider` for production:

```python
app = bootstrap(integrations=[
    SchedulerProvider(),
    RedisProvider(),       # provides DistributedLock automatically
])
```

## Testing

```python
from hwhkit.testing.fakes import FakeScheduler

async def test_my_job_registers() -> None:
    sched = FakeScheduler()
    sched.add_cron_job("job", "0 * * * *", my_job, lock_key="k")
    assert "job" in sched.jobs
    await sched.run("job")  # manually trigger
```

## Health & lifecycle

`SchedulerProvider.health_check()` reports `running` + job count.
`shutdown()` stops the scheduler (jobs in flight finish naturally).
