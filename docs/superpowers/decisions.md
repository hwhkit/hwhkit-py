# Decisions Log

> 在 spec 没有明文规定、但执行时必须有立场的决策,记录在这里。
> 每条都标 **何时拍板 / 决策 / 理由**。变更需在本文件里追加,**不删旧条目**。

---

## D1 — 2026-05-16 — sample_app 范围

**决策**:`tests/e2e/sample_app/` 采用 **b)中度** —— /healthz、/readyz、/version、/metrics(框架内置)+ 一个 dummy `GET /items/{id}` + `POST /items` CRUD(内存存储)。

**理由**:比纯极简多一点点工作量,但 W3 写 Postgres 集成测试时可以直接复用同一个业务路由形态(只换底层 store),避免 W3 重新做 sample。

---

## D2 — 2026-05-16 — Postgres Repository 基类不实现

**决策**:`hwhkit.integrations.postgres.repository` **不**提供通用 CRUD 基类。业务代码直接用 `AsyncSession` + SQLAlchemy 2.0 原生 API。

**理由**:Repository pattern 有争议;SQLAlchemy 2.0 async 原生 API 已足够好用;业务方想要自己写一个 30 行基类不难;框架不强加 pattern 更通用。

---

## D3 — 2026-05-16 — libcst codemod 不降级

**决策**:`hwhkit add <module>` 用 libcst 做 CST 编辑;遇到难处理的 `main.py` 结构 **死磕到底,不降级**(原选项 a)。

**作者意图**(2026-05-16 答复 Q3 = a):一键加 integration 是核心承诺,降级到"打印请手动加"会让 CLI 体验严重打折;宁可 W5 延期也要做出来。

**原始候选**:
- a) 死磕 ✅ **采用**
- b) 全降级(只生成新文件 + 打印提示)
- c) 部分降级(原我的倾向)

**影响**:W5 CLI 子任务时间预算需要更宽松。若 libcst 撞墙,我会把"难解析的 main.py 结构样例"记到 decisions 备查,并在 spec 加约束(例如:`bootstrap()` 调用必须在 module-level,不能藏在函数里)而非降级实现。

---

## D4 — 2026-05-16 — mota spike 按原计划放 W6 末

**决策**:**不**前置 mota Python 服务接入 spike。按 spec § 9.4 原计划,W6 末做业务接入验证。W6 暴露的问题在 0.4.x patch 系列消化,1.0 推迟也认。

**作者意图**(2026-05-16 答复 Q4 = b):不必为了"撞墙宁可早"挤压 W5;W6 暴露问题用 0.4.x patch 修是可以接受的轨道。

**影响**:W5 末 CLI 收尾时间宽裕(配合 D3 的"libcst 死磕不降级");W6 业务接入若发现重大设计缺陷,1.0.0 可能推迟到 W7-W8。

---

## D5 — 2026-05-16 — PyPI 账号归属

**决策**:新建 PyPI 组织账号 **`hwhkit`** 发布。

**理由**:GitHub 已经是 `hwhkit/hwhkit-py`,PyPI 一致;PyPI 组织免费;未来转交协作者不用重新申请 namespace。**用户需手动注册 + 启用 2FA + 配 trusted publishing(W6)**。

---

## D6 — 2026-05-16 — rc 观察期 3 天

**决策**:`0.4.0-rc.1` 在 TestPyPI 跑 **3 天**,无问题后发正式 `0.4.0` 到 PyPI。

**理由**:24h 太赶,1 周太慢;3 天够对照 spec § 9.5 的 1.0.0 GA 准入清单。

---

## D7 — 2026-05-16 — 1.0.0 trigger 由用户决定

**决策**:**框架不自动升 1.0.0**。我会备好准入清单逐项打勾,但 release tag 由用户手动触发。

**理由**:1.0 是 SemVer 公开承诺,只能用户拍板。

---

## D8 — 2026-05-16 — OTel 默认采样

**决策**:`observability.sampler.ratio` 默认 `0.1`(prod)/ `1.0`(dev)。

---

## D9 — 2026-05-16 — Container 镜像版本

**决策**:`postgres:16-alpine`、`redis:7-alpine`、`nats:2-alpine`。

---

## D10 — 2026-05-16 — Redis Redlock 节点数

**决策**:默认 **1 节点**(单 Redis);需 5 节点 cluster 时通过 config 多 endpoint 开启。

---

## D11 — 2026-05-16 — NATS JetStream 默认 storage

**决策**:`file`(持久化)生产 / `memory` 仅开发。

---

## D12 — 2026-05-16 — APScheduler jobstore

**决策**:默认 `memory`(开发);Postgres jobstore 通过 config 启用(生产推荐)。

---

## D13 — 2026-05-16 — Feishu Notifier 实现

**决策**:Webhook(Bot URL)方式,**不**走 OAuth。简单可靠。

---

## D14 — 2026-05-16 — LLM 不预设模型

**决策**:`LlmProvider` 不预设默认模型;业务方在 config 显式指定。示例 doc 用 `claude-sonnet-4`。

---

## D15 — 2026-05-16 — Sigstore 签名默认启用

**决策**:发布流程默认 sigstore 签名 + SPDX + CycloneDX SBOM 双导出。

---

## D17 — 2026-05-17 — OTel test isolation:add-processor-not-replace-provider

