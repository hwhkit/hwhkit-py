# hwhkit-py 生产级重写 — Design Doc

- **Status**: Approved, ready for implementation planning
- **Date**: 2026-05-16
- **Author**: louishwh
- **Target version**: `0.4.0-alpha.1` → `1.0.0`(6 周)
- **Repo**: `github.com/hwhkit/hwhkit-py`
- **License**: `MIT OR Apache-2.0`(对齐 hwhkit-rs)
- **Python**: `>=3.11`

---

## 0. 目标与非目标

### 目标

- 把 hwhkit-py 从"试验品"提升到**工业级生产可用**框架,作为 `louishwh` 名下交易服务和多个微服务的共同底座
- 架构**完全镜像 hwhkit-rs**,跨语言切换零认知成本
- 测试基础设施达到**严格工业级**:单元 + 集成 + e2e + 性能基准 + 混沌 + 安全扫描全覆盖
- 落实"**框架沉淀不变、业务自己写**"哲学:通过 Contracts(端口)+ Adapters(适配器)实现底层组件无痕替换
- 6 周内发布 `1.0.0`,并在 mota 业务实际接入验证

### 非目标

- **不**做向后兼容旧 `infoman` API:全量重写,旧代码 `git rm`
- **不**做多语言 SDK 客户端(`hwhkit-py` 本身只是 Python 框架)
- **不**做服务网格 / 编排层 / API 网关(这些是更高一层的事)
- **不**做 GUI 管理面板
- **不**在 P0 实现 Vector / MongoDB / Neo4j / Object Store / MySQL(预留接口和占位)

---

## 1. 整体模块布局

包根:**`hwhkit`**(单 PyPI 包,所有非核心依赖走 extras)。

```
hwhkit/
├── __init__.py                  # facade: 顶层 re-export
│
├── core/                        # = hwhkit-rs/crates/hwhkit-core
│   ├── bootstrap.py             # bootstrap() 启动管线入口
│   ├── context.py               # AppContext
│   ├── integration.py           # IntegrationProvider ABC + 生命周期协议
│   ├── errors.py                # ApiError 类层级 + 错误码规范(XYYZZZ 6 位)
│   ├── health.py                # HealthCheck 协议 + 聚合器
│   ├── shutdown.py              # 优雅关闭
│   ├── jwt.py                   # JWT 验证器(JWKS 缓存 + FastAPI Depends 提取器)
│   └── contracts/               # 端口(抽象接口)— 业务代码 import 这里
│       ├── cache.py             # Cache protocol
│       ├── relational_db.py     # RelationalDb / Session protocol
│       ├── message_bus.py       # MessageBus protocol
│       ├── object_store.py     # ObjectStore protocol
│       ├── vector_store.py      # VectorStore protocol
│       ├── kv_store.py          # KvStore protocol
│       ├── scheduler.py         # Scheduler protocol
│       ├── lock.py              # DistributedLock protocol
│       ├── llm.py               # LlmClient / EmbeddingClient protocol
│       ├── secrets.py           # SecretsProvider protocol
│       ├── telemetry.py         # Tracer / Meter / LogEmitter protocol
│       └── notifier.py          # Notifier protocol
│
├── config/                      # = hwhkit-config
│   ├── base.py                  # Settings 基类(pydantic-settings)
│   ├── sources.py               # env / yaml / dotenv 加载器
│   └── schemas.py               # 各 integration 配置 schema 注册中心
│
├── observability/               # = hwhkit-observability
│   ├── otel.py                  # OTel SDK 初始化(默认关闭)
│   ├── logging.py               # 结构化日志 + trace 关联
│   ├── tracing.py               # span 装饰器/上下文管理器
│   ├── metrics.py               # 标准指标注册器
│   └── instrumentation.py       # 自动 instrumentation 注入
│
├── integrations/                # 适配器
│   ├── postgres/                # P0 ✅ 实现 RelationalDb
│   │   ├── provider.py
│   │   ├── session.py
│   │   ├── migrations.py
│   │   └── repository.py
│   ├── redis/                   # P0 ✅ 实现 Cache + KvStore + DistributedLock + MessageBus(pub/sub)
│   │   ├── provider.py
│   │   └── cache.py
│   ├── nats/                    # P1 ✅ 实现 MessageBus(JetStream)
│   │   ├── provider.py
│   │   ├── publisher.py
│   │   ├── consumer.py
│   │   └── jetstream.py
│   ├── mysql/                   # P2(占位,接口先定义)
│   ├── qdrant/                  # P2(占位)
│   ├── mongodb/                 # P2(占位)
│   ├── neo4j/                   # P2(占位)
│   ├── s3/                      # P2(占位)
│   └── oss/                     # P2(占位)
│
├── scheduler/                   # = hwhkit-scheduler (P0)
│   ├── provider.py              # SchedulerProvider (APScheduler 封装)
│   ├── lock.py                  # 基于 Redis 的分布式锁
│   └── decorators.py            # @scheduled_task
│
├── web/                         # FastAPI 集成层(取代旧 hwhkit.service)
│   ├── app.py                   # build_app() 工厂
│   ├── responses.py             # 统一 JSON 信封 + 分页
│   ├── exceptions.py            # 异常处理器
│   ├── middleware/{request_id,logging,auth,metrics}.py
│   └── server.py                # granian/uvicorn 启动器
│
├── llm/                         # P1 = LLM 集成
│   ├── provider.py              # LlmProvider (litellm-based, 实现 LlmClient/EmbeddingClient contract)
│   ├── chat.py
│   └── embeddings.py
│
├── utils/                       # 通用工具(从旧代码迁移)
│   ├── encryption.py
│   ├── hash.py
│   ├── decorators.py            # retry / cache / timing / safe_execute
│   ├── http.py                  # httpx 客户端封装
│   └── notification/feishu.py   # Notifier 实现
│
├── testing/                     # 框架自带,供业务方测试用
│   ├── fakes/                   # 内存实现的所有 contract
│   │   ├── cache.py             # FakeCache
│   │   ├── message_bus.py       # FakeMessageBus
│   │   ├── relational_db.py     # FakeRelationalDb(sqlite memory)
│   │   └── ...
│   ├── contract_tests/          # 通用 contract 契约测试套件(供 adapter 继承)
│   ├── fixtures.py              # pytest fixtures
│   ├── factories.py             # factory-boy helpers
│   └── otel_recorder.py         # 内存 OTel exporter
│
└── cli/                         # = cargo-hwhkit
    ├── __main__.py
    ├── commands/
    │   ├── init.py              # hwhkit init <name>
    │   ├── add.py               # hwhkit add <module>
    │   ├── doctor.py            # hwhkit doctor
    │   ├── upgrade.py           # hwhkit upgrade
    │   ├── new_integration.py   # hwhkit new-integration <name>(框架贡献者用)
    │   ├── gen.py               # hwhkit gen migration(alembic wrapper)
    │   ├── list.py              # hwhkit list
    │   └── version.py
    └── templates/
        ├── project/             # init 命令的项目骨架
        └── modules/             # add 命令的增量片段 + libcst codemod
```

