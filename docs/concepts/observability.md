# Observability

hwhkit speaks OpenTelemetry natively. Logs / metrics / traces all flow
through OTel; you point at any OTLP-compatible collector (Jaeger, Tempo,
SigNoz, Datadog Agent, Honeycomb refinery, …).

**Default: disabled.** Zero overhead until you flip
`observability.enabled = true`.

## Enable

`.env` or environment:

```bash
HWHKIT_OBSERVABILITY__ENABLED=true
HWHKIT_OBSERVABILITY__EXPORTER=otlp_http
HWHKIT_OBSERVABILITY__ENDPOINT=http://otel-collector:4318
```

Or `config.yaml`:

```yaml
observability:
  enabled: true
  exporter: otlp_http
  endpoint: http://otel-collector:4318
  sampler:
    type: parent_based_ratio
    ratio: 0.1
```

Now every HTTP request emits a span; SQLAlchemy / asyncpg / redis / httpx
calls are auto-instrumented; logs include `trace_id` + `span_id`.

## Standard metrics

Once enabled, you automatically get:

- `http.server.request.duration` (Histogram, ms)
- `http.server.active_requests` (UpDownCounter)
- `db.client.operation.duration` (Histogram)
- `redis.command.duration` (Histogram)
- `messaging.publish.duration` / `messaging.consume.duration`
- `scheduler.job.duration`

## Custom metrics

```python
from hwhkit.observability.metrics import get_meter

meter = get_meter()
trades = meter.create_counter("trading.trades.executed", unit="1")

@router.post("/trade")
async def trade(...):
    ...
    trades.add(1, {"symbol": symbol, "side": side})
```

## Custom spans

```python
from hwhkit.observability.tracing import span, traced

@traced("portfolio.rebalance")
async def rebalance(user_id: int) -> None:
    with span("fetch.positions", user_id=user_id):
        ...
    with span("compute.targets"):
        ...
```

## Logs

```python
from hwhkit.observability.logging import get_logger

log = get_logger(__name__)

@router.post("/trade")
async def trade(symbol: str):
    log.info("trade_received", symbol=symbol)  # JSON to stdout
    ...
```

When OTel is active, every log line gets `trace_id` and `span_id`
fields automatically — you can pivot from a slow trace in Jaeger to its
log lines in seconds.

## Sampling

Default is `parent_based_ratio` at `0.1` (10% of root requests sampled).
For dev: bump to `1.0`. For prod with high QPS: collector-side tail
sampling is the recommended pattern (sample errors / slow requests
always, drop the rest).

Health-check paths (`/healthz`, `/readyz`, `/metrics`, `/version`) are
unconditionally excluded from instrumentation to keep traces clean.
