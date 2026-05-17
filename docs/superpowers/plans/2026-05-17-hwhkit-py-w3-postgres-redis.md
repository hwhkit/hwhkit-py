# W3 — Postgres + Redis Integration Week

> Use superpowers:executing-plans to drive this; W3 spans ~20 tasks across 5 layers.

**Goal:** Two P0 integrations land with complete testing pyramid: unit + contract
conformance + integration (testcontainers) + benchmark + chaos. Plus
`hwhkit.testing.fakes` populated so downstream services can write unit tests
against in-memory contract impls.

**Definition of done:** `make test test-integration test-cov` all green; Postgres
+ Redis adapters satisfy their declared contracts; coverage stays ≥85% (target
≥90% on hwhkit.integrations.*); contract test suites are reusable for future
adapters.

**Architecture:**
- `hwhkit.integrations.postgres.PostgresProvider` — SQLAlchemy 2.0 async,
  implements `RelationalDb` contract; lazy-imports SQLAlchemy/asyncpg.
- `hwhkit.integrations.redis.RedisProvider` — `redis.asyncio.Redis`, implements
  4 contracts: `Cache`, `KvStore`, `DistributedLock`, `MessageBus` (pub/sub).
- `hwhkit.testing.contract_tests.*` — abstract test classes; concrete suites
  inherit + bind a fixture for their adapter. Same tests run against the fake
  and the real adapter.
- `hwhkit.testing.fakes.*` — fully in-memory contract impls for business unit tests.
- `hwhkit.web.middleware.auth` — W2.11 deferred item, now lands using
  JwtVerifier + an optional Redis token-blacklist (opt-in).

**Tech:** SQLAlchemy[asyncio] 2.0, asyncpg, alembic, redis[hiredis] 7.x,
testcontainers[postgres,redis], pytest-benchmark, toxiproxy.

---

## File Structure (W3 additions)

```
hwhkit/
├── integrations/
│   ├── __init__.py
│   ├── postgres/
│   │   ├── __init__.py
│   │   ├── provider.py       # PostgresProvider (impls RelationalDb)
│   │   ├── session.py        # AsyncSession factory + Depends helper
│   │   ├── config.py         # PostgresConfig (Pydantic)
│   │   ├── migrations.py     # alembic helpers (env.py template + run_migrations)
│   │   └── repository.py     # OPT-IN Generic Repository base (see D2 — disabled by default; ship as helper, not enforced)
│   └── redis/
│       ├── __init__.py
│       ├── provider.py       # RedisProvider (impls Cache + KvStore + Lock + MessageBus)
│       ├── cache.py          # RedisCache impl detail
│       ├── lock.py           # Redlock-style single-node lock
│       ├── message_bus.py    # pub/sub MessageBus
│       └── config.py         # RedisConfig
├── testing/
│   ├── fakes/
│   │   ├── __init__.py
│   │   ├── cache.py             # FakeCache (in-memory + TTL via asyncio task)
│   │   ├── kv_store.py          # FakeKvStore
│   │   ├── lock.py              # FakeDistributedLock
│   │   ├── message_bus.py       # FakeMessageBus
│   │   └── relational_db.py     # FakeRelationalDb (sqlite-memory via SQLAlchemy)
│   └── contract_tests/
│       ├── __init__.py
│       ├── cache.py             # CacheContractTests abstract base
│       ├── kv_store.py
│       ├── lock.py
│       ├── message_bus.py
│       └── relational_db.py
└── web/middleware/
    └── auth.py                  # W2.11 deferred: JWT-based AuthMiddleware

tests/
├── unit/integrations/
│   ├── __init__.py
│   ├── postgres/test_provider.py
│   └── redis/{test_provider,test_lock,test_message_bus}.py
├── integration/
│   ├── conftest.py              # testcontainers session fixtures
│   ├── postgres/
│   │   ├── test_lifecycle.py
│   │   ├── test_session.py
│   │   ├── test_repository.py
│   │   └── test_contract_conformance.py  # inherits RelationalDb contract suite
│   └── redis/
│       ├── test_lifecycle.py
│       ├── test_cache.py
│       └── test_contract_conformance.py
├── benchmark/
│   ├── test_postgres.py    # session-acquire / simple CRUD p99
│   └── test_redis.py       # GET/SET/INCR p99
└── chaos/
    ├── test_postgres_disconnect.py
    └── test_redis_disconnect.py
```

---

## Tasks (high-level — each task is its own commit)

### Phase A: Foundation
- **A1:** `hwhkit.integrations.__init__` empty module + `tests/unit/integrations/__init__.py`
- **A2:** `PostgresConfig` + `RedisConfig` pydantic schemas (in `hwhkit/integrations/{postgres,redis}/config.py`)
- **A3:** `hwhkit.testing.contract_tests.cache.CacheContractTests` abstract — TDD-style;
  one test per contract method. (~ 15 tests)