### 1.1 Extras 映射

```toml
[project.optional-dependencies]
web         = ["fastapi", "granian", "orjson", "python-multipart", "aiofiles"]
postgres    = ["sqlalchemy[asyncio]~=2.0.36", "asyncpg~=0.31", "alembic~=1.14"]
redis       = ["redis[hiredis]~=7.1"]
nats        = ["nats-py~=2.10"]
mysql       = ["sqlalchemy[asyncio]~=2.0.36", "asyncmy~=0.2.10"]
qdrant      = ["qdrant-client~=1.16"]
mongodb     = ["motor~=3.5"]
neo4j       = ["neo4j~=5.20"]
s3          = ["aioboto3~=14.0"]
oss         = ["aliyun-oss2~=2.18"]
scheduler   = ["apscheduler~=3.10"]
llm         = ["litellm~=1.75"]
otel        = [
  "opentelemetry-sdk",
  "opentelemetry-exporter-otlp",
  "opentelemetry-instrumentation-fastapi",
  "opentelemetry-instrumentation-sqlalchemy",
  "opentelemetry-instrumentation-asyncpg",
  "opentelemetry-instrumentation-redis",
  "opentelemetry-instrumentation-httpx",
]
dev         = ["pytest>=8", "pytest-asyncio", "pytest-cov", "pytest-benchmark",
               "ruff>=0.14", "mypy>=1.8", "pre-commit>=3.6",
               "testcontainers[postgres,redis]", "respx", "freezegun",
               "libcst", "diff-cover"]
docs        = ["mkdocs~=1.6", "mkdocs-material~=9", "mkdocstrings[python]", "mike", "pytest-examples"]
security    = ["bandit", "pip-audit", "safety", "cyclonedx-py"]
all         = [上面所有 P0/P1 模块的 extras]
```

---

## 2. `IntegrationProvider` 抽象 + Bootstrap 流程

### 2.1 `IntegrationProvider` ABC

```python
# hwhkit/core/integration.py
from abc import ABC, abstractmethod
from typing import ClassVar, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends

from hwhkit.core.context import AppContext
from hwhkit.core.health import HealthStatus

class IntegrationProvider(ABC):
    """
    一个 Integration 是框架托管的插件:有生命周期、有配置 schema、有健康检查。
    通过 bootstrap() 注册一组 IntegrationProvider 实例。
    """
    name: ClassVar[str]                         # "postgres" / "redis" / "nats"
    config_schema: ClassVar[type[BaseModel]]
    implements: ClassVar[list[type]] = []       # 声明实现哪些 contracts

    @abstractmethod
    async def setup(self, ctx: AppContext) -> None: ...

    @abstractmethod
    async def health_check(self) -> HealthStatus: ...

    @abstractmethod
    async def shutdown(self) -> None: ...

    # 可选钩子(默认 no-op)
    def fastapi_router(self) -> Optional[APIRouter]: return None
    def fastapi_middlewares(self) -> list: return []
    def fastapi_dependencies(self) -> dict[str, Depends]: return {}
```

### 2.2 `AppContext`

```python
# hwhkit/core/context.py
class AppContext:
    """框架启动后的运行时上下文。"""
    config: Settings
    integrations: dict[str, IntegrationProvider]
    tracer: Tracer
    meter: Meter
    logger: BoundLogger

    def get(self, name: str) -> IntegrationProvider:
        """ctx.get("postgres") - 动态场景"""

    def get_typed(self, cls: type[T]) -> T:
        """ctx.get_typed(PostgresProvider) - 类型安全"""

    def bind_contract(self, contract: type, provider_name: str) -> None:
        """启动期手动绑定:Cache → "redis"。"""

    def resolve(self, contract: type[T]) -> T:
        """运行时取 contract 实现:ctx.resolve(Cache) → RedisProvider 实例。"""
```

