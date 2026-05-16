# W2 — Bootstrap + Web + Observability + Config Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development or executing-plans. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Turn W1's "static building blocks" into a runnable framework: `hwhkit.bootstrap()` can start a FastAPI app with config loading + lifecycle + standard endpoints + structured logging + optional OTel.

**Definition of done:** `tests/e2e/sample_app/` (a CRUD service with 0 integrations) starts via `bootstrap()`, responds to `/healthz`, `/readyz`, `/version`, `/metrics`, `/items` CRUD with `ApiResponse` envelope including trace_id, and OTel console exporter emits spans/metrics/logs when enabled.

**Architecture:**
- `hwhkit.config.*` loads layered config (env → yaml → dotenv → defaults).
- `hwhkit.observability.*` is a thin facade over OTel SDK, defaults disabled.
- `hwhkit.web.*` is the FastAPI integration: app factory + middleware stack + envelope + exception handlers + ASGI launcher.
- `hwhkit.core.bootstrap()` ties them together: config → observability → AppContext → integrations.setup() (parallel) → web.build_app() → return FastAPI app.
- `hwhkit.utils.*` migrated from old `infoman` code (hash/encryption/decorators/http/feishu) but rewritten clean.

**Tech Stack:** pydantic-settings, structlog, opentelemetry-sdk, FastAPI, granian, orjson, httpx, cryptography.

---

## File Structure

```
hwhkit/
├── core/
│   └── bootstrap.py              # bootstrap(name, version, integrations, routers, ...)
├── config/
│   ├── __init__.py
│   ├── base.py                   # Settings base + AppConfig
│   ├── sources.py                # env / yaml / dotenv loaders
│   └── schemas.py                # WebConfig / ObservabilityConfig (Pydantic models)
├── observability/
│   ├── __init__.py
│   ├── otel.py                   # setup_otel(config) → Tracer/Meter/LoggerProvider
│   ├── logging.py                # configure_logging() — structlog + trace_id injection
│   ├── tracing.py                # @traced decorator + span helpers
│   ├── metrics.py                # standard metrics registry
│   └── instrumentation.py        # auto_instrument(app) entry
├── web/
│   ├── __init__.py
│   ├── app.py                    # build_app(ctx, routers, integrations)
│   ├── responses.py              # ApiResponse[T], PageResponse[T], @raw_response
│   ├── exceptions.py             # register_exception_handlers(app)
│   ├── system_router.py          # /healthz /readyz /version /metrics
│   ├── server.py                 # run(app, server="granian", ...) + main() CLI
│   └── middleware/
│       ├── __init__.py
│       ├── request_id.py         # RequestIDMiddleware
│       ├── logging.py            # LoggingMiddleware
│       ├── metrics.py            # MetricsMiddleware (OTel histogram)
│       └── auth.py               # AuthMiddleware (uses W1 JwtVerifier)
└── utils/
    ├── __init__.py
    ├── hash.py                   # sha256_hex(...), bcrypt helpers
    ├── encryption.py             # AES-GCM encrypt/decrypt
    ├── decorators.py             # @retry, @timed, @safe_execute
    ├── http.py                   # async HTTP client wrapper (httpx-based)
    └── notification/
        ├── __init__.py
        └── feishu.py             # FeishuNotifier (Notifier contract)
tests/
├── unit/{config,observability,web,utils}/...
└── e2e/sample_app/
    ├── __init__.py
    ├── main.py                   # uses bootstrap(), defines /items router
    └── test_smoke.py             # boots app + httpx hits / verifies envelope
```

---

## Task 1: `hwhkit.config.base` — Settings base (TDD)

**Files:** `hwhkit/config/{__init__.py,base.py,schemas.py}`, `tests/unit/config/test_base.py`

- [ ] **Step 1.1:** Write failing tests for `Settings`, `AppConfig`, `WebConfig`, `ObservabilityConfig`.
- [ ] **Step 1.2:** Implement `base.py` (Settings inherits pydantic-settings) + `schemas.py` (config models for each subsystem).
- [ ] **Step 1.3:** Run tests, commit.

## Task 2: `hwhkit.config.sources` — env/yaml/dotenv loaders (TDD)

**Files:** `hwhkit/config/sources.py`, `tests/unit/config/test_sources.py`

