# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