### 2.3 Bootstrap 流程

```python
# 业务方代码:trading_service/main.py
from hwhkit import bootstrap
from hwhkit.integrations.postgres import PostgresProvider
from hwhkit.integrations.redis import RedisProvider
from hwhkit.integrations.nats import NatsProvider
from hwhkit.scheduler import SchedulerProvider

from trading_service.api import api_router
from trading_service.scheduler import register_jobs

app = bootstrap(
    name="trading-service",
    version="1.2.3",
    integrations=[
        PostgresProvider(),
        RedisProvider(),
        NatsProvider(),
        SchedulerProvider(),
    ],
    routers=[api_router],
    on_startup=[register_jobs],
    on_shutdown=[],
    config_overrides=None,        # 测试时可注入
)

if __name__ == "__main__":
    from hwhkit.web.server import run
    run(app)
```

**`bootstrap()` 内部按顺序执行:**

1. 加载配置(env → yaml → dotenv 合并)
2. 初始化 OpenTelemetry SDK(如 `observability.enabled=true`)
3. 创建 `AppContext`
4. **并行**调用所有 `integration.setup(ctx)`(失败立即终止启动)
5. 注册每个 integration 的 router/middleware/dependencies
6. 注册标准端点:`/healthz` / `/readyz` / `/version` / `/metrics`(可选)
7. 注册信号处理器(SIGTERM/SIGINT → 反向调用所有 `integration.shutdown()`)
8. 执行用户 `on_startup` 钩子
9. 返回 FastAPI app 实例

### 2.4 接合点(业务代码使用 integration 的三种方式)

```python
# 方式 1:FastAPI Depends(推荐,显式、可测试)
from hwhkit.integrations.postgres import get_session

@router.get("/users/{id}")
async def get_user(id: int, session: AsyncSession = Depends(get_session)):
    return await session.get(User, id)

# 方式 2:从 ctx 取(全局,适合后台任务)
@router.post("/jobs")
async def trigger_job(request: Request):
    ctx: AppContext = request.app.state.ctx
    bus = ctx.resolve(MessageBus)
    await bus.publish("jobs.new", payload)

# 方式 3:装饰器(定时任务/事件订阅)
@scheduled_task("0 * * * *", lock_key="hourly-aggregate")
async def hourly_aggregate(ctx: AppContext): ...

@nats_subscriber("trades.executed")
async def handle_trade(event: TradeEvent, ctx: AppContext): ...
```

### 2.5 关键设计原则

- **顺序无关**:`setup()` 并行调用,integration 之间不能互相依赖启动顺序
- **失败语义**:任一 `setup()` 抛异常 → 框架反向 `shutdown()` 已起来的 → 进程退出 + log fatal
- **健康检查分级**:`liveness` 永远 200,只要进程在;`readiness` 任一 unhealthy 即 503
- **shutdown 超时**:每个 `shutdown()` 给 30s timeout(可配),超时强杀;反向顺序

---

## 3. Web 层(FastAPI 集成)

定位:`hwhkit.web` 只做"FastAPI 集成 + 通用 HTTP 模式",**不做业务路由**。

### 3.1 `build_app()` 工厂

`bootstrap()` 内部调用,顺序:
1. 创建 FastAPI app + 注入 AppContext
2. 注册异常处理器
3. 注册标准中间件(从外到内):GZip → CORS → RequestID → Logging → Metrics
4. 注册各 integration 提供的中间件
5. 注册系统路由(/healthz, /readyz, /version, /metrics)
6. 注册业务路由
7. 注册各 integration 暴露的管理路由(默认关闭)

### 3.2 统一响应信封

```python
class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "ok"
    data: Optional[T] = None
    trace_id: Optional[str] = None  # 自动注入

class PageResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int
    has_next: bool
```

**默认开启**信封,**支持 opt-out**:路由加 `@raw_response` 装饰器返回裸数据。

### 3.3 错误处理与错误码

```python
# hwhkit/core/errors.py
class ApiError(Exception):
    code: int        # 6 位:XYYZZZ
    http_status: int
    message: str
    details: dict = {}
```

**6 位错误码规范 `XYYZZZ`**:

- `X` 大类:`1`=客户端 / `5`=服务端 / `9`=外部依赖 / `6-8`=业务自留
- `YY` 模块:`00`=core / `01`=auth / `10`=postgres / `11`=redis / `12`=nats / `13`=scheduler / `14`=llm / `15`=web / `20-99`=业务保留
- `ZZZ` 具体错误:模块内自编

**框架预定义错误**(节选):

| 类 | code | http |
|---|---|---|
| NotFoundError | 100404 | 404 |
| UnauthorizedError | 100401 | 401 |
| ForbiddenError | 100403 | 403 |
| ValidationError | 100422 | 422 |
| ConflictError | 100409 | 409 |
| RateLimitError | 100429 | 429 |
| InternalError | 500000 | 500 |
| IntegrationError | 500001 | 503 |
| DbConnectionError | 510001 | 503 |
| RedisConnectionError | 511001 | 503 |
| NatsConnectionError | 512001 | 503 |