- [ ] Tests cover: env-only, yaml-only, dotenv-only, layered precedence (env > yaml > dotenv > defaults).
- [ ] Commit.

## Task 3: `hwhkit.observability.logging` — structlog + trace injection (TDD)

**Files:** `hwhkit/observability/{__init__.py,logging.py}`, `tests/unit/observability/test_logging.py`

- [ ] `configure_logging(level, json_mode)` sets up structlog processors with trace_id/span_id from OTel context.
- [ ] `get_logger(name)` returns bound logger.
- [ ] Tests: log capture verifies JSON shape + trace_id field when OTel context active (use OtelRecorder context manager).
- [ ] Commit.

## Task 4: `hwhkit.observability.otel` — SDK init (TDD)

**Files:** `hwhkit/observability/otel.py`, `tests/unit/observability/test_otel.py`

- [ ] `setup_otel(config)` returns `(Tracer, Meter, LoggerProvider)`. Returns no-op when disabled.
- [ ] Supports exporters: `otlp_http`, `otlp_grpc`, `console`, `none`.
- [ ] Tests: disabled mode is no-op; console exporter creates valid spans.
- [ ] Commit.

## Task 5: `hwhkit.observability.{tracing,metrics,instrumentation}` (TDD)

**Files:** corresponding modules + tests.

- [ ] `tracing.py`: `@traced(name)` decorator wraps function in span; `span(name)` context manager.
- [ ] `metrics.py`: provides shared meter; declares standard `http.server.*` / `db.client.*` histograms.
- [ ] `instrumentation.py`: `auto_instrument(app, integrations)` opt-in FastAPI / SQLAlchemy / Redis / httpx auto-instrumentation. No-op when those libs not installed.
- [ ] Commit.

## Task 6: `hwhkit.web.responses` — ApiResponse[T] + PageResponse[T] (TDD)

**Files:** `hwhkit/web/__init__.py`, `hwhkit/web/responses.py`, `tests/unit/web/test_responses.py`

- [ ] `ApiResponse[T]`: pydantic generic with `code: int = 0, message: str = "ok", data: Optional[T] = None, trace_id: Optional[str] = None`.
- [ ] `PageResponse[T]`: `items: list[T], total, page, page_size, has_next`.
- [ ] `@raw_response` decorator marks a route as opt-out (no envelope).
- [ ] Tests: ApiResponse JSON shape; raw_response marker readable from route.
- [ ] Commit.

## Task 7: `hwhkit.web.exceptions` — exception handlers (TDD)

**Files:** `hwhkit/web/exceptions.py`, `tests/unit/web/test_exceptions.py`

- [ ] `register_exception_handlers(app)` registers handlers for:
  - `ApiError` → status + ApiResponse with code/message/details/trace_id
  - `RequestValidationError` → 422 + `code=100422`
  - `HTTPException` → wrap in envelope
  - `Exception` (catch-all) → 500 + `code=500000`, log full traceback, never leak to client
- [ ] Tests: each handler produces correct response shape; trace_id from current OTel span injected.
- [ ] Commit.

## Task 8: Middleware: RequestID + Logging + Metrics + Auth (TDD)

**Files:** `hwhkit/web/middleware/{__init__,request_id,logging,metrics,auth}.py`, `tests/unit/web/middleware/test_*.py`

- [ ] `RequestIDMiddleware`: reads `X-Request-ID` header or generates uuid; sets in OTel baggage + response header.
- [ ] `LoggingMiddleware`: emits structured log per request (method, path template, status, duration, request_id). Skip noisy paths (/healthz /readyz /metrics).
- [ ] `MetricsMiddleware`: records `http.server.request.duration` histogram with labels (method, route, status_code).
- [ ] `AuthMiddleware`: optional; if JwtVerifier configured, validates Bearer token and injects `request.state.user`. Routes can opt-out via `@public_endpoint` marker.
- [ ] Tests via FastAPI TestClient.
- [ ] Commit.

## Task 9: `hwhkit.web.system_router` — /healthz /readyz /version /metrics (TDD)

**Files:** `hwhkit/web/system_router.py`, `tests/unit/web/test_system_router.py`

