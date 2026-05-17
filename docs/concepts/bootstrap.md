# Bootstrap

`hwhkit.bootstrap()` is the single entry point. It loads configuration, wires
observability, sets up integrations, and returns a ready-to-serve FastAPI app.

## Minimal example

```python
from hwhkit import bootstrap

app = bootstrap(name="my-service", version="0.1.0")

if __name__ == "__main__":
    from hwhkit.web.server import run
    run(app, server="uvicorn")
```

That gives you `/healthz`, `/readyz`, `/version`, plus the
`ApiResponse` envelope and exception handlers on every route. No
integrations, no telemetry — just the framework's spine.

## With integrations

```python
from hwhkit import bootstrap
from hwhkit.integrations.postgres import PostgresProvider
from hwhkit.integrations.redis import RedisProvider

from my_service.api import api_router

app = bootstrap(
    name="my-service",
    version="0.1.0",
    integrations=[
        PostgresProvider(),
        RedisProvider(),
    ],
    routers=[api_router],
)
```

`bootstrap()` calls each integration's `setup()` concurrently, fails
fast on any error (reverse-shutting-down the ones that succeeded), then
mounts the FastAPI app.

## The 9-step pipeline

Spec § 2.3 documents what `bootstrap()` does internally:

1. Load config (env → yaml → dotenv → defaults)
2. `setup_otel(config.observability)` — no-op if disabled
3. `configure_logging(...)`
4. Create `AppContext` and register integrations
5. `asyncio.gather(integ.setup(ctx) for integ in integrations)`
6. `build_app(ctx, routers, integrations, on_startup, on_shutdown)`
7. Auto-instrument FastAPI / SQLAlchemy / Redis / httpx (best-effort)
8. Install signal handlers for graceful shutdown
9. Return the FastAPI app

## Signature

```python
def bootstrap(
    *,
    name: str,
    version: str,
    integrations: list[IntegrationProvider] | None = None,
    routers: list[APIRouter] | None = None,
    on_startup: list[LifecycleHook] | None = None,
    on_shutdown: list[LifecycleHook] | None = None,
    config_overrides: dict[str, Any] | None = None,
    settings_cls: type[Settings] | None = None,
) -> FastAPI:
    ...
```

- `name` / `version` populate `/version` and the OTel resource attributes.
- `routers` are mounted under `/` (you wire prefixes yourself).
- `on_startup` / `on_shutdown` hooks receive the `AppContext` and run inside the FastAPI lifespan.
- `config_overrides` is mainly a testing hook — see [Testing](testing.md).
- `settings_cls` lets your project extend `hwhkit.config.base.Settings` to add integration-specific config sections.

## Async variant

If your top-level code is already running inside an asyncio loop, use
`bootstrap_async()`. Same arguments, returns the same FastAPI app, no
nested-loop trickery.