**异常处理器优先级**:
1. `ApiError` → 按 `http_status` + `ApiResponse`
2. `RequestValidationError`(FastAPI) → 422 + `code=100422`
3. `HTTPException`(FastAPI 原生) → 透传 + 包装信封
4. `Exception`(兜底) → 500 + `code=500000` + 日志记录;**不**返回 traceback

### 3.4 标准中间件

| 中间件 | 职责 | 备注 |
|---|---|---|
| RequestIDMiddleware | 从 `X-Request-ID` header 取或生成 UUID,贯穿日志/trace | 必须最外层 |
| LoggingMiddleware | 请求/响应日志(method/path/status/duration/request_id) | 不记 body |
| MetricsMiddleware | OTel meter:`http.server.*` | label 含 method/route/status |
| AuthMiddleware(可选) | JWT 验证 + 注入 user | 用 `hwhkit.core.jwt` |

### 3.5 服务器启动器

```bash
hwhkit-serve --app trading_service.main:app --server granian --workers 4
```

支持 granian(生产推荐)/ uvicorn(开发)/ gunicorn(legacy)。

---

## 4. 可观测性(OpenTelemetry 三合一)

### 4.1 三大信号

| 信号 | 用什么 | 业务方接口 |
|---|---|---|
| Traces | OTel SDK + OTLP exporter | 自动(FastAPI/SQLAlchemy/Redis/httpx/NATS auto-instrumentation) |
| Metrics | OTel SDK + OTLP exporter(可选 Prometheus 兼容) | 自动(标准指标)+ `meter.create_counter(...)` 自定义 |
| Logs | structlog + OTel logs bridge | `get_logger(__name__).info(event, ...)` |

**整个 observability 子系统默认关闭**(`observability.enabled=false`)。本地开发零开销;生产显式 enable。

### 4.2 OTel SDK 初始化

```yaml
observability:
  enabled: false                     # 默认关闭
  service_name: trading-service
  service_version: ${APP_VERSION}
  environment: prod                  # dev/staging/prod
  exporter: otlp_http                # otlp_http / otlp_grpc / console / none
  endpoint: http://otel-collector:4318
  sampler:
    type: parent_based_ratio
    ratio: 0.1
  prometheus_compat:
    enabled: false                   # 过渡期可开,默认关
```

### 4.3 采样

- 默认 `ParentBased(TraceIdRatioBased(0.1))`,生产 10%
- `_HealthCheckExcludingSampler` 包装,排除 `/healthz` / `/readyz` / `/metrics`
- 错误/慢请求强采样:在 collector 侧用 tail-sampling 实现

### 4.4 自动 Instrumentation

| 库 | OTel 包 |
|---|---|
| FastAPI | `opentelemetry-instrumentation-fastapi` |
| SQLAlchemy | `opentelemetry-instrumentation-sqlalchemy` |
| asyncpg | `opentelemetry-instrumentation-asyncpg` |
| Redis | `opentelemetry-instrumentation-redis` |
| httpx | `opentelemetry-instrumentation-httpx` |
| nats-py | 自实现(traceparent 走 NATS header) |
| APScheduler | 自实现(跨次执行用 span link) |

### 4.5 日志 ↔ Trace 关联

structlog 上下文处理器自动注入 `trace_id` / `span_id`,JSON 格式同时输出到 stdout 和 OTel logs。

### 4.6 标准指标

遵循 OTel Semantic Conventions:`http.server.*` / `db.client.*` / `redis.command.*` / `messaging.*` / `scheduler.job.*`。

### 4.7 替换 OTel 后端

通过 `Telemetry` contract 抽象 Tracer/Meter/LogEmitter。OTel 是默认 adapter,但理论上可替换(罕见需求)。

---

## 5. Contracts 层(Hexagonal Architecture)

### 5.1 核心思想

- 业务代码**只依赖** `hwhkit.core.contracts.*` 的 protocol(端口)
- `hwhkit.integrations.*` **实现这些 protocol**(适配器)
- 替换底层(NATS↔Kafka、Postgres↔MySQL)= 换 adapter,业务零变更

**`IntegrationProvider` 管生命周期,`Contract` 管业务能力 —— 两层正交。** 一个 integration 可实现 0 或多个 contract。

### 5.2 第一批交付的 Contract

| Contract | 首批 adapter | 分级 | 未来 adapter |
|---|---|---|---|
| Cache | Redis | P0 | Memcached, in-memory |
| KvStore | Redis | P0 | etcd, Consul |
| DistributedLock | Redis(Redlock) | P0 | etcd, ZooKeeper |
| RelationalDb | Postgres(SQLAlchemy) | P0 | MySQL(P2) |
| Scheduler | APScheduler | P0 | Celery-beat, Temporal |
| Telemetry | OTel | P0 | 自定义 |
| MessageBus | NATS JetStream | P1 | Kafka, RabbitMQ, Redis Streams |
| LlmClient / EmbeddingClient | litellm | P1 | 直连 OpenAI/Anthropic |
| Notifier | 飞书 | P1 | 钉钉、邮件、短信 |

P2 接口先定义,实现推后:`VectorStore`(Qdrant)、`ObjectStore`(S3/OSS)、`GraphDb`(Neo4j)、`DocumentDb`(MongoDB)。

### 5.3 示例:`Cache` contract

