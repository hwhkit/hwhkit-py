# IntegrationProvider

An **IntegrationProvider** is the framework-managed wrapper around any
external dependency: a Postgres connection pool, a Redis client, a NATS
JetStream context, an LLM client, etc.

It is a single ABC with five required methods (three of them abstract):

```python
class IntegrationProvider(ABC):
    name: ClassVar[str]                      # globally-unique short id
    config_schema: ClassVar[type[BaseModel]]  # pydantic config model
    implements: ClassVar[list[type]] = []     # contract protocols satisfied

    @abstractmethod
    async def setup(self, ctx: AppContext) -> None: ...

    @abstractmethod
    async def health_check(self) -> HealthStatus: ...

    @abstractmethod
    async def shutdown(self) -> None: ...

    def fastapi_router(self) -> APIRouter | None: ...
    def fastapi_middlewares(self) -> list[Any]: ...
    def fastapi_dependencies(self) -> dict[str, Any]: ...
```

## Lifecycle

1. `bootstrap()` registers your providers on the `AppContext`.
2. It calls every `setup(ctx)` concurrently via `asyncio.gather`.
3. If any `setup()` raises, framework reverse-runs `shutdown()` on the
   ones that already finished, then propagates the exception. No half-up
   service.
4. `health_check()` is called by `/readyz`. Aim for <100 ms (a single
   round-trip to your dependency).
5. On `SIGTERM` / `SIGINT`, framework runs `shutdown()` in LIFO order.

## Adding a Provider to your app

```python
from hwhkit import bootstrap
from hwhkit.integrations.postgres import PostgresProvider

app = bootstrap(
    name="trading",
    version="1.0.0",
    integrations=[PostgresProvider()],
)
```

## Writing your own Provider

Most users only consume the built-in providers, but writing your own is
intentionally easy — there's no plugin system to learn:

```python
from hwhkit.core.integration import IntegrationProvider
from hwhkit.core.health import HealthStatus
from pydantic import BaseModel


class MyServiceConfig(BaseModel):
    url: str = "http://myservice.local"


class MyServiceProvider(IntegrationProvider):
    name = "myservice"
    config_schema = MyServiceConfig

    def __init__(self, config: MyServiceConfig | None = None) -> None:
        self._client = None
        self._config = config

    async def setup(self, ctx) -> None:
        cfg = self._config or ctx.config.myservice
        self._client = await connect(cfg.url)

    async def health_check(self) -> HealthStatus:
        ok = await self._client.ping()
        return HealthStatus.ok() if ok else HealthStatus.fail("unreachable")

    async def shutdown(self) -> None:
        if self._client:
            await self._client.close()
```

## Why this abstraction?

Two reasons:

- **Uniform lifecycle.** Every dependency is set up the same way, surfaces
  health the same way, shuts down the same way. No bespoke `__init__` /
  `connect` / `close` patterns scattered across your codebase.
- **Contract binding.** When a Provider declares `implements = [Cache]`,
  business code can ask `ctx.resolve(Cache)` and get back whatever Provider
  is implementing it — swap the adapter, business code unchanged.

See [Contracts & Adapters](contracts.md).
