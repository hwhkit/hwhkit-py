# hwhkit-py 全量重写 — Master TODO List

> **For agentic workers:** 这是 6 周里程碑的高层全景。**每周一份独立的详细 plan**(`2026-05-XX-hwhkit-py-wN-<topic>.md`),W1 plan 已生成可立即执行。W2-W6 plan 在前一周完成时基于实战反馈生成。

**Spec**: `docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md`
**Target**: 0.4.0-alpha.1 → 1.0.0 in 6 weeks
**Start date**: 2026-05-16

---

## 全局进度

- [x] **W1: Foundation** — 项目骨架 + CI/CD + 测试基础设施 + `hwhkit.core` 完整 ✅ **2026-05-16 完成**
- [x] **W2: Web + Observability + Config** — bootstrap 全打通 + 空 integration 服务可启动
- [x] **W3: Postgres + Redis** — 两个 P0 integration 完整测试金字塔
- [x] **W4: Scheduler + NATS** — 全 P0 完成
- [x] **W5: CLI + Testing + P1 (LLM/Auth/Notifier)** — `hwhkit init` 一键可用
- [ ] **W6: P2 占位 + 文档 + Release rc.1 + 业务验证** — 0.4.0 正式发布

---

## W1: Foundation Week

**目标**: 项目从空目录到"测试基础设施全就绪、所有 contracts 已定义、CI 全绿"。

**详细 plan**: [`2026-05-16-hwhkit-py-w1-foundation.md`](./2026-05-16-hwhkit-py-w1-foundation.md)

- [x] **W1.1** 清空 + 重新初始化项目骨架(`git rm -r hwhkit/` + `uv init`)
- [x] **W1.2** `pyproject.toml` 完整 metadata + 所有 extras 定义
- [x] **W1.3** `pre-commit` 配置(ruff format/check, mypy strict, trufflehog, yamllint, toml-sort)
- [x] **W1.4** `tests/` 目录结构(unit/integration/e2e/benchmark/chaos) + `conftest.py`
- [x] **W1.5** `.github/workflows/ci.yml` 流水线(lint + test-unit matrix + build-wheel)
- [ ] **W1.6** `.github/workflows/release.yml`(tag 触发发布) — 推迟到 W6 sigstore/Trusted Publishing 配置
- [x] **W1.7** Renovate / dependabot 配置
- [x] **W1.8** `mkdocs.yml` + 文档站冒烟版 + `hwhkit.louishwh.tech` DNS 准备(DNS 由作者另外配置)
- [x] **W1.9** `hwhkit.core.errors` 完整 6 位错误码体系 + 所有预定义异常类
- [x] **W1.10** `hwhkit.core.contracts.*` 全部 12 个 protocol 定义
- [x] **W1.11** `hwhkit.core.integration.IntegrationProvider` ABC + 元数据
- [x] **W1.12** `hwhkit.core.context.AppContext` 完整(get / get_typed / bind_contract / resolve)
- [x] **W1.13** `hwhkit.core.health.HealthStatus` + `HealthCheck` 协议 + 聚合器
- [x] **W1.14** `hwhkit.core.shutdown` 优雅关闭管线
- [x] **W1.15** `hwhkit.core.jwt` JWKS 缓存 + Claims 提取器(测试用 mock JWKS)
- [x] **W1.16** `hwhkit.testing` 基础架子:`fakes/` 空目录 + `contract_tests/` 框架 + `otel_recorder.py`
- [x] **W1.17** `Makefile`(make {dev, test, lint, build, docs})
- [x] **W1.18** W1 验收:CI 全绿 + 文档站冒烟版上线 + 所有 contract 有针对性 unit test ✅

**W1 实际产出**:14 个 commit,68 单测全过,覆盖率 89%(目标 85% ✅),`hwhkit.core` 子模块 95%+,mypy strict 干净,ruff 全绿。

**W1 推迟项**:
- W1.6 release.yml 推到 W6(届时配 sigstore/Trusted Publishing 一起做)
- `hwhkit.louishwh.tech` DNS 由作者手动配置(`CNAME → louishwh.github.io`)
- GitHub remote 确认为 `git@github.com:hwhkit/hwhkit-py.git`(用户决定使用 `hwhkit/` GitHub 组织,docs 站仍部署在个人域名 `hwhkit.louishwh.tech`)

---

## W2: Web + Observability + Config