- [ ] `make_system_router(ctx, *, enable_metrics: bool)` returns APIRouter.
  - `/healthz` → liveness, always 200 if process alive, body `{"ok": true}`.
  - `/readyz` → readiness, aggregates `ctx.integrations[*].health_check()` via HealthAggregator. 503 if any unhealthy.
  - `/version` → `{"name", "version", "build", "git_sha"}` from ctx.config.app.
  - `/metrics` → Prometheus-compat endpoint if `observability.prometheus_compat.enabled`; else 404.
- [ ] Tests via TestClient.
- [ ] Commit.

## Task 10: `hwhkit.web.app.build_app()` (TDD)

**Files:** `hwhkit/web/app.py`, `tests/unit/web/test_app.py`

- [ ] `build_app(ctx, routers, integrations)`:
  1. Create FastAPI(title from ctx.config.app, docs_url conditional, lifespan handler that drives integration setup/shutdown).
  2. `app.state.ctx = ctx`.
  3. Register exception handlers.
  4. Add middleware in order: GZip → CORS → RequestID → Logging → Metrics → AuthMiddleware (last so it sees request_id).
  5. Add system router.
  6. Add business routers passed in.
  7. Add per-integration routers/middleware/dependencies (if exposed and `web.admin_routes_enabled`).
  8. Return app.
- [ ] Tests: app boots with 0 routers, /healthz works; with integrations registered, /readyz aggregates correctly.
- [ ] Commit.

## Task 11: `hwhkit.core.bootstrap()` (TDD)

**Files:** `hwhkit/core/bootstrap.py`, `tests/unit/core/test_bootstrap.py`

- [ ] Function signature:
  ```python
  async def bootstrap(
      *,
      name: str,
      version: str,
      integrations: list[IntegrationProvider] | None = None,
      routers: list[APIRouter] | None = None,
      on_startup: list[Callable[[AppContext], Awaitable[None]]] | None = None,
      on_shutdown: list[Callable[[AppContext], Awaitable[None]]] | None = None,
      config_overrides: dict | None = None,
  ) -> FastAPI: ...
  ```
- [ ] Implements spec § 2.3 9-step pipeline:
  1. Load config (with config_overrides applied last for testability).
  2. setup_otel(config.observability) — returns no-op if disabled.
  3. configure_logging(config.observability).
  4. Create AppContext.
  5. Parallel integration.setup(ctx) via asyncio.gather; any failure → reverse-shutdown started ones + raise.
  6. Register signal handlers (SIGTERM/SIGINT → run GracefulShutdown).
  7. Run user on_startup callbacks.
  8. build_app(ctx, routers, integrations).
  9. Return app.
- [ ] Test bootstrap with 0 integrations: returns app, /healthz works.
- [ ] Test bootstrap with 2 fake integrations: both setup called concurrently, /readyz aggregates.
- [ ] Test bootstrap with 1 failing integration: clean reverse shutdown + exception propagates.
- [ ] Commit.

## Task 12: `hwhkit.web.server` — granian/uvicorn launcher + `hwhkit-serve` CLI (TDD)

**Files:** `hwhkit/web/server.py`, `tests/unit/web/test_server.py`

- [ ] `run(app, *, server="granian", host=None, port=None, workers=None, **kwargs)` dispatches to granian/uvicorn/gunicorn.
- [ ] `main()` is the `hwhkit-serve` CLI entry: parses `--app module:attr --server X --port N --workers W` and calls `run`.
- [ ] Tests: `main(["--help"])` exits 0; granian/uvicorn import errors gracefully (missing extra prompts user to install).
- [ ] Commit.

## Task 13: `hwhkit.utils.*` — migrated utilities (TDD)

**Files:** `hwhkit/utils/{__init__,hash,encryption,decorators,http}.py`, tests.

- [ ] `hash.py`: `sha256_hex(data: bytes|str) -> str`, `bcrypt_hash/verify(password, hash)`.
- [ ] `encryption.py`: AES-GCM `encrypt(key: bytes, plaintext: bytes) -> bytes` (nonce prefixed), `decrypt(key: bytes, blob: bytes) -> bytes`.
- [ ] `decorators.py`: `@retry(attempts, exceptions, backoff)`, `@timed(metric)`, `@safe_execute(default)`.
- [ ] `http.py`: thin async httpx wrapper with sane defaults (timeout=10s, retries=3, OTel auto-instrumentation hook).
- [ ] Commit per file, each TDD.