```python
@runtime_checkable
class Cache(Protocol):
    async def get(self, key: str) -> Optional[bytes]: ...
    async def set(self, key: str, value: bytes, ttl: Optional[timedelta] = None) -> None: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def incr(self, key: str, delta: int = 1) -> int: ...
    async def expire(self, key: str, ttl: timedelta) -> bool: ...

class TypedCache(Generic[T]):
    """高层封装:JSON/pickle 编解码 + 类型化"""
```

### 5.4 示例:`MessageBus` contract

```python
@runtime_checkable
class MessageBus(Protocol):
    async def publish(self, subject: str, payload: bytes, *,
                      headers: dict[str, str] | None = None,
                      deduplication_key: str | None = None) -> PublishAck: ...
    async def subscribe(self, subject: str, handler: Callable[[Message], Awaitable[None]], *,
                        durable: str | None = None, manual_ack: bool = False,
                        max_in_flight: int = 100) -> Subscription: ...
    async def request(self, subject: str, payload: bytes,
                      timeout: timedelta = timedelta(seconds=5)) -> bytes: ...
```

### 5.5 业务代码示例(只依赖 contract)

```python
class PortfolioService:
    def __init__(self, db: RelationalDb, cache: Cache, bus: MessageBus):
        self.db, self.cache, self.bus = db, cache, bus

    async def get_position(self, user_id: int, symbol: str) -> Position:
        if cached := await self.cache.get(f"pos:{user_id}:{symbol}"):
            return Position.from_bytes(cached)
        ...
        await self.bus.publish("portfolio.queried", event.to_bytes())
```

### 5.6 DI 绑定机制

```python
class RedisProvider(IntegrationProvider):
    name = "redis"
    implements = [Cache, KvStore, DistributedLock, MessageBus]  # 自动注册
```

多 adapter 实现同一 contract 时,在 config 显式选:
```yaml
contracts:
  message_bus: nats
  cache: redis
```

### 5.7 何时不抽象 — Escape Hatch

需要 adapter 特定能力时显式 opt-out:
- Postgres 特定语法 → 直接拿 SQLAlchemy `Session`
- NATS JetStream 特定 API → `ctx.get_typed(NatsProvider).js`
- Redis Lua 脚本 / Streams → `ctx.get_typed(RedisProvider).client`

**约定**:opt-out 处用 `_pg_specific` / `_nats_specific` 后缀,便于审计。

---

## 6. 测试金字塔(工业级)

### 6.1 分层

| 层 | 目录 | 占比 | 时长 | 触发 |
|---|---|---|---|---|
| Unit | `tests/unit/` | 70% | <30s | 每 commit / pre-commit |
| Integration | `tests/integration/` | 20% | <3min | 每 PR |
| E2E | `tests/e2e/` | 5% | <5min | 每 PR |
| Benchmark | `tests/benchmark/` | 3% | <10min | 每 PR(对比基线)+ main 写基线 |
| Chaos | `tests/chaos/` | 1% | <15min | 每周 cron + 手动 |
| Security | scanners | n/a | <2min | 每 PR + 每周 SBOM |

**覆盖率**:整体 ≥85%,`hwhkit.core` ≥95%,每个 integration 关键路径 ≥90%,新代码 ≥90%。

### 6.2 Unit

工具:`pytest` + `pytest-asyncio` + `freezegun` + `respx` + `pytest-mock`。
- 纯函数 / 业务逻辑 / 错误码映射 / contract 契约 / config 解析
- 不允许 I/O
- 每个 contract 配 `FakeAdapter`(`hwhkit.testing.fakes`)

### 6.3 Integration

工具:`testcontainers` 自动起停容器,端口随机。

每个 P0/P1 integration 必须覆盖:
- Setup → 健康 → Shutdown 完整生命周期
- 真实 CRUD / publish-subscribe / lock-unlock
- 连接断开重连
- 慢响应(toxiproxy 注入延迟)
- 配置错误清晰报错
- contract 契约验证(继承 `CacheContractTests` 等通用套件)

### 6.4 E2E

启动完整 `tests/e2e/sample_app/`(用框架 bootstrap 的最小服务),`httpx.AsyncClient` 黑盒打。

### 6.5 Benchmark

`pytest-benchmark`,关键路径:
- `bootstrap()` 冷启动 <2s(全 P0 integration)
- 每个 contract 操作 p99
- 中间件开销 baseline vs 全套
- OTel auto-instrumentation 开销

基线写入 `.benchmarks/main.json`,PR 回归 >10% 自动失败。

### 6.6 Chaos

工具:**toxiproxy** + docker-compose。

场景(完整列表):
- DB 完全断连 → 验证连接池行为、health → unhealthy
- DB 慢响应(5s latency) → 验证 query timeout 不级联
- DB 包丢失 → 验证重试 + 熔断
- Redis 持续重启 → 验证 scheduler 分布式锁不双跑
- NATS broker 切换 → 验证自动重连 + 不丢消息
- OTel collector 不可达 → 验证 SDK 队列不爆 + 降级

**跑频**:每周日 cron + 大版本前手动。失败自动建 issue。

### 6.7 Security