**目标**: bootstrap 全打通,零 integration 的最小服务可启动 + `/healthz` /readyz` 通,OTel 三大信号可发(本地 console exporter)。

待 W1 完成时生成详细 plan。**预计任务**:

- [x] **W2.1** `hwhkit.config.base.Settings` 基类(pydantic-settings)
- [x] **W2.2** `hwhkit.config.sources` env/yaml/dotenv 加载
- [x] **W2.3** `hwhkit.config.schemas` 注册中心(整合 integration 配置)
- [x] **W2.4** `hwhkit.core.bootstrap` 启动管线(完整 9 步)
- [x] **W2.5** `hwhkit.web.app.build_app()` 工厂
- [x] **W2.6** `hwhkit.web.responses` `ApiResponse[T]` + `PageResponse[T]` + `@raw_response`
- [x] **W2.7** `hwhkit.web.exceptions` 异常处理器注册
- [x] **W2.8** `hwhkit.web.middleware.request_id`
- [x] **W2.9** `hwhkit.web.middleware.logging`
- [x] **W2.10** `hwhkit.web.middleware.metrics`
- [x] **W2.11** `hwhkit.web.middleware.auth`(用 W1 JWT)
- [x] **W2.12** `hwhkit.web.server` granian/uvicorn launcher + `hwhkit-serve` CLI
- [x] **W2.13** `hwhkit.observability.otel` SDK 初始化(默认关闭)
- [x] **W2.14** `hwhkit.observability.logging` structlog + trace_id 注入
- [x] **W2.15** `hwhkit.observability.tracing` span 工具
- [x] **W2.16** `hwhkit.observability.metrics` 标准指标注册
- [x] **W2.17** `hwhkit.observability.instrumentation` 自动 instrumentation 入口
- [x] **W2.18** `hwhkit.utils.*` 全部迁移(encryption/hash/decorators/http/notification/feishu)
- [x] **W2.19** `tests/e2e/sample_app/` 最小服务 + e2e 测试
- [x] **W2.20** W2 验收:`sample_app` 起得来,/healthz /readyz /version 通,OTel console exporter 输出 trace/metric/log,e2e 全绿

**W2 实际产出**:13 个 commit,198 测试全过(190 unit + 8 e2e),mypy strict 干净,ruff 全绿。Auth middleware 推到 W3 与 Redis auth-store 一起做。Feishu Notifier 完成。

**W2 推迟项**:
- W2.11 Auth middleware:JwtVerifier 已就绪(W1.15),AuthMiddleware ASGI 接线推到 W3(届时和 Redis token-store 一起做)

---

## W3: Postgres + Redis(两个 P0 Integration)

**目标**: 两个 integration 完整通过测试金字塔(unit + integration with testcontainers + e2e + benchmark + chaos)。

待 W2 完成时生成详细 plan。**预计任务**:

- [x] **W3.1** `hwhkit.integrations.postgres.provider.PostgresProvider`(实现 `RelationalDb` contract)
- [x] **W3.2** `hwhkit.integrations.postgres.session` async session factory + per-request middleware
- [x] **W3.3** `hwhkit.integrations.postgres.migrations` alembic 集成
- [x] **W3.4** `hwhkit.integrations.postgres.repository` 通用 Repository 基类
- [x] **W3.5** `hwhkit.testing.fakes.relational_db.FakeRelationalDb`(sqlite memory)
- [x] **W3.6** `hwhkit.testing.contract_tests.relational_db` 契约测试套件
- [x] **W3.7** Postgres integration tests(testcontainers,生命周期/CRUD/重连/慢响应/配置错误)
- [ ] **W3.8** Postgres benchmark(session 申请释放 / 简单 CRUD p99)
- [ ] **W3.9** Postgres chaos(断连 / 慢响应 / 包丢失)
- [x] **W3.10** `hwhkit.integrations.redis.provider.RedisProvider`(实现 `Cache` + `KvStore` + `DistributedLock` + `MessageBus`)
- [x] **W3.11** `hwhkit.integrations.redis.cache.RedisCache`
- [x] **W3.12** `hwhkit.testing.fakes.cache.FakeCache`
- [x] **W3.13** `hwhkit.testing.fakes.message_bus.FakeMessageBus`
- [x] **W3.14** `hwhkit.testing.contract_tests.{cache,kv_store,lock,message_bus}` 契约测试套件
- [x] **W3.15** Redis integration tests(testcontainers,各 contract)
- [ ] **W3.16** Redis benchmark + chaos
- [x] **W3.17** W3 验收:Postgres + Redis 通过完整测试金字塔,覆盖率 ≥90%

---

## W4: Scheduler + NATS(全 P0 完成)

**目标**: P0 完整,可构建完整业务场景。

待 W3 完成时生成详细 plan。**预计任务**:

- [x] **W4.1** `hwhkit.scheduler.provider.SchedulerProvider`(APScheduler 封装,实现 `Scheduler` contract)
- [x] **W4.2** `hwhkit.scheduler.lock` 基于 Redis 的分布式锁(Redlock)
- [x] **W4.3** `hwhkit.scheduler.decorators.@scheduled_task`
- [ ] **W4.4** Scheduler integration tests + benchmark + chaos(多实例不双跑)
- [x] **W4.5** `hwhkit.integrations.nats.provider.NatsProvider`(实现 `MessageBus` contract,JetStream)
- [x] **W4.6** `hwhkit.integrations.nats.publisher`
- [x] **W4.7** `hwhkit.integrations.nats.consumer`(订阅 + 重试 + DLQ)
- [x] **W4.8** `hwhkit.integrations.nats.jetstream` 高级特性
- [x] **W4.9** NATS instrumentation 自实现(traceparent 走 NATS header)
- [ ] **W4.10** NATS integration tests + benchmark + chaos
- [x] **W4.11** W4 验收:全 P0 通过完整测试金字塔

---

## W5: CLI + Testing 完整 + P1 模块

**目标**: `hwhkit init` 一键创建可跑项目;`hwhkit add` 增量加 integration;`hwhkit.testing` 业务方可用;LLM/Auth/Notifier 完整。

待 W4 完成时生成详细 plan。**预计任务**:

- [x] **W5.1** `hwhkit.cli.commands.init` + 项目模板 jinja2
- [x] **W5.2** `hwhkit.cli.commands.add` 框架 + libcst CST 编辑工具
- [x] **W5.3** add postgres 模块(模板 + codemod)
- [x] **W5.4** add redis 模块
- [x] **W5.5** add nats 模块
- [x] **W5.6** add scheduler 模块
- [x] **W5.7** add llm 模块
- [x] **W5.8** add auth 模块
- [x] **W5.9** add otel 模块
- [x] **W5.10** add admin 模块
- [x] **W5.11** `hwhkit.cli.commands.doctor`
- [x] **W5.12** `hwhkit.cli.commands.upgrade` + codemod 基础设施
- [x] **W5.13** `hwhkit.cli.commands.new_integration`
- [x] **W5.14** `hwhkit.cli.commands.gen migration`(alembic wrapper)
- [x] **W5.15** `hwhkit.cli.commands.list` + `version`
- [x] **W5.16** `hwhkit.llm.provider.LlmProvider`(litellm,实现 `LlmClient` + `EmbeddingClient`)
- [x] **W5.17** `hwhkit.testing.fakes.*` 全部 contract 的 fake 完整
- [x] **W5.18** `hwhkit.utils.notification.feishu` 实现 `Notifier` contract
- [x] **W5.19** CLI 测试(`tests/integration/test_cli_init.py`, `test_cli_add.py`)
- [x] **W5.20** W5 验收:`hwhkit init demo-service && cd demo-service && hwhkit add postgres redis nats scheduler && make test` 一气呵成

---

## W6: P2 占位 + 文档 + Release + 业务验证

**目标**: 0.4.0 正式发布。

待 W5 完成时生成详细 plan。**预计任务**:

- [x] **W6.1** `hwhkit.integrations.mysql/` 占位 provider 接口
- [x] **W6.2** `hwhkit.integrations.qdrant/` 占位
- [x] **W6.3** `hwhkit.integrations.mongodb/` 占位
- [x] **W6.4** `hwhkit.integrations.neo4j/` 占位
- [x] **W6.5** `hwhkit.integrations.s3/` 占位
- [x] **W6.6** `hwhkit.integrations.oss/` 占位
- [x] **W6.7** `hwhkit.core.contracts.{vector_store, object_store, graph_db, document_db}` 接口定义
- [ ] **W6.8** 完整文档站内容:`concepts/` 完整
- [ ] **W6.9** 文档站:`integrations/` 每个 integration 一篇
- [ ] **W6.10** 文档站:`contracts/` 每个 contract 规范 + 跨 adapter 行为对照表
- [ ] **W6.11** 文档站:`recipes/`(交易服务、定时任务、事件驱动、AI agent)
- [ ] **W6.12** 文档站:`migration/` 0.x → 1.0 迁移指南
- [ ] **W6.13** 文档站:API ref(mkdocstrings 自动生成 + 校验)
- [ ] **W6.14** `pytest-examples` 校验文档代码块可跑
- [ ] **W6.15** Sigstore 签名 + SBOM 流水线打通
- [ ] **W6.16** Release `0.4.0-rc.1` 到 TestPyPI
- [ ] **W6.17** 业务接入验证(见 spec § 9.4 选项 1 或 2)
- [ ] **W6.18** rc.1 暴露问题修复 → 发 `0.4.0` 正式版
- [ ] **W6.19** 设定 1.0.0 GA 准入清单(spec § 9.5)进度审查
- [ ] **W6.20** W6 验收:`0.4.0` 在 PyPI,文档站完整在 `hwhkit.louishwh.tech`,业务接入冒烟通过

---

## 全局约束(每周都适用)

- 每个 PR 必须 CI 全绿(lint + test + security + license)
- 新代码覆盖率 ≥90%(diff-cover 强制)
- `hwhkit.core` 模块覆盖率始终 ≥95%
- benchmark 回归 >10% 自动 fail
- 每个 P0/P1 integration 必须有 contract test + integration test + chaos test
- 每个 breaking 变更必须配 codemod(在 `hwhkit.cli.commands.upgrade` 注册)
- Conventional Commits 规范,release-please 自动 bump

---

## 不在计划内(不做)

- 多语言 SDK 客户端
- 服务网格 / API 网关
- GUI 管理面板
- P0 阶段实现 P2 integration 的具体逻辑

---

*完。每周完成时,在该周区块勾选完成项,并生成下一周的详细 plan。*
