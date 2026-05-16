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

## D3 — 2026-05-16 — libcst codemod fallback 策略

**决策**:`hwhkit add <module>` 用 libcst 做 CST 编辑;若撞到难处理的 `main.py` 结构,采用 **c)部分降级** —— 能自动改的(import / 简单参数追加)自动改,改不了的打印"请把这 3 行加到此处"提示。

**理由**:保留 90% 一键体验,极端 case 不卡进度。

---

## D4 — 2026-05-16 — W5 末做 mota spike

**决策**:在 W5 末抽 1-2 天做 mota Python 服务接入 spike,而非等到 W6 末才做。

**理由**:0.4.0 是首次对外承诺版本,撞墙宁可早不要晚。代价是 W5 末 CLI 收尾稍赶。

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