| 工具 | 用途 | 跑频 |
|---|---|---|
| bandit | 代码静态安全扫描 | 每 PR |
| pip-audit | 依赖漏洞 | 每 PR |
| safety | 依赖漏洞(double check) | 每 PR |
| semgrep | 自定义模式 | 每 PR |
| trufflehog/gitleaks | 防止密钥提交 | pre-commit + PR |
| cyclonedx-py | SBOM 生成 | 每 release |
| pip-licenses | 不允许 GPL/AGPL | 每 PR |

JWT/加密代码额外要求负向测试:过期 / 弱密钥 / 算法混淆(`none` 攻击) / 重放 / 时序攻击。

### 6.8 `hwhkit.testing` 子模块

```python
hwhkit/testing/
├── fakes/                       # 内存实现的所有 contract
├── contract_tests/              # 通用 contract 契约测试套件
├── fixtures.py                  # postgres_container, sample_app 等
├── factories.py                 # factory-boy helpers
└── otel_recorder.py             # 内存 OTel exporter
```

业务方使用示例:
```python
from hwhkit.testing.fakes import FakeCache, FakeRelationalDb, FakeMessageBus

async def test_get_position():
    service = PortfolioService(db=FakeRelationalDb(), cache=FakeCache(), bus=FakeMessageBus())
    ...
```

---

## 7. CI/CD + Release/Versioning

### 7.1 平台

**GitHub Actions**,PyPI Trusted Publishing(OIDC,无 token)。

### 7.2 流水线

```
PR 触发                                main 触发                tag v* 触发
─────────                              ─────────                ───────────
pre-commit / lint                      + write benchmark baseline   + publish PyPI
test-unit (matrix 3.11/3.12 x mac/lin) + deploy docs (mike)          + publish docs (versioned)
test-integration (testcontainers)      + build & push images         + create GitHub Release
test-e2e                                                              + sigstore 签名
benchmark (compare to baseline)                                       + SBOM artifact
security-scan
build-wheel
license-check

每周日 cron:
chaos-test
dependency-update (renovate)
```

### 7.3 关键约束

- PR 全套 CI <10 分钟
- main 永远绿,merge 需 1+ approval + CI 全绿
- Conventional Commits 规范 + release-please 自动 bump 版本/CHANGELOG
- 每个 release 附带:sdist + wheel + sigstore 签名 + SBOM(SPDX + CycloneDX) + SLSA provenance

### 7.4 SemVer 政策

```
MAJOR.MINOR.PATCH
MAJOR: 破坏性变更
MINOR: 新功能,向后兼容
PATCH: bug 修复
Pre-release: alpha → beta → rc
```

**0.x 阶段**:minor(`x`)可 breaking,但 release notes 必须有 migration guide;patch(`y`)严格非破坏性。计划 6 周后发 `1.0.0`。

**Deprecation 政策**:`@deprecated` 至少保留 1 个 MINOR 版本 → MAJOR 移除;伴随 `DeprecationWarning` + CHANGELOG 标注 + 文档横幅。

### 7.5 分支策略

```
main         ← protected
  ↑
  feature/*  ← 短命分支
release/*    ← 长版本分支(关键 bugfix backport)
hotfix/*     ← 紧急修复
```

### 7.6 文档

**mkdocs-material + mike**(版本化),部署到 `hwhkit.louishwh.tech`。

结构:
- `concepts/`:bootstrap / AppContext / IntegrationProvider / contracts
- `integrations/`:每个 integration 一篇
- `contracts/`:每个 contract 规范 + 跨 adapter 行为对照
- `recipes/`:交易服务、定时任务、事件驱动、AI agent
- `api/`:mkdocstrings 自动生成
- `migration/`:版本迁移指南
- `contributing/`:贡献指南、本地开发、跑测试

文档代码块用 `pytest-examples` 校验可跑通。

---

## 8. CLI 脚手架

### 8.1 命令集

```bash
hwhkit init <name>            # 创建项目
hwhkit add <module>           # 增量加 integration
hwhkit doctor                 # 项目体检
hwhkit upgrade                # 升级 + 应用 codemod
hwhkit new-integration <name> # 框架贡献者:生成新 integration 骨架
hwhkit gen migration "<msg>"  # alembic wrapper
hwhkit list                   # 列出已启用 integration
hwhkit version                # 打印版本
```

### 8.2 `hwhkit init <name>`

生成完整可跑的项目骨架(默认零 integration,只有 /healthz):

```
trading-service/
├── pyproject.toml + uv.lock
├── .env.example / .gitignore
├── Makefile (make {dev, test, lint, build, run})
├── Dockerfile (multi-stage, python:3.12-slim)
├── docker-compose.yml (依赖注释模板)
├── .github/workflows/{ci.yml, release.yml}
├── docs/README.md
├── trading_service/
│   ├── main.py / config.py
│   ├── api/ / services/ / domain/ / adapters/
└── tests/{unit, integration, e2e}/ + conftest.py
```

### 8.3 `hwhkit add <module>`

**实现策略:libcst CST 编辑**,保留注释/格式/空行,用户改过 main.py 也能合并。

支持模块:
- postgres / redis / nats / scheduler / llm / auth / otel / admin / mysql(P2)

**幂等**:重复跑同一命令检测到已加,不重复修改。

**前置检查**:
- 是 hwhkit 项目(找 pyproject 依赖)
- main.py 可解析 + 找得到 `bootstrap()` 调用
- 目标 integration 未存在

**失败时**:写变更到 `.hwhkit-add.preview/`,报错并给手动指引。

### 8.4 `hwhkit doctor`