- **A4:** Same for `kv_store` / `lock` / `message_bus` / `relational_db` contract test suites.

### Phase B: Fakes
- **B1:** `FakeCache` (in-memory + asyncio TTL task) — passes CacheContractTests via inheritance.
- **B2:** `FakeKvStore` — passes KvStoreContractTests.
- **B3:** `FakeDistributedLock` — passes LockContractTests.
- **B4:** `FakeMessageBus` — passes MessageBusContractTests (in-memory queues per subject).
- **B5:** `FakeRelationalDb` — sqlite-memory AsyncEngine + AsyncSession.

### Phase C: Postgres adapter
- **C1:** `PostgresProvider.setup` → create AsyncEngine + warm up + register OTel SQLAlchemy instrumentation.
- **C2:** `PostgresProvider.health_check` → `SELECT 1` round trip, target <100ms.
- **C3:** `PostgresProvider.shutdown` → engine.dispose().
- **C4:** `session()` factory → returns AsyncSession context manager.
- **C5:** `get_session` FastAPI Depends helper (yields per-request session, auto-rollback on exception).
- **C6:** `PostgresProvider` satisfies `RelationalDb` contract — runs `RelationalDbContractTests`.
- **C7:** alembic env helpers in `migrations.py` (async-engine wired into env.py template).
- **C8:** Optional `Repository[T]` base — ship per D2 (disabled by default, available as helper).
- **C9:** Integration tests via testcontainers PostgreSQL 16.

### Phase D: Redis adapter
- **D1:** `RedisProvider.setup` → connection pool + ping + OTel redis instrumentation.
- **D2:** `RedisCache` — wraps `redis.asyncio.Redis` for Cache contract.
- **D3:** `RedisProvider` also impls `KvStore` (just delegates; same backing connection).
- **D4:** `RedisDistributedLock` — `SET NX EX` + token-based safe-release Lua script.
- **D5:** `RedisMessageBus` — pub/sub via `PubSub`, durable=False (Streams support reserved
  for `hwhkit.integrations.redis_streams` future).
- **D6:** `RedisProvider` satisfies all 4 contracts (Cache, KvStore, DistributedLock, MessageBus).
- **D7:** Integration tests via testcontainers Redis 7.

### Phase E: Auth middleware (deferred from W2.11)
- **E1:** `hwhkit.web.middleware.auth.AuthMiddleware` — uses `JwtVerifier`;
  optional Redis token-blacklist (opt-in via config).
- **E2:** Tests with `pyjwt` mocked JWKS + TestClient.

### Phase F: Hardening
- **F1:** Benchmark suite (`tests/benchmark/test_postgres.py`, `test_redis.py`).
- **F2:** Chaos: disconnect / slow response via toxiproxy. May skip if toxiproxy
  setup proves slow in CI — D17-style fallback acceptable.
- **F3:** Coverage report; identify gaps; add tests.

### Phase G: Release prep
- **G1:** Update CHANGELOG + master TODO.
- **G2:** Update mkdocs site: `docs/integrations/postgres.md`, `docs/integrations/redis.md`.
- **G3:** Final mypy + ruff clean; push.

---

## Risk register

- **testcontainers macOS slow** — Spec § 11 risk #4. Mitigation: integration tests
  default to ubuntu CI only via marker; locally still runnable but marked `@pytest.mark.slow`.
- **OTel SQLAlchemy instrumentor strictness** — has been version-finicky. Mitigation:
  try-except around the call, log warning if instrumentation fails to install.
- **Redis pub/sub durability** — Redis pub/sub is fire-and-forget by design.
  Mitigation: clearly document the limit; reserve durable semantics for future
  Redis Streams adapter.
- **alembic async wiring** — alembic env.py needs `async_engine_from_config` not
  the sync default. Mitigation: ship env.py.j2 template via `hwhkit add postgres`
  CLI (W5); meanwhile document the snippet in W3 docs.

---

## Decision pre-commitments (no need to stop and ask)

Per D16 (灰区局部最优):

- alembic `script_location` defaults to `<project_root>/migrations` (industry standard).
- Redis MessageBus publish returns `PublishAck(subject=subject, sequence=0, duplicate=False)`
  — Redis pub/sub doesn't yield a server-assigned sequence; we surface 0 as a sentinel.
- DistributedLock Lua script for safe release (avoid releasing someone else's lock
  via key-value compare-and-delete atomicity).
- `FakeRelationalDb` uses `aiosqlite` in-memory; this means business unit tests run
  against a real SQL backend (just not Postgres). Tradeoff: real SQL parsing,
  dialect-specific features (JSONB ops, ON CONFLICT RETURNING) won't work in unit
  tests — those should be exercised in integration tier.

---

*End of W3 plan. Detailed steps emerge per task — short plan since W3 follows the
W1/W2 patterns established.*
