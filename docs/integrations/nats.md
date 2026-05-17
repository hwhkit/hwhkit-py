# NATS

`hwhkit.integrations.nats.NatsProvider` implements `MessageBus` backed by
NATS / JetStream. Durable consumers when you pass `durable=`; ephemeral
core pub/sub otherwise. Request/reply via NATS core.

## Install

```bash
hwhkit add nats
```

## Configuration

```bash
HWHKIT_NATS__SERVERS=["nats://localhost:4222"]
HWHKIT_NATS__NAME=hwhkit
HWHKIT_NATS__MAX_RECONNECT_ATTEMPTS=60
HWHKIT_NATS__JETSTREAM_STORAGE=file        # or memory
HWHKIT_NATS__ENSURE_STREAM=TRADES          # auto-create on setup
HWHKIT_NATS__ENSURE_SUBJECTS=["trades.>"]
```

## Publish + Subscribe

```python
from hwhkit.core.contracts import MessageBus, Message

bus: MessageBus = ctx.resolve(MessageBus)

# Fire-and-forget pub/sub (ephemeral)
async def on_trade(msg: Message) -> None:
    print(msg.subject, msg.payload)

sub = await bus.subscribe("trades.executed", on_trade)
await bus.publish("trades.executed", b'{"id":1}')
```

## Durable JetStream consumers

```python
sub = await bus.subscribe(
    "trades.executed",
    on_trade,
    durable="trades-aggregator",   # persists offset; resumes on restart
    manual_ack=True,
    max_in_flight=100,
)
```

In the handler, call `await msg.ack()` after successful processing or
`await msg.nack()` to redeliver.

## Deduplication

```python
await bus.publish(
    "trades.executed",
    payload,
    deduplication_key=f"trade-{trade_id}",   # written as Nats-Msg-Id header
)
```

JetStream dedupes by `Nats-Msg-Id` within the stream's dedup window
(default 2 minutes — adjustable on the stream).

## Request/Reply

```python
response = await bus.request("pricing.query", b"AAPL", timeout=timedelta(seconds=2))
```

Subscribers respond via the standard NATS reply subject — see the NATS
docs for handler patterns.

## Direct JetStream access

```python
from hwhkit.integrations.nats import NatsProvider

nc = ctx.get_typed(NatsProvider)
js = nc.js   # JetStream context — use for KV stores, Object stores,
             # stream / consumer management.
```

## Testing

Unit tests: `FakeMessageBus` (in-memory queues). Integration tests
should spin a real `nats:2-alpine` container with JetStream enabled
(`-js` flag). Contract test suites apply.