检查项:
- 依赖最新性 + 漏洞(pip-audit)
- 配置 schema 完整性
- 是否有直接 import adapter 的代码(违反 contract)
- 是否有 deprecation warning
- 测试覆盖率快速 sample
- alembic 配置完整性
- Dockerfile 反模式(alpine 警告)
- `.env.example` 完整性

`hwhkit doctor --fix` 自动修复能修的。

### 8.5 `hwhkit upgrade`

```bash
$ hwhkit upgrade
✓ Current: 0.9.x → Latest: 1.0.0
⚠ Major upgrade, breaking changes
✓ Found N applicable codemods (示例,实际由发布时的 breaking 变更决定):
    - bootstrap() 参数 `routers=` 重命名为 `routes=` (X files)
    - Cache.set() ttl 参数类型从 int(秒) 改为 timedelta (X files)
    - 弃用的 `hwhkit.utils.legacy.*` 完全移除,替换为 `hwhkit.utils.*` (X files)
✓ Preview / Apply ?
```

**codemod = libcst 写的代码改写规则,跟着 `hwhkit` 自己版本走**。每个 breaking 必须配套 codemod。0.4.0 是干净起点,首批 codemod 会从首个引入 breaking 变更的版本开始累积(可能是 0.x → 1.0、或 1.x → 2.0)。

### 8.6 CLI 实现栈

- Click(命令路由)
- rich(输出)
- libcst(CST 编辑)
- jinja2(non-Python 模板)
- uv(子进程调用)

### 8.7 关键设计原则

- `init` 出来的真能跑(`uv sync && uv run python -m <pkg>.main` 立即起来)
- `add` 幂等 + `--dry-run` 默认显示 diff
- `add` 用 CST 而非字符串拼接
- 每个 breaking 变更配套 codemod
- `doctor` 抓反模式
- 不锁定项目结构(建议而非强制)

---

## 9. 迁移 / Cutover 计划

### 9.1 老代码处置

**`git rm -r hwhkit/` 直接删**,从空目录重写。

需要参考老代码时:
- 旧代码留在 `infoman-kit-py` 原仓库(`/Users/louis/infoman/infoman-kit-py`)
- 重写过程中需要"打捞"的具体文件(utils 加密/hash、scaffold templates、响应辅助):用 `cp` 显式拷贝 + 重构
- 不保留任何兼容层

### 9.2 起步版本

`0.4.0-alpha.1`(承接现有 0.3.29 编号)。alpha → beta → rc → `0.4.0` → ... → `1.0.0`。

### 9.3 六周里程碑

| 周 | 产出 | 可验证标准 |
|---|---|---|
| **W1** | 项目骨架(空 `hwhkit/`)+ pyproject + extras + CI/CD 骨架 + pre-commit + 测试基础设施(testcontainers, fakes 框架, benchmark 框架, OTel 内存 recorder)+ `hwhkit.core.contracts` 所有 protocol + `hwhkit.core.integration` ABC + `hwhkit.core.errors` + `hwhkit.core.context` | CI 全绿;文档站冒烟版上线 `hwhkit.louishwh.tech` |
| **W2** | `hwhkit.core.bootstrap` + `hwhkit.web` 完整(app factory + middleware + responses + exceptions)+ `hwhkit.observability` 完整(OTel 三合一)+ `hwhkit.config` 完整 + `hwhkit.utils.*` 全迁移 | sample_app 起得来,/healthz /readyz /metrics 通,零 integration 时 e2e 全绿 |
| **W3** | **Postgres** 完整(provider + session + alembic + repository + contract tests + 集成测试 + benchmark + chaos)+ **Redis** 完整(Cache + KvStore + Lock + MessageBus 四个 contract) | 两个 P0 integration 通过完整测试金字塔 |
| **W4** | **Scheduler** 完整(provider + 分布式锁 + 装饰器)+ **NATS** 完整(MessageBus / publisher / consumer / JetStream) | 全部 P0 完成 |
| **W5** | **CLI 完整**(init + add 各模块 + doctor + upgrade + new-integration + gen)+ **`hwhkit.testing` 完整** + **LLM**(litellm)+ **JWT auth** + **Notifier(飞书)** | `hwhkit init` 一键创建出可跑的 trading-service demo;P1 完成 |
| **W6** | **P2 占位 integration**(mysql / qdrant / mongodb / neo4j / s3 / oss)空目录 + Provider 接口 + 文档 + **完整文档站** + **发布 0.4.0-rc.1 到 TestPyPI** + **真实业务场景接入验证**(见 § 9.4) | rc.1 在 TestPyPI;接入冒烟通过;一周内若无问题发 `0.4.0` 正式版 |

### 9.4 W6 业务接入验证 — 强约束

**背景**:当前 mota 项目栈是 Rust(mota-service / mota-agent)+ Flutter(mota-app),没有 Python 服务直接可用。因此 W6 验证目标改为以下二选一,由作者按当周资源决定:

- **选项 1(推荐)**:基于 hwhkit 0.4.0-rc.1 构建一个 **mota-data-ingest** 之类的真实 Python 微服务,职责小但栈完整(Postgres + Redis + NATS + Scheduler + OTel),供 mota 主栈消费。验证标准:服务在本地 docker-compose 起来 + 写入数据库 + 发布 NATS 事件 + 定时任务跑通 + OTel 指标可见。
- **选项 2(备选)**:在 hwhkit 仓库内 `examples/full-stack/` 下构建一个**仿真完整微服务**(模拟一个交易撮合服务,带 5 个 endpoint + 2 个定时任务 + 1 个事件订阅)。验证标准:完整 e2e 测试套件通过,benchmark 达标,chaos 测试不挂。