**触发**:实现 W2 Task 4-5(observability.otel + tracing)单测时,撞到 OTel `set_tracer_provider` 进程级"只能 set 一次"的限制 —— 先跑的 test_otel.py 锁住 global provider 后,test_tracing.py 的 `set_tracer_provider` 被静默忽略,导致 InMemorySpanExporter 收不到 spans。

**决策**:tracing 测试不再尝试替换全局 TracerProvider,改为对当前 global provider 调用 `add_span_processor()` 注入 InMemorySpanExporter。Tests 通过共享 module-level exporter + 每测试 `clear()` 隔离。

**理由**:
- OTel 设计就是"first-set wins";绕过私有 `_TRACER_PROVIDER = None` 仅在某些 SDK 版本有效,跨版本脆弱。
- `add_span_processor()` 是 SDK `TracerProvider` 的**公开 API**,符合 OTel 设计意图(支持多 processor 共存)。
- 业务方未来用 `OtelRecorder` + 自己的 SDK 时也是同样套路,文档可以推荐。

**备选**:
- `pytest-forked` 每测试独立进程 — 过重,CI 慢 5-10 倍。
- monkeypatch `trace._TRACER_PROVIDER` — 私有 API,跨版本脆弱。
- 改 `tracing.py` 接受可注入 tracer — 过度设计,业务从不需要。

**影响**:仅测试代码;`hwhkit/observability/*` 公开 API 不变。文档(W6)recipes 里加一条 "Testing with OTel" 说明此模式。

**回滚成本**:低(只动 `tests/unit/observability/test_tracing.py` 一个文件)。

---

## D18 — 2026-05-17 — OTel `ConsoleLogRecordExporter` rename 兼容

**触发**:W2 Task 4 实现 `_build_log_exporter` 用 `ConsoleLogExporter`,但 OTel SDK 1.41 已弃用此名为 `ConsoleLogRecordExporter`,pytest `filterwarnings = ["error"]` 把 DeprecationWarning 升为错误。

**决策**:`_build_log_exporter` 优先 import 新名 `ConsoleLogRecordExporter`,失败回退老名 `ConsoleLogExporter`(老版本 SDK 兼容)。

**理由**:OTel logs API 仍未 stable,跨版本兼容是常态。Try/except import 是 Python 库 graceful degradation 标准模式。

**影响**:`hwhkit/observability/otel.py:206` 一段代码;无 public API 变化。

**回滚成本**:低。

---

## D19 — 2026-05-17 — OTel SDK 内部类型用 `Any` 而非精确类型

**触发**:`hwhkit/observability/otel.py` 内部 builder helpers 返回 `TracerProvider`/`MeterProvider`/`Resource`/...,mypy `--strict` 要求精确类型 annotation,但这些类型来自 lazy-imported `opentelemetry.sdk.*`(可选 extras `[otel]`)。

**决策**:内部 helper 返回类型用 `Any`。`OtelHandles` 公开 dataclass 字段也用 `Any` + comment 标注语义。

**理由**:
- 这些类型不暴露在 hwhkit public API(`OtelHandles` 只被 bootstrap 内部用)。
- 强类型化要求 `from opentelemetry.sdk.trace import TracerProvider` 在模块顶层 — 会让 `hwhkit.observability.otel` 必须装 otel extras 才能 import,违背"otel default disabled"原则。
- mypy 在 W3+ adapter 模块(postgres/redis/...)仍按 strict 走,因为那些模块强依赖具体 SDK。

**影响**:`hwhkit/observability/otel.py` 内部 helper signatures;无 public API 变化。

**回滚成本**:低(可改回精确类型,只是 import 变重)。

---

## D16 — 2026-05-16 — 中途灰区按局部最优解执行

**决策**:**spec 没明文规定 + 我能给出有理由的局部最优解**的中途灰区,我**不再停下来等审批**,直接按局部最优解执行,并把决策、理由、影响**追加到本文件**(D17+)。**作者可事后追溯并要求修正**。

**作者意图**(2026-05-16 答复 Q8):接受"局部最优 + 留痕"模式,优先保持进度;不接受"绕过 spec 改架构 + 不留痕"。

**触发本规则的灰区类别**(沿用 § 8 "中途灰区"):
- 加新依赖(不在现有 extras 列表)
- 加新 contract / 砍合并 contract
- 测试覆盖率掉到 85% 以下且修不上来
- benchmark baseline 退化 >10% 查不出原因
- chaos test flaky(复现率 <90%)
- license / 安全 / 合规灰区
- 实现时发现 spec 描述模糊或自相矛盾

**例外(仍然停下来等审批)**:
- 改 spec 已明文规定的事(如砍掉 P0 integration、改 SemVer 政策、换 OTel 为别的)
- 任何会让 0.4.0 公开破坏性变更的事
- 任何涉及私钥 / 账号注册 / 钱的事
- 我认为可能让作者后悔的事(留可疑就 ask)

**留痕格式**(每条灰区一个新 D 编号):
```
## DNN — YYYY-MM-DD — <一句话决策>

**触发**:执行 W?.X 时,撞到 <情况>。
**决策**:<我选了什么>。
**理由**:<为什么>。
**备选**:<想过的其他选项 + 为什么没选>。
**影响**:<对哪些子系统 / 哪些任务 / 哪个里程碑有影响>。
**回滚成本**:<高 / 中 / 低,简短说明>。
```

---