## Task 14: `hwhkit.utils.notification.feishu` — FeishuNotifier (TDD)

**Files:** `hwhkit/utils/notification/{__init__,feishu}.py`, `tests/unit/utils/test_feishu.py`

- [ ] `FeishuNotifier(webhook_url, secret=None)` implements `Notifier` contract.
- [ ] `notify(title, body, severity, target)` posts JSON to Feishu webhook.
- [ ] Use `respx` to mock HTTP; verify payload shape (Lark card format).
- [ ] Sign request if `secret` provided (Feishu HMAC-SHA256 timestamp scheme).
- [ ] Commit.

## Task 15: E2E sample_app + smoke test

**Files:** `tests/e2e/sample_app/{__init__,main}.py`, `tests/e2e/test_smoke.py`

- [ ] `sample_app/main.py` uses `bootstrap(name="sample", version="0.0.1", routers=[items_router])`.
- [ ] Routes:
  - `GET /items/{id}` → `ApiResponse[Item]` from in-memory dict.
  - `POST /items` → 201 + `ApiResponse[Item]`.
- [ ] `test_smoke.py` uses `httpx.AsyncClient` against `app` (no real server):
  - GET /healthz → 200 `{"ok": true}`.
  - GET /readyz → 200 (no integrations to fail).
  - GET /version → 200 + name=sample.
  - POST /items + GET /items/{id} → roundtrip via envelope.
  - GET /missing → 404 + `code=100404` envelope.
  - Force exception in route → 500 + `code=500000` + no traceback leak.
- [ ] All e2e tests have `@pytest.mark.e2e`.
- [ ] Commit.

## Task 16: Update public API + CHANGELOG + W2 acceptance

- [ ] Update `hwhkit/__init__.py` to re-export `bootstrap`, `ApiResponse`, `PageResponse`, `get_logger`.
- [ ] Update `hwhkit/core/__init__.py` to export `bootstrap`.
- [ ] CHANGELOG.md `[Unreleased]` adds W2 entries.
- [ ] `make test test-cov lint typecheck docs` all green.
- [ ] Coverage target: hwhkit.core ≥95%, hwhkit.web ≥90%, hwhkit.observability ≥85%, overall ≥85%.
- [ ] Master TODO W2 section checkbox.
- [ ] Push to origin.
- [ ] Commit.

---

## W2 Definition of Done

- ✅ `tests/e2e/sample_app/` smoke tests all pass against TestClient.
- ✅ `bootstrap()` round-trip with 0 / N integrations works.
- ✅ ApiResponse envelope + 6-digit error codes wired through every response.
- ✅ Logs include `trace_id` when OTel enabled.
- ✅ `/healthz` + `/readyz` + `/version` + `/metrics` all behave per spec § 2.3 step 6.
- ✅ `hwhkit-serve --app tests.e2e.sample_app.main:app` starts a real granian server (manual smoke).
- ✅ FeishuNotifier respx tests pass.
- ✅ CI green on push.

---

## Self-Review Notes

**Spec coverage:**
- § 2.3 bootstrap flow — Task 11
- § 2.4 接合点(Depends / ctx.state / decorator) — Task 8-10 (Depends + state); decorators land W4 (@scheduled_task) / W5 (@nats_subscriber)
- § 3.1 build_app factory — Task 10
- § 3.2 信封 — Task 6
- § 3.3 错误码 + 异常处理 — Task 7
- § 3.4 标准中间件 — Task 8
- § 3.5 服务器启动器 — Task 12
- § 4.1-4.7 OTel — Tasks 3, 4, 5
- § 5 contracts — already done in W1; W2 wires `LogEmitter` / `Tracer` / `Meter` contracts via observability module

**Type consistency:**
- `bootstrap()` returns `FastAPI`, matches Task 10 / spec § 2.3.
- `ApiResponse[T]` field names match across responses.py / exceptions.py.
- `HealthAggregator` (from W1) used in system_router.py readyz.
- `RequestIDMiddleware` adds to baggage; `LoggingMiddleware` reads it; `MetricsMiddleware` adds labels using it.

**Placeholders:** none.

---

*End of W2 plan.*
