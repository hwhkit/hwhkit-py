# Redis

`hwhkit.integrations.redis.RedisProvider` implements four contracts from a
single redis.asyncio connection pool: **Cache**, **KvStore**,
**DistributedLock**, and **MessageBus** (pub/sub mode).

## Install

```bash
hwhkit add redis
```

## Configuration

```bash
HWHKIT_REDIS__URL=redis://localhost:6379/0
HWHKIT_REDIS__MAX_CONNECTIONS=20
HWHKIT_REDIS__SOCKET_TIMEOUT=5.0
```

For TLS, use `rediss://` scheme.

## As a Cache

```python
from datetime import timedelta
from hwhkit.core.contracts import Cache

cache: Cache = ctx.resolve(Cache)

await cache.set("session:abc", b"...", ttl=timedelta(minutes=30))
data = await cache.get("session:abc")
```

For typed values use `TypedCache`:

```python
from hwhkit.core.contracts.cache import TypedCache, JsonCodec

users: TypedCache[dict] = TypedCache(cache, codec=JsonCodec())
await users.set("u:1", {"name": "alice"})
```

## As a DistributedLock

```python
from datetime import timedelta
from hwhkit.core.contracts import DistributedLock

lock: DistributedLock = ctx.resolve(DistributedLock)

token = await lock.acquire("process-batch", ttl=timedelta(minutes=5), blocking=False)
if token:
    try:
        ...
    finally:
        await lock.release(token)
```

Implementation uses Redis `SET NX EX` + Lua-scripted compare-and-delete on
release — only the holder can unlock (the wrong-token-release test is in
the contract suite).

## As a MessageBus (pub/sub)

```python
from hwhkit.core.contracts import MessageBus

bus: MessageBus = ctx.resolve(MessageBus)

async def on_event(msg):
    print(msg.subject, msg.payload)

sub = await bus.subscribe("trades.executed", on_event)
await bus.publish("trades.executed", b'{"id":1}')
```

!!! note "Pub/Sub vs JetStream"
    Redis pub/sub is **fire-and-forget**: subscribers offline at publish
    time miss the message. For durable + at-least-once semantics, use
    [NATS](nats.md) instead — `NatsProvider` also implements `MessageBus`.

## Direct client access

```python
from hwhkit.integrations.redis import RedisProvider

r = ctx.get_typed(RedisProvider).client
# r is the underlying redis.asyncio.Redis instance — use for Lua scripts,
# Redis Streams, geo commands, etc.
```

## Testing

`FakeCache` / `FakeDistributedLock` / `FakeMessageBus` for unit tests;
real Redis container via testcontainers for integration tests.
