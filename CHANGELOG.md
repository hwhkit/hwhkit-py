# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (W3 — Postgres + Redis P0 Integrations)
- `hwhkit.integrations.postgres.PostgresProvider` (SQLAlchemy 2.0 async +
  asyncpg) implementing `RelationalDb` contract; `get_session()` Depends helper.
- `hwhkit.integrations.postgres.migrations` — alembic helpers (async-engine
  wired `run_migrations_online`, `run_migrations_offline`, env.py template).
- `hwhkit.integrations.redis.RedisProvider` (redis.asyncio) implementing
  Cache + KvStore + DistributedLock + MessageBus contracts. Lua SAFE_RELEASE/
  SAFE_EXTEND atomics for token-checked locks.
- `hwhkit.web.middleware.AuthMiddleware` — JWT Bearer auth with path-based
  exclusion (deferred from W2.11).
- `hwhkit.testing.fakes.FakeRelationalDb` (sqlite-memory) +
  `hwhkit.testing.contract_tests.relational_db.RelationalDbContractTests`.
- testcontainers fixtures (Postgres 16-alpine, Redis 7-alpine).
- 22 Redis + 4 Postgres integration tests; both providers pass relevant
  contract conformance suites.

### Added (W4 — Scheduler + NATS P0 Completion)
- `hwhkit.scheduler.SchedulerProvider` (APScheduler async) implementing
  `Scheduler` contract; optional distributed-lock wrap so multi-instance
  scheduler doesn't double-fire.
- `hwhkit.scheduler.@scheduled_task` decorator + `register_scheduled_tasks()`
  bootstrap hook.
- `hwhkit.integrations.nats.NatsProvider` (nats-py) implementing `MessageBus`
  with JetStream support (durable + at-least-once); falls back to core NATS
  pub/sub for ephemeral subscribers; request/reply via NATS core.
- `hwhkit.testing.fakes.FakeScheduler` for unit tests of scheduled-job logic.
- 252 unit tests + 29 integration tests pass. mypy strict + ruff clean.

### Deferred from W3/W4
- Benchmarks for Postgres / Redis / Scheduler / NATS (W3.8, W3.16, W4.4
  bench, W4.10 bench).
- Chaos tests via toxiproxy (W3.9, W4.4 chaos, W4.10 chaos).
  Both buckets land in W6 release-readiness phase.

### Added (W2 — Bootstrap + Web + Observability + Config + Utils)
- `hwhkit.config.*` — pydantic-settings based layered config (env > yaml > .env > defaults)
  with `Settings` base, `AppConfig` / `WebConfig` / `ObservabilityConfig` schemas.
- `hwhkit.observability.*` — full OTel three-pillar (default disabled):
  - `logging` (structlog + trace_id/span_id auto-inject)
  - `otel` SDK init (otlp_http / otlp_grpc / console / none exporters)
  - `tracing` (`@traced` decorator + `span()` ctxmgr)
  - `metrics` (lazy standard registry: 7 default histograms/counters)
  - `instrumentation` (FastAPI/SQLAlchemy/asyncpg/redis/httpx auto-instrument)
- `hwhkit.web.*` — FastAPI integration:
  - `ApiResponse[T]` / `PageResponse[T]` envelope + `@raw_response` opt-out
  - 4-tier exception handler stack (ApiError / Validation / HTTPException / catchall)
  - 3 middlewares: RequestID / Logging / Metrics
  - System router: /healthz / /readyz / /version / /metrics
  - `build_app()` factory with lifespan
  - `web.server.run()` + `hwhkit-serve` CLI (granian/uvicorn/gunicorn)
- `hwhkit.core.bootstrap()` / `bootstrap_async()` — 9-step pipeline
  (config → otel → logging → AppContext → parallel integration setup with
  reverse-shutdown → build_app → auto-instrument → return FastAPI app).
- `hwhkit.utils.*` — hash (SHA-256/HMAC/constant_time_compare/random_token),
  encryption (AES-256-GCM), decorators (@retry/@timed/@safe_execute), http
  (HttpClient wrapper).
- `hwhkit.utils.notification.feishu.FeishuNotifier` — Notifier contract impl,
  card-format + HMAC signing.
- E2E sample app at `tests/e2e/sample_app/main.py` + 8 smoke tests.
- 190 unit tests, 8 e2e tests, mypy --strict clean, ruff clean.

### Added (W1 — Foundation)
- Greenfield rewrite of hwhkit-py, mirroring hwhkit-rs architecture.
- `hwhkit.core.contracts.*` — all 12 protocol definitions (Cache, KvStore,
  DistributedLock, MessageBus, RelationalDb, ObjectStore, VectorStore,
  Scheduler, LlmClient/EmbeddingClient, SecretsProvider, Telemetry, Notifier).
- `hwhkit.core.integration.IntegrationProvider` ABC with implements[] for
  contract auto-binding.
- `hwhkit.core.context.AppContext` with name/type/contract resolution.
- `hwhkit.core.errors` with 6-digit XYYZZZ error code taxonomy.
- `hwhkit.core.health` — HealthStatus + HealthAggregator.
- `hwhkit.core.shutdown` — GracefulShutdown with LIFO + per-call timeout.
- `hwhkit.core.jwt` — JwksCache + JwtVerifier (hardened against alg:none).
- `hwhkit.testing.OtelRecorder` — in-memory Tracer/Meter/LogEmitter for tests.
- CI/CD pipeline (GitHub Actions): lint + typecheck + matrix test + build + security.
- pre-commit config (ruff, mypy --strict, gitleaks, conventional commits).
- mkdocs-material documentation site (smoke version) at hwhkit.louishwh.tech.
- Renovate config for weekly dependency updates.
- 68 unit tests, 89% coverage (core modules 95%+).

### Removed
- Legacy `infoman` code (see commit history).

## [0.4.0-alpha.1] - TBD
- Alpha 1 of the rewrite. Foundation only — integrations land in W3+.