无论哪个,**目的相同:在真实使用场景下暴露 design 中的缺陷**。这一步暴露的问题在 0.4.x 系列 patch 修复;不阻塞 1.0.0,但 1.0.0 发布前所有 W6 暴露的问题必须有 issue + 修复或明确 wontfix 理由。

### 9.5 1.0.0 发布前的 Definition of Done

- ✅ 所有 P0/P1 integration 通过完整测试金字塔
- ✅ 覆盖率达标(整体 85% / core 95% / 新代码 90%)
- ✅ 所有 chaos 测试通过
- ✅ 所有 security 扫描通过(无 high 漏洞)
- ✅ benchmark 基线建立
- ✅ 完整文档站上线
- ✅ CLI 完整可用,`hwhkit init` + 全部 `add` 命令演示通过
- ✅ mota 实际接入验证通过
- ✅ CHANGELOG 完整,migration guide 写完
- ✅ Sigstore 签名 + SBOM + SLSA provenance 流水线跑通

---

## 10. 跨语言一致性 — 与 hwhkit-rs / hwhkit-go 的关系

`hwhkit` 是三语言基础框架品牌:

| 实现 | 仓库 | 角色 |
|---|---|---|
| `hwhkit-rs` | `github.com/louishwh/hwhkit-rs` | 高性能后端、架构参考 |
| `hwhkit-py` | `github.com/hwhkit/hwhkit-py`(本文档) | 业务/AI/数据后端、生态主力 |
| `hwhkit-go` | `github.com/louishwh/hwhkit-go` | 微服务、CLI 工具(后续按相同思路重写) |

三语版本**模块切分对齐**:
- `core` / `config` / `observability` / `integrations.*` / `scheduler` / `cli`
- IntegrationProvider 抽象、AppContext、Bootstrap 流程、ApiError 6 位错误码、健康检查协议 —— 跨语言概念一致

**不强求**:
- 各语言惯用具体库不同(Python FastAPI / Rust Axum / Go gin 或 chi)
- 测试工具链各异
- 各语言的 ergonomic 不强行模仿(如 Python 用 ABC + Protocol、Rust 用 trait、Go 用 interface)

---

## 11. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 6 周排期过紧 | 1.0.0 跳票 | W6 业务接入验证缓冲(0.4.x patch 系列消化);1.0.0 可延后 1-2 周 |
| Contract 抽象过度 | 性能或灵活性损失 | 提供 escape hatch(`ctx.get_typed(...)` 拿原生 adapter);benchmark 强制 |
| libcst codemod 学习曲线 | CLI add 命令延期 | W5 集中实现;部分 add 模块若 codemod 过复杂,降级为"提示用户手动改" |
| testcontainers macOS 慢 | 本地开发体验差 | 集成测试默认 ubuntu CI 跑;macOS 本地用 Docker Desktop 或 Colima 加速 |
| OTel 自动 instrumentation 兼容性问题 | 观测数据丢失或服务异常 | observability 默认关闭;启用后有 fallback 到无 instrumentation 的能力 |
| 与 mota 业务接入冲突 | W6 暴露大量问题 | 提早(W5 末)做 mota 接入 spike,而非到 W6 才动手 |
| 0.x → 1.0 breaking 太多 | 业务方升级痛苦 | codemod 配套;CHANGELOG migration guide 详尽 |

---

## 附录 A:决策一览表

| 决策 | 选择 |
|---|---|
| 实施路径 | 全量重写(Approach A) |
| ORM | SQLAlchemy 2.0 async only(砍 Tortoise) |
| 测试深度 | 工业级(unit + integration + e2e + benchmark + chaos + security) |
| 观测 | OpenTelemetry 三合一 |
| 架构 | 完全镜像 hwhkit-rs |
| 发布 | 单 PyPI 包 + extras |
| 响应信封 | 默认启用,`@raw_response` opt-out |
| 错误码 | 6 位 `XYYZZZ` |
| 整合管理路由 | 默认关闭,显式开启 + 强制 auth |
| Observability 启用 | 默认关闭 |
| Contracts/Adapters | 启用,业务零依赖 adapter |
| `hwhkit.testing` | 启用 |
| 文档站 | `hwhkit.louishwh.tech`(mkdocs-material + mike) |
| CLI 命令集 | init + add + doctor + upgrade + new-integration + gen + list + version |
| `add` 实现 | libcst CST 编辑 |
| `upgrade` codemod | 每个 breaking 必配套 |
| 老代码处置 | `git rm -r hwhkit/` 直接删 |
| 起步版本 | 0.4.0-alpha.1 |
| Python 最低版本 | >=3.11 |
| 仓库 | `github.com/hwhkit/hwhkit-py` |
| License | `MIT OR Apache-2.0` |
| 1.0.0 目标日期 | 6 周后 |

---

## 附录 B:目录树最终态

见 § 1。所有 P2 占位 integration 在 W6 创建空目录 + `provider.py` 接口签名,实现推后。

---

*文档结束。*
