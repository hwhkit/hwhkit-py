# hwhkit

> Production-ready Python framework for trading services and microservices.

`hwhkit` is the Python sibling of
[hwhkit-rs](https://github.com/louishwh/hwhkit-rs) — same architectural
philosophy, idiomatic for each language.

**Status**: 🟡 **2.0.0-alpha.1** — first alpha of the greenfield rewrite.
Foundation + P0/P1 integrations + CLI + docs are complete. See the
[design doc](docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md)
and the [release checklist](docs/superpowers/RELEASE-CHECKLIST.md).

> **Note on the version jump (1.x → 2.0):** versions 1.0.0–1.0.21 on
> PyPI were an unrelated personal packaging tool by the same author.
> `2.0.0-alpha.1` is the first release of *this* framework on that
> namespace. There is no upgrade path from 1.x; the API is entirely new.

## What you get

- **Single `bootstrap()` call** — wire FastAPI + OpenTelemetry + integrations + lifespan + signal handling, get back a runnable ASGI app.
- **`Contracts` + `Adapters`** — business code depends on `Cache`/`MessageBus`/`RelationalDb` protocols; swap adapters without touching it.
- **Five P0/P1 integrations built-in** — Postgres (SQLAlchemy 2.0 async),
  Redis (cache / kvstore / distributed-lock / pub/sub), NATS (JetStream-durable MessageBus), APScheduler (with Redis-Redlock for multi-replica safety), LLM (litellm — OpenAI / Anthropic / DeepSeek / Ollama / ...).
- **`hwhkit init` + `hwhkit add`** — one command per integration, libcst-based codemod patches your `main.py` idempotently.
- **OpenTelemetry-native** — auto-instrumentation for FastAPI / SQLAlchemy / asyncpg / Redis / httpx; traces, metrics, logs through OTLP. Default disabled (zero overhead until enabled).
- **6-digit error code taxonomy** — `XYYZZZ` (e.g. `100404`, `510001`); ApiResponse envelope on every response with `trace_id`.
- **Industrial-grade testing** — `hwhkit.testing` ships in-memory fakes + reusable contract conformance test suites. The same tests prove FakeCache *and* RedisProvider.

## Quick start

```bash
pip install "hwhkit[web,postgres,redis,otel,cli]"
hwhkit init my-service && cd my-service
hwhkit add postgres redis
make dev
```

That gets you:

- A working FastAPI app with `/healthz`, `/readyz`, `/version`, `/metrics`.
- Postgres + Redis providers registered, health-checked via `/readyz`.
- `ApiResponse` envelope + 6-digit error codes on every endpoint.
- OpenTelemetry stack ready (set `HWHKIT_OBSERVABILITY__ENABLED=true`).
- `pyproject.toml` + Makefile + Dockerfile + docker-compose + tests scaffolded.

See [hwhkit.louishwh.tech](https://hwhkit.louishwh.tech) for full docs.

## Test pyramid

| Layer | Count | Status |
|---|---:|---|
| Unit | 299 | ✅ |
| Integration (testcontainers Postgres + Redis) | 29 | ✅ |
| E2E (sample app via TestClient) | 8 | ✅ |
| **Total** | **336** | **✅** |

Plus mypy `--strict` clean, ruff clean, mkdocs `--strict` clean.

## License

`MIT OR Apache-2.0` — choose either. Aligned with hwhkit-rs.

## Sibling projects

- [hwhkit-rs](https://github.com/louishwh/hwhkit-rs) — Rust, reference architecture.
- hwhkit-go — Go, planned rewrite.
