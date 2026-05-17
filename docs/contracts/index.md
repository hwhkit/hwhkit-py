# Contracts reference

All contracts live in `hwhkit.core.contracts.*` as `typing.Protocol`s.

| Contract | Module | Built-in adapter |
|---|---|---|
| `Cache` | `hwhkit.core.contracts.cache` | Redis |
| `KvStore` | `hwhkit.core.contracts.kv_store` | Redis |
| `DistributedLock` | `hwhkit.core.contracts.lock` | Redis |
| `RelationalDb` | `hwhkit.core.contracts.relational_db` | Postgres |
| `MessageBus` | `hwhkit.core.contracts.message_bus` | NATS, Redis (pub/sub) |
| `ObjectStore` | `hwhkit.core.contracts.object_store` | S3, OSS (P2) |
| `VectorStore` | `hwhkit.core.contracts.vector_store` | Qdrant (P2) |
| `Scheduler` | `hwhkit.core.contracts.scheduler` | APScheduler |
| `LlmClient` | `hwhkit.core.contracts.llm` | litellm |
| `EmbeddingClient` | `hwhkit.core.contracts.llm` | litellm |
| `Notifier` | `hwhkit.core.contracts.notifier` | Feishu webhook |
| `SecretsProvider` | `hwhkit.core.contracts.secrets` | (env-var default) |
| `Telemetry` (Tracer/Meter/LogEmitter) | `hwhkit.core.contracts.telemetry` | OTel SDK |

All are `@runtime_checkable` — `isinstance(provider, Cache)` works.

## Method signatures

See the module docstrings in source; they're the canonical reference.
Key principles:

- **Async by default.** Every IO method is `async def`.
- **Bytes by default.** `Cache.get` / `Cache.set` are `bytes`-typed; encoding
  is the caller's choice. Helpers like `TypedCache[T]` add codec on top.
- **Timeouts via `timedelta`.** No raw seconds or milliseconds.
- **Token-based locks.** `DistributedLock.acquire` returns an opaque
  `LockToken` you must pass to `release` / `extend`. This is what makes
  the wrong-token-can't-unlock guarantee possible.
- **Acks are explicit.** `MessageBus` consumers can opt into `manual_ack`
  for durable adapters.

## Why protocols, not ABCs?

`typing.Protocol` allows **structural typing**. An adapter doesn't have
to inherit `Cache` to satisfy it — defining the right methods is enough.
This makes wrapping third-party libraries trivial.

`IntegrationProvider` IS an ABC (you must inherit and implement abstract
methods), but the contracts the Provider claims to satisfy are protocols.

## Adding a new contract

Process:

1. Add a `Protocol` to `hwhkit/core/contracts/<name>.py`. Mark
   `@runtime_checkable`.
2. Export from `hwhkit/core/contracts/__init__.py`.
3. Write a reusable test suite in
   `hwhkit/testing/contract_tests/<name>.py`.
4. Write `FakeXxx` in `hwhkit/testing/fakes/<name>.py`. It must pass the
   contract test suite.
5. At least one real adapter should declare `implements = [YourContract]`.

The contract test suite is the spec — if a future adapter passes it,
business code that depends on the contract is guaranteed to work.
