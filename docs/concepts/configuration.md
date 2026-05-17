# Configuration

Built on `pydantic-settings`. Sources layered, with later-source winning:

1. Defaults declared on the `Settings` subclass
2. `.env` file
3. `config.yaml` (path from `$HWHKIT_CONFIG` env var, defaults to `./config.yaml`)
4. Environment variables (prefix `HWHKIT_`, nested delimiter `__`)
5. Programmatic overrides (passed to `bootstrap(config_overrides=...)`)

## Built-in sections

`Settings` ships with three sections every service has:

```python
class Settings(BaseSettings):
    app: AppConfig               # name, version, environment, description
    web: WebConfig               # host, port, server, CORS, docs_url, ...
    observability: ObservabilityConfig  # OTel exporter, sampler, log level
```

## Per-integration sections

Each integration declares its own pydantic model. Add them to your project's
`Settings` subclass:

```python
from hwhkit.config.base import Settings
from hwhkit.integrations.postgres import PostgresConfig
from hwhkit.integrations.redis import RedisConfig


class AppSettings(Settings):
    postgres: PostgresConfig = PostgresConfig()
    redis: RedisConfig = RedisConfig()


app = bootstrap(
    name="my-service",
    version="0.1.0",
    settings_cls=AppSettings,
    integrations=[PostgresProvider(), RedisProvider()],
)
```

## Reading config in business code

```python
from fastapi import Request

@router.get("/info")
async def info(request: Request):
    cfg = request.app.state.ctx.config
    return {"environment": cfg.app.environment}
```

## Environment-variable mapping

`Settings` uses `env_prefix = "HWHKIT_"` and `env_nested_delimiter = "__"`:

```bash
HWHKIT_APP__NAME=trading-service
HWHKIT_WEB__PORT=9000
HWHKIT_OBSERVABILITY__ENABLED=true
HWHKIT_OBSERVABILITY__SAMPLER__RATIO=0.05
HWHKIT_POSTGRES__DSN=postgresql+asyncpg://user:pwd@host:5432/db
```

## YAML

```yaml
app:
  name: trading-service
  version: 1.2.3
  environment: prod

web:
  port: 9000

observability:
  enabled: true
  exporter: otlp_http
  endpoint: http://otel-collector:4318

postgres:
  dsn: postgresql+asyncpg://user:pwd@host:5432/db
  pool_size: 20
```

Loaded automatically if `config.yaml` exists in CWD, or set
`HWHKIT_CONFIG=/path/to/file.yaml`.

## Testing

`bootstrap(config_overrides={...})` injects test-only values bypassing
all other sources — handy in fixtures:

```python
app = bootstrap(
    name="test",
    version="0",
    config_overrides={"web": {"docs_enabled": False}},
)
```
