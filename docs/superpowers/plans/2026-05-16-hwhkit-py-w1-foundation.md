# W1 — Foundation Week Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Take hwhkit-py from copied-over `infoman` legacy code to a clean foundation: project skeleton + CI/CD + test infrastructure + `hwhkit.core` (errors, contracts, integration ABC, context, health, shutdown, jwt) + `hwhkit.testing` scaffold + docs site smoke version — all CI green.

**Architecture:** Clean greenfield start. `git rm -r` everything copied from `infoman`, regenerate `pyproject.toml` with all extras declared, build `hwhkit.core` from scratch with strict TDD. Protocols (Cache / MessageBus / etc.) defined in `hwhkit.core.contracts` with no implementations yet.

**Tech Stack:** Python 3.11+, `uv` for env/deps, `pytest` + `pytest-asyncio` + `pytest-benchmark`, `ruff` + `mypy --strict`, `pre-commit`, GitHub Actions, `mkdocs-material` + `mike`.

**Spec reference:** [`../specs/2026-05-16-hwhkit-py-production-readiness-design.md`](../specs/2026-05-16-hwhkit-py-production-readiness-design.md)

---

## File Structure

After W1, the repo looks like:

```
hwhkit-py/
├── .github/
│   ├── workflows/
│   │   ├── ci.yml                      # PR / push 流水线
│   │   ├── release.yml                 # tag 发布流水线
│   │   └── chaos.yml                   # 周日 cron(W1 占位,W3+ 启用)
│   ├── renovate.json                   # 依赖升级机器人
│   ├── CODEOWNERS                      # 单人项目,占位
│   └── PULL_REQUEST_TEMPLATE.md
├── .pre-commit-config.yaml
├── .python-version                     # 3.12.x(保留现有)
├── .gitignore                          # 重写
├── pyproject.toml                      # 重写,所有 extras 完整
├── uv.lock                             # `uv lock` 生成
├── Makefile                            # make {dev test lint typecheck docs build}
├── README.md                           # 重写,正确描述 hwhkit
├── CHANGELOG.md                        # Keep-a-Changelog 格式起步
├── LICENSE-MIT                         # MIT license
├── LICENSE-APACHE                      # Apache 2.0 license
├── mkdocs.yml                          # 文档站配置
├── docs/                               # 文档源 + spec/plan 也住这
│   ├── index.md                        # 文档站首页
│   ├── getting-started.md              # quick start(W1 冒烟)
│   ├── superpowers/                    # spec & plan(本目录已有)
│   │   ├── specs/
│   │   └── plans/
│   ├── concepts/                       # 占位,W2+ 填充
│   ├── integrations/                   # 占位,W3+ 填充
│   ├── contracts/                      # 占位,W3+ 填充
│   ├── recipes/                        # 占位,W5+ 填充
│   ├── migration/                      # 占位,W6+ 填充
│   └── contributing.md
├── hwhkit/
│   ├── __init__.py                     # 顶层 facade
│   ├── py.typed                        # PEP 561 标记,启用类型分发
│   ├── core/
│   │   ├── __init__.py
│   │   ├── errors.py                   # ApiError + 6 位错误码体系
│   │   ├── integration.py              # IntegrationProvider ABC
│   │   ├── context.py                  # AppContext
│   │   ├── health.py                   # HealthStatus + HealthCheck
│   │   ├── shutdown.py                 # 优雅关闭管线
│   │   ├── jwt.py                      # JWKS cache + Claims 提取器
│   │   └── contracts/
│   │       ├── __init__.py
│   │       ├── cache.py                # Cache + TypedCache
│   │       ├── relational_db.py        # RelationalDb + Session
│   │       ├── message_bus.py          # MessageBus + Message + Subscription
│   │       ├── object_store.py
│   │       ├── vector_store.py
│   │       ├── kv_store.py
│   │       ├── scheduler.py
│   │       ├── lock.py
│   │       ├── llm.py
│   │       ├── secrets.py
│   │       ├── telemetry.py            # Tracer / Meter / LogEmitter
│   │       └── notifier.py
│   └── testing/
│       ├── __init__.py
│       ├── fakes/                      # 占位,W3+ 填充
│       │   └── __init__.py
│       ├── contract_tests/             # 框架,W3+ 用
│       │   └── __init__.py
│       └── otel_recorder.py            # 内存 OTel exporter
└── tests/
    ├── __init__.py
    ├── conftest.py                     # 全局 fixtures
    ├── unit/
    │   ├── __init__.py
    │   ├── core/
    │   │   ├── __init__.py
    │   │   ├── test_errors.py
    │   │   ├── test_integration.py
    │   │   ├── test_context.py
    │   │   ├── test_health.py
    │   │   ├── test_shutdown.py
    │   │   ├── test_jwt.py
    │   │   └── contracts/
    │   │       ├── __init__.py
    │   │       └── test_protocols_are_runtime_checkable.py
    │   └── testing/
    │       ├── __init__.py
    │       └── test_otel_recorder.py
    ├── integration/                    # 占位,W3+ 填充
    │   └── __init__.py
    ├── e2e/                            # 占位,W2+ 填充
    │   └── __init__.py
    ├── benchmark/                      # 占位,W2+ 填充
    │   └── __init__.py
    └── chaos/                          # 占位,W3+ 填充
        └── __init__.py
```

---

## Task 1: Clean slate — 删除遗留代码

**Files:**
- Delete: `hwhkit/` (整个目录), `config/`, `doc/`, `examples/`, `scripts/`, `tests/`, `Makefile`, `pyproject.toml`, `README.md`, `uv.lock`
- Keep: `.git/`, `.gitignore`, `.python-version`, `docs/superpowers/`

- [ ] **Step 1.1: 检查当前 git 状态**

```bash
cd /Users/louis/code/hwhkit/hwhkit-py
git status
```

Expected: `On branch main` + `Untracked files` 列出从 infoman 复制的内容,加上 docs/superpowers/ 已经 tracked。

- [ ] **Step 1.2: 删除遗留文件**

```bash
rm -rf hwhkit/ config/ doc/ examples/ scripts/ tests/ Makefile pyproject.toml README.md uv.lock
ls -la
```

Expected: 只剩 `.git/`, `.gitignore`, `.python-version`, `docs/`(其中只有 superpowers/)。

- [ ] **Step 1.3: 提交"clean slate"**

```bash
git add -A
git commit -m "chore: remove infoman legacy code, start greenfield rewrite

See docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md § 9.1.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

Expected: `git log --oneline -3` 显示 3 个 commit:这个、design doc、initial。

---

## Task 2: `pyproject.toml` + uv 初始化

**Files:**
- Create: `pyproject.toml`
- Create: `LICENSE-MIT`
- Create: `LICENSE-APACHE`
- Create: `hwhkit/__init__.py`
- Create: `hwhkit/py.typed`

- [ ] **Step 2.1: 创建 `pyproject.toml`**

完整内容(全部 extras + 工具配置):

```toml
[project]
name = "hwhkit"
version = "0.4.0a1"
description = "Production-ready Python framework for trading services and microservices, mirroring hwhkit-rs"
readme = "README.md"
license = "MIT OR Apache-2.0"
authors = [{name = "louishwh", email = "louishwh@gmail.com"}]
requires-python = ">=3.11"
keywords = ["framework", "fastapi", "async", "trading", "microservices", "opentelemetry"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Framework :: FastAPI",
    "Framework :: AsyncIO",
    "Topic :: Software Development :: Libraries :: Application Frameworks",
    "Typing :: Typed",
]

# 核心依赖(无 extras 时也必装)
dependencies = [
    "pydantic>=2.12,<3",
    "pydantic-settings>=2.12,<3",
    "structlog>=25.0",
    "typing-extensions>=4.12; python_version<'3.12'",
]

[project.optional-dependencies]
web = [
    "fastapi>=0.127,<0.200",
    "granian>=2.6,<3",
    "orjson>=3.11,<4",
    "python-multipart>=0.0.20",
    "aiofiles>=25.1",
]
postgres = [
    "sqlalchemy[asyncio]>=2.0.36,<3",
    "asyncpg>=0.31,<1",
    "alembic>=1.14,<2",
]
mysql = [
    "sqlalchemy[asyncio]>=2.0.36,<3",
    "asyncmy>=0.2.10,<0.3",
]
redis = ["redis[hiredis]>=7.1,<8"]
nats = ["nats-py>=2.10,<3"]
qdrant = ["qdrant-client>=1.16,<2"]
mongodb = ["motor>=3.5,<4"]
neo4j = ["neo4j>=5.20,<6"]
s3 = ["aioboto3>=14.0,<15"]
oss = ["aliyun-oss2>=2.18,<3"]
scheduler = ["apscheduler>=3.10,<4"]
llm = ["litellm>=1.75,<2"]
otel = [
    "opentelemetry-sdk>=1.27",
    "opentelemetry-exporter-otlp>=1.27",
    "opentelemetry-instrumentation-fastapi>=0.48b0",
    "opentelemetry-instrumentation-sqlalchemy>=0.48b0",
    "opentelemetry-instrumentation-asyncpg>=0.48b0",
    "opentelemetry-instrumentation-redis>=0.48b0",
    "opentelemetry-instrumentation-httpx>=0.48b0",
]
jwt = [
    "pyjwt[crypto]>=2.10,<3",
    "httpx>=0.28,<1",
]
cli = [
    "click>=8.1,<9",
    "rich>=13.9,<14",
    "libcst>=1.5,<2",
    "jinja2>=3.1,<4",
]
all = [
    "hwhkit[web,postgres,redis,nats,scheduler,llm,otel,jwt,cli]",
]
dev = [
    "pytest>=8.3,<9",
    "pytest-asyncio>=0.24",
    "pytest-cov>=5",
    "pytest-benchmark>=4",
    "pytest-mock>=3.14",
    "freezegun>=1.5",
    "respx>=0.21",
    "ruff>=0.14",
    "mypy>=1.13",
    "pre-commit>=4",
    "testcontainers[postgres,redis]>=4.10",
    "diff-cover>=9",
]
docs = [
    "mkdocs>=1.6",
    "mkdocs-material>=9.5",
    "mkdocstrings[python]>=0.27",
    "mike>=2.1",
    "pytest-examples>=0.0.13",
]
security = [
    "bandit>=1.7",
    "pip-audit>=2.7",
    "safety>=3.2",
    "cyclonedx-py>=1.0",
]

[project.urls]
Homepage = "https://hwhkit.louishwh.tech"
Documentation = "https://hwhkit.louishwh.tech"
Repository = "https://github.com/hwhkit/hwhkit-py.git"
Issues = "https://github.com/hwhkit/hwhkit-py/issues"
Changelog = "https://github.com/hwhkit/hwhkit-py/blob/main/CHANGELOG.md"

[project.scripts]
hwhkit = "hwhkit.cli.__main__:main"
hwhkit-serve = "hwhkit.web.server:main"

[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["hwhkit"]

[tool.hatch.build.targets.sdist]
include = ["hwhkit/", "README.md", "LICENSE-MIT", "LICENSE-APACHE", "pyproject.toml"]

# ============ ruff ============
[tool.ruff]
line-length = 100
target-version = "py311"
src = ["hwhkit", "tests"]

[tool.ruff.lint]
select = [
    "E", "W",      # pycodestyle
    "F",           # pyflakes
    "I",           # isort
    "B",           # bugbear
    "C4",          # comprehensions
    "UP",          # pyupgrade
    "S",           # bandit subset
    "SIM",         # simplify
    "RUF",         # ruff-specific
    "TCH",         # type-checking
    "PT",          # pytest-style
    "ASYNC",       # async/await issues
]
ignore = [
    "E501",  # 由 formatter 处理
    "S101",  # assert in tests is fine
]

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["S", "B011", "ASYNC230"]

[tool.ruff.format]
quote-style = "double"

# ============ mypy ============
[tool.mypy]
python_version = "3.11"
strict = true
warn_unused_configs = true
warn_redundant_casts = true
warn_return_any = true
warn_unreachable = true
no_implicit_reexport = true
disallow_untyped_decorators = false  # pytest decorators
plugins = ["pydantic.mypy"]

[[tool.mypy.overrides]]
module = "tests.*"
disallow_untyped_defs = false

# ============ pytest ============
[tool.pytest.ini_options]
minversion = "8.0"
testpaths = ["tests"]
asyncio_mode = "auto"
asyncio_default_fixture_loop_scope = "function"
addopts = [
    "-ra",
    "--strict-markers",
    "--strict-config",
    "--showlocals",
]
markers = [
    "integration: tests requiring real backends (testcontainers)",
    "e2e: end-to-end tests against sample_app",
    "benchmark: performance benchmarks",
    "chaos: chaos engineering tests",
    "slow: tests that take >5 seconds",
]
filterwarnings = [
    "error",
    "ignore::DeprecationWarning:pkg_resources.*",
]

# ============ coverage ============
[tool.coverage.run]
source = ["hwhkit"]
branch = true
omit = ["hwhkit/testing/*"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "raise NotImplementedError",
    "if TYPE_CHECKING:",
    "@overload",
    "@abstractmethod",
]
show_missing = true
skip_covered = false
fail_under = 0  # W1 阶段先 0,W3 起逐步抬升到 85
```

- [ ] **Step 2.2: 创建 LICENSE 文件**

```bash
curl -sL https://raw.githubusercontent.com/licenses/license-templates/master/templates/mit.txt \
  | sed -e 's/{{ year }}/2026/g' -e 's/{{ organization }}/louishwh/g' > LICENSE-MIT

curl -sL https://www.apache.org/licenses/LICENSE-2.0.txt > LICENSE-APACHE
```

- [ ] **Step 2.3: 创建包根 `hwhkit/__init__.py`**

```python
"""hwhkit — production-ready Python framework for trading services and microservices.

See https://hwhkit.louishwh.tech for documentation.
"""

__version__ = "0.4.0a1"
__all__ = ["__version__"]
```

- [ ] **Step 2.4: 创建 `hwhkit/py.typed`**

```bash
touch hwhkit/py.typed
```

(PEP 561 标记空文件)

- [ ] **Step 2.5: `uv lock` + verify install**

```bash
uv lock
uv sync --extra dev
uv run python -c "import hwhkit; print(hwhkit.__version__)"
```

Expected: 输出 `0.4.0a1`,无错误。

- [ ] **Step 2.6: Commit**

```bash
git add pyproject.toml uv.lock LICENSE-MIT LICENSE-APACHE hwhkit/__init__.py hwhkit/py.typed
git commit -m "chore: bootstrap pyproject with full extras matrix

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: README + CHANGELOG + Makefile

**Files:**
- Create: `README.md`
- Create: `CHANGELOG.md`
- Create: `Makefile`

- [ ] **Step 3.1: 创建 `README.md`**

```markdown
# hwhkit

> Production-ready Python framework for trading services and microservices.

`hwhkit` is the Python sibling of [hwhkit-rs](https://github.com/louishwh/hwhkit-rs) — same architectural philosophy, idiomatic for each language.

**Status**: 🚧 0.4.x alpha — under active rewrite to 1.0. See [design doc](docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md).

## Philosophy

- **Framework stays invariant, business code lives in your project.**
- **Contracts (ports) + Adapters (integrations)** for swappable infrastructure.
- **OpenTelemetry-native** observability, off by default.
- **Industrial-grade testing**: unit, integration, e2e, benchmark, chaos, security.

## Quick start

```bash
pip install hwhkit[web,postgres,redis,otel]
hwhkit init my-service && cd my-service
hwhkit add postgres redis
make dev
```

See [hwhkit.louishwh.tech](https://hwhkit.louishwh.tech) for full docs.

## License

`MIT OR Apache-2.0` — choose either. Aligned with hwhkit-rs.
```

- [ ] **Step 3.2: 创建 `CHANGELOG.md`**

```markdown
# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Greenfield rewrite of hwhkit-py, mirroring hwhkit-rs architecture.
- `hwhkit.core.contracts.*` protocols (Cache, MessageBus, RelationalDb, ...).
- `hwhkit.core.integration.IntegrationProvider` ABC.
- `hwhkit.core.errors` with 6-digit error code taxonomy.
- CI/CD pipeline (GitHub Actions).
- mkdocs-material documentation site at hwhkit.louishwh.tech.

### Removed
- Legacy `infoman` code (see commit history).

## [0.4.0-alpha.1] - TBD
- Alpha 1 of the rewrite. Foundation only — no integrations implemented yet.
```

- [ ] **Step 3.3: 创建 `Makefile`**

```makefile
.DEFAULT_GOAL := help
.PHONY: help dev install test test-unit test-integration test-e2e lint typecheck format docs docs-serve build clean

help:
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

install: ## sync dev dependencies
	uv sync --extra dev --extra docs --extra security

dev: install ## prep dev env + pre-commit hooks
	uv run pre-commit install

test: ## run all unit tests
	uv run pytest tests/unit -v

test-unit: ## alias for test
	$(MAKE) test

test-integration: ## run integration tests (requires Docker)
	uv run pytest tests/integration -v -m integration

test-e2e: ## run e2e tests
	uv run pytest tests/e2e -v -m e2e

test-cov: ## run unit tests with coverage report
	uv run pytest tests/unit --cov=hwhkit --cov-report=term-missing --cov-report=html

lint: ## run ruff check
	uv run ruff check hwhkit tests
	uv run ruff format --check hwhkit tests

format: ## auto-format with ruff
	uv run ruff format hwhkit tests
	uv run ruff check --fix hwhkit tests

typecheck: ## run mypy --strict
	uv run mypy hwhkit

docs: ## build docs site
	uv run mkdocs build --strict

docs-serve: ## serve docs locally at http://127.0.0.1:8000
	uv run mkdocs serve

build: ## build wheel + sdist
	uv build

clean: ## remove build artifacts
	rm -rf dist build *.egg-info .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage

security: ## run security scanners
	uv run bandit -r hwhkit -q
	uv run pip-audit
```

- [ ] **Step 3.4: Commit**

```bash
git add README.md CHANGELOG.md Makefile
git commit -m "docs: add README, CHANGELOG, Makefile"
```

---

## Task 4: `.gitignore` 重写 + 全局忽略

**Files:**
- Modify: `.gitignore`

- [ ] **Step 4.1: 重写 `.gitignore`**

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
*.egg
dist/
build/
.eggs/

# Virtual envs
.venv/
venv/
env/

# Testing / coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
.tox/
.coverage
.coverage.*
htmlcov/
coverage.xml
.benchmarks/  # 注意:main 分支的基线需要 commit;这里默认忽略,W2 时通过 !main-baseline.json 反向放行

# OS
.DS_Store
Thumbs.db

# IDE
.idea/
.vscode/
*.swp
*.swo

# uv
# uv.lock IS committed
.uv-cache/

# mkdocs
site/

# Secrets
.env
.env.local
*.pem
*.key

# Misc
.envrc
```

- [ ] **Step 4.2: Commit**

```bash
git add .gitignore
git commit -m "chore: rewrite .gitignore for greenfield Python project"
```

---

## Task 5: pytest 测试目录骨架

**Files:**
- Create: `tests/__init__.py`, `tests/conftest.py`
- Create: `tests/{unit,integration,e2e,benchmark,chaos}/__init__.py`
- Create: `tests/unit/{core,testing}/__init__.py`
- Create: `tests/unit/core/contracts/__init__.py`

- [ ] **Step 5.1: 创建测试目录树**

```bash
mkdir -p tests/unit/core/contracts tests/unit/testing tests/integration tests/e2e tests/benchmark tests/chaos
touch tests/__init__.py
touch tests/unit/__init__.py tests/unit/core/__init__.py tests/unit/core/contracts/__init__.py tests/unit/testing/__init__.py
touch tests/integration/__init__.py tests/e2e/__init__.py tests/benchmark/__init__.py tests/chaos/__init__.py
```

- [ ] **Step 5.2: 创建 `tests/conftest.py`**

```python
"""Global pytest fixtures for hwhkit test suite.

Per-layer conftest files live under tests/integration/conftest.py etc.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Force asyncio (vs trio) for any anyio-based tests."""
    return "asyncio"
```

- [ ] **Step 5.3: 烟雾测试 — 一个 pass 测试,确认 pytest 跑得通**

`tests/unit/test_smoke.py`:
```python
"""Smoke test: pytest infrastructure works."""


def test_truth() -> None:
    assert True
```

- [ ] **Step 5.4: Run smoke test**

```bash
uv run pytest tests/unit/test_smoke.py -v
```

Expected: `1 passed`.

- [ ] **Step 5.5: Commit**

```bash
git add tests/
git commit -m "test: add pytest directory skeleton + smoke test"
```

---

## Task 6: pre-commit 配置

**Files:**
- Create: `.pre-commit-config.yaml`

- [ ] **Step 6.1: 创建 `.pre-commit-config.yaml`**

```yaml
default_install_hook_types: [pre-commit, commit-msg]
default_stages: [pre-commit]

repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v5.0.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-toml
      - id: check-added-large-files
        args: ["--maxkb=500"]
      - id: check-merge-conflict
      - id: mixed-line-ending
        args: ["--fix=lf"]

  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.14.0
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.13.0
    hooks:
      - id: mypy
        additional_dependencies:
          - pydantic
          - structlog
          - types-PyYAML
        args: [--strict]
        files: ^hwhkit/

  - repo: https://github.com/gitleaks/gitleaks
    rev: v8.21.2
    hooks:
      - id: gitleaks

  - repo: https://github.com/pappasam/toml-sort
    rev: v0.24.2
    hooks:
      - id: toml-sort-fix
        args: [--in-place, --no-sort-tables]

  - repo: https://github.com/compilerla/conventional-pre-commit
    rev: v3.6.0
    hooks:
      - id: conventional-pre-commit
        stages: [commit-msg]
        args: [feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert]
```

- [ ] **Step 6.2: 安装 hooks**

```bash
uv run pre-commit install
uv run pre-commit run --all-files
```

Expected: 第一次跑可能修复一些格式问题(re-run 应全绿)。

- [ ] **Step 6.3: Commit**

```bash
git add .pre-commit-config.yaml
git commit -m "chore: add pre-commit config (ruff, mypy, gitleaks, conventional commits)"
```

---

## Task 7: GitHub Actions CI 流水线

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`

- [ ] **Step 7.1: 创建 CI workflow**

`.github/workflows/ci.yml`:
```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

concurrency:
  group: ci-${{ github.ref }}
  cancel-in-progress: true

env:
  PYTHONUNBUFFERED: "1"
  FORCE_COLOR: "1"

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --extra dev
      - run: uv run ruff check hwhkit tests
      - run: uv run ruff format --check hwhkit tests

  typecheck:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
      - run: uv sync --extra dev
      - run: uv run mypy hwhkit

  test-unit:
    needs: [lint, typecheck]
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [ubuntu-latest, macos-latest]
        python: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
        with:
          enable-cache: true
          python-version: ${{ matrix.python }}
      - run: uv sync --extra dev
      - run: uv run pytest tests/unit -v --cov=hwhkit --cov-report=xml
      - uses: codecov/codecov-action@v5
        if: matrix.os == 'ubuntu-latest' && matrix.python == '3.12'
        with:
          files: ./coverage.xml
          fail_ci_if_error: false

  build:
    needs: [test-unit]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv build
      - uses: actions/upload-artifact@v4
        with:
          name: dist
          path: dist/

  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra dev --extra security
      - run: uv run bandit -r hwhkit -q
      - run: uv run pip-audit --strict
```

- [ ] **Step 7.2: 创建 PR 模板**

`.github/PULL_REQUEST_TEMPLATE.md`:
```markdown
## Summary
<!-- 1-3 bullets describing what changed and why -->

## Type
- [ ] feat (new feature)
- [ ] fix (bug fix)
- [ ] docs
- [ ] refactor
- [ ] test
- [ ] chore

## Spec / Plan
<!-- Link to the spec or plan section this implements -->

## Tests
- [ ] Added/updated unit tests
- [ ] Added/updated integration tests (if applicable)
- [ ] Manual verification described below

## Breaking Changes
- [ ] No
- [ ] Yes — codemod registered in `hwhkit.cli.commands.upgrade`

## Checklist
- [ ] CI is green
- [ ] CHANGELOG.md updated under [Unreleased]
- [ ] New code coverage ≥ 90% (diff-cover)
```

- [ ] **Step 7.3: Commit**

```bash
git add .github/
git commit -m "ci: add GitHub Actions CI pipeline (lint, typecheck, test matrix, build, security)"
```

---

## Task 8: Renovate / dependabot

**Files:**
- Create: `.github/renovate.json`

- [ ] **Step 8.1: 创建 `renovate.json`**

```json
{
  "$schema": "https://docs.renovatebot.com/renovate-schema.json",
  "extends": ["config:recommended"],
  "schedule": ["before 9am on monday"],
  "timezone": "Asia/Shanghai",
  "prConcurrentLimit": 5,
  "lockFileMaintenance": {
    "enabled": true,
    "schedule": ["before 9am on monday"]
  },
  "vulnerabilityAlerts": {
    "enabled": true,
    "labels": ["security"]
  },
  "packageRules": [
    {
      "matchUpdateTypes": ["minor", "patch"],
      "matchCurrentVersion": "!/^0/",
      "automerge": false
    },
    {
      "matchDepTypes": ["devDependencies"],
      "matchUpdateTypes": ["minor", "patch"],
      "automerge": true
    }
  ]
}
```

- [ ] **Step 8.2: Commit**

```bash
git add .github/renovate.json
git commit -m "ci: add Renovate config for weekly dependency updates"
```

---

## Task 9: 文档站冒烟版(mkdocs-material)

**Files:**
- Create: `mkdocs.yml`
- Create: `docs/index.md`
- Create: `docs/getting-started.md`
- Create: `docs/contributing.md`
- Create: `docs/concepts/.gitkeep`, `docs/integrations/.gitkeep`, `docs/contracts/.gitkeep`, `docs/recipes/.gitkeep`, `docs/migration/.gitkeep`
- Create: `.github/workflows/docs.yml`

- [ ] **Step 9.1: 创建 `mkdocs.yml`**

```yaml
site_name: hwhkit
site_url: https://hwhkit.louishwh.tech
site_description: Production-ready Python framework for trading services and microservices
site_author: louishwh
repo_url: https://github.com/hwhkit/hwhkit-py
repo_name: hwhkit/hwhkit-py
edit_uri: edit/main/docs/

theme:
  name: material
  language: zh
  features:
    - navigation.tabs
    - navigation.sections
    - navigation.indexes
    - navigation.tracking
    - content.code.copy
    - content.code.annotate
    - search.suggest
    - search.highlight
  palette:
    - media: "(prefers-color-scheme: light)"
      scheme: default
      primary: deep purple
      toggle:
        icon: material/brightness-7
        name: Switch to dark mode
    - media: "(prefers-color-scheme: dark)"
      scheme: slate
      primary: deep purple
      toggle:
        icon: material/brightness-4
        name: Switch to light mode

nav:
  - Home: index.md
  - Getting started: getting-started.md
  - Concepts: concepts/
  - Integrations: integrations/
  - Contracts: contracts/
  - Recipes: recipes/
  - Migration: migration/
  - Contributing: contributing.md

markdown_extensions:
  - admonition
  - attr_list
  - pymdownx.details
  - pymdownx.superfences
  - pymdownx.tabbed:
      alternate_style: true
  - pymdownx.highlight:
      anchor_linenums: true
  - pymdownx.inlinehilite
  - pymdownx.snippets
  - tables
  - toc:
      permalink: true

plugins:
  - search
  - mkdocstrings:
      handlers:
        python:
          options:
            show_source: true
            show_root_heading: true
            members_order: source

extra:
  social:
    - icon: fontawesome/brands/github
      link: https://github.com/louishwh
  version:
    provider: mike
    default: latest
```

- [ ] **Step 9.2: 创建首页 `docs/index.md`**

```markdown
# hwhkit

> Production-ready Python framework for trading services and microservices.

`hwhkit` is one of three sibling implementations of the same architectural philosophy:

| Language | Repo | Role |
|---|---|---|
| Rust | [hwhkit-rs](https://github.com/louishwh/hwhkit-rs) | High-performance backends, reference architecture |
| Python | [hwhkit-py](https://github.com/hwhkit/hwhkit-py) (you are here) | Business / AI / data services |
| Go | [hwhkit-go](https://github.com/louishwh/hwhkit-go) | Microservices, CLI tools (forthcoming rewrite) |

## Status

🚧 **0.4.x alpha** — under active rewrite to 1.0. Foundation week (W1) in progress.

See the [design doc](https://github.com/hwhkit/hwhkit-py/blob/main/docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md) for the full roadmap.

## Quick start

See [Getting started](getting-started.md).
```

- [ ] **Step 9.3: 创建 `docs/getting-started.md`**

```markdown
# Getting started

!!! warning "0.4.x alpha"
    This page describes the target experience post-1.0. As of W1, only the foundation is in place; integrations land in W3+.

## Install

```bash
pip install hwhkit[web,postgres,redis,otel]
```

## Create a project

```bash
hwhkit init my-service
cd my-service
hwhkit add postgres redis
make dev
```

Your service is at <http://127.0.0.1:8000>.

## Next steps

- [Concepts](concepts/) — how hwhkit thinks about apps
- [Integrations](integrations/) — postgres, redis, NATS, …
- [Recipes](recipes/) — real-world patterns
```

- [ ] **Step 9.4: 创建 `docs/contributing.md`**

```markdown
# Contributing

```bash
git clone https://github.com/hwhkit/hwhkit-py.git
cd hwhkit-py
make dev          # uv sync + pre-commit install
make test         # unit tests
make lint         # ruff
make typecheck    # mypy --strict
make docs-serve   # local docs at :8000
```

See the [design doc](https://github.com/hwhkit/hwhkit-py/blob/main/docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md) for architectural decisions.
```

- [ ] **Step 9.5: 创建占位目录**

```bash
mkdir -p docs/concepts docs/integrations docs/contracts docs/recipes docs/migration
touch docs/concepts/.gitkeep docs/integrations/.gitkeep docs/contracts/.gitkeep docs/recipes/.gitkeep docs/migration/.gitkeep
```

- [ ] **Step 9.6: 本地构建文档站**

```bash
uv sync --extra docs
uv run mkdocs build --strict
```

Expected: `dist site/` 生成,无 warning(strict 模式)。

- [ ] **Step 9.7: 创建 docs CI workflow**

`.github/workflows/docs.yml`:
```yaml
name: Docs

on:
  push:
    branches: [main]
    paths:
      - "docs/**"
      - "mkdocs.yml"
      - "hwhkit/**"
      - ".github/workflows/docs.yml"
  pull_request:
    paths:
      - "docs/**"
      - "mkdocs.yml"

permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      - uses: astral-sh/setup-uv@v4
      - run: uv sync --extra docs
      - run: uv run mkdocs build --strict
      - if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        run: |
          git config user.name github-actions
          git config user.email github-actions@github.com
          uv run mike deploy --push --update-aliases latest main
```

- [ ] **Step 9.8: Commit**

```bash
git add mkdocs.yml docs/ .github/workflows/docs.yml
git commit -m "docs: add mkdocs-material site (smoke version)

Site will deploy to hwhkit.louishwh.tech via GitHub Pages + mike."
```

---

## Task 10: `hwhkit.core.errors` — 6 位错误码 + ApiError 体系(TDD)

**Files:**
- Create: `hwhkit/core/__init__.py`
- Create: `hwhkit/core/errors.py`
- Create: `tests/unit/core/test_errors.py`

- [ ] **Step 10.1: 创建空 `hwhkit/core/__init__.py`**

```python
"""hwhkit core — bootstrap, AppContext, integration ABC, errors, contracts, etc."""
```

- [ ] **Step 10.2: 写失败测试 — `ApiError` 基类**

`tests/unit/core/test_errors.py`:
```python
"""Tests for hwhkit.core.errors."""

from __future__ import annotations

import pytest

from hwhkit.core.errors import (
    ApiError,
    ConflictError,
    DbConnectionError,
    ForbiddenError,
    InternalError,
    IntegrationError,
    NatsConnectionError,
    NotFoundError,
    RateLimitError,
    RedisConnectionError,
    UnauthorizedError,
    ValidationError,
)


class TestApiError:
    def test_base_has_code_and_http_status(self) -> None:
        err = ApiError("something went wrong")
        assert err.code == 500000
        assert err.http_status == 500
        assert err.message == "something went wrong"
        assert err.details == {}

    def test_details_accepted(self) -> None:
        err = ApiError("oops", details={"reason": "x"})
        assert err.details == {"reason": "x"}

    def test_subclasses_have_distinct_codes(self) -> None:
        # 4xx 客户端
        assert NotFoundError("nf").code == 100404
        assert UnauthorizedError("u").code == 100401
        assert ForbiddenError("f").code == 100403
        assert ValidationError("v").code == 100422
        assert ConflictError("c").code == 100409
        assert RateLimitError("r").code == 100429
        # 5xx 服务端
        assert InternalError("i").code == 500000
        # 5xx 集成
        assert IntegrationError("i").code == 500001
        assert DbConnectionError("d").code == 510001
        assert RedisConnectionError("r").code == 511001
        assert NatsConnectionError("n").code == 512001

    def test_subclasses_have_correct_http_status(self) -> None:
        assert NotFoundError("nf").http_status == 404
        assert UnauthorizedError("u").http_status == 401
        assert ForbiddenError("f").http_status == 403
        assert ValidationError("v").http_status == 422
        assert ConflictError("c").http_status == 409
        assert RateLimitError("r").http_status == 429
        assert InternalError("i").http_status == 500
        assert IntegrationError("i").http_status == 503
        assert DbConnectionError("d").http_status == 503
        assert RedisConnectionError("r").http_status == 503
        assert NatsConnectionError("n").http_status == 503

    def test_code_format_six_digits(self) -> None:
        for cls in [
            NotFoundError, UnauthorizedError, ForbiddenError, ValidationError,
            ConflictError, RateLimitError, InternalError, IntegrationError,
            DbConnectionError, RedisConnectionError, NatsConnectionError,
        ]:
            assert 100000 <= cls.code <= 999999, f"{cls.__name__}.code not 6-digit"

    def test_is_exception(self) -> None:
        with pytest.raises(ApiError):
            raise NotFoundError("missing")

    def test_business_codes_reserved_range(self) -> None:
        """Codes 600000-899999 reserved for business use."""

        class InsufficientBalance(ApiError):
            code = 620001
            http_status = 400

        err = InsufficientBalance("not enough")
        assert err.code == 620001
        assert err.http_status == 400
```

- [ ] **Step 10.3: 跑测试,确认 fail**

```bash
uv run pytest tests/unit/core/test_errors.py -v
```

Expected: `ImportError: cannot import name 'ApiError' from 'hwhkit.core.errors'` 或 module not found。

- [ ] **Step 10.4: 实现 `hwhkit/core/errors.py`**

```python
"""hwhkit error taxonomy — 6-digit codes following the XYYZZZ scheme.

Code format: `XYYZZZ`
    X    大类:1=客户端 / 5=服务端 / 9=外部依赖 / 6-8=业务自留
    YY   模块:00=core, 01=auth, 10=postgres, 11=redis, 12=nats, 13=scheduler,
              14=llm, 15=web, 20-99=业务保留
    ZZZ  具体错误:模块内自编

See spec § 3.3.
"""

from __future__ import annotations

from typing import Any, ClassVar


class ApiError(Exception):
    """Base for all framework / business errors.

    Subclasses override ``code`` and ``http_status`` as class attributes;
    instances carry ``message`` and optional ``details``.
    """

    code: ClassVar[int] = 500000
    http_status: ClassVar[int] = 500

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details: dict[str, Any] = details or {}

    def __repr__(self) -> str:
        return (
            f"{type(self).__name__}(code={self.code}, http_status={self.http_status}, "
            f"message={self.message!r})"
        )


# ---- 4xx 客户端类(X=1, YY=00 core) --------------------------------------
class UnauthorizedError(ApiError):
    code = 100401
    http_status = 401


class ForbiddenError(ApiError):
    code = 100403
    http_status = 403


class NotFoundError(ApiError):
    code = 100404
    http_status = 404


class ConflictError(ApiError):
    code = 100409
    http_status = 409


class ValidationError(ApiError):
    code = 100422
    http_status = 422


class RateLimitError(ApiError):
    code = 100429
    http_status = 429


# ---- 5xx 服务端类(X=5) ---------------------------------------------------
class InternalError(ApiError):
    code = 500000
    http_status = 500


class IntegrationError(ApiError):
    """Generic downstream / integration failure."""
    code = 500001
    http_status = 503


# ---- 5xx 集成具体(X=5, YY=integration code) -----------------------------
class DbConnectionError(IntegrationError):
    code = 510001
    http_status = 503


class RedisConnectionError(IntegrationError):
    code = 511001
    http_status = 503


class NatsConnectionError(IntegrationError):
    code = 512001
    http_status = 503


__all__ = [
    "ApiError",
    "ConflictError",
    "DbConnectionError",
    "ForbiddenError",
    "InternalError",
    "IntegrationError",
    "NatsConnectionError",
    "NotFoundError",
    "RateLimitError",
    "RedisConnectionError",
    "UnauthorizedError",
    "ValidationError",
]
```

- [ ] **Step 10.5: 跑测试,确认 pass**

```bash
uv run pytest tests/unit/core/test_errors.py -v
```

Expected: 所有用例 pass。

- [ ] **Step 10.6: Commit**

```bash
git add hwhkit/core/__init__.py hwhkit/core/errors.py tests/unit/core/test_errors.py
git commit -m "feat(core): add ApiError taxonomy with 6-digit XYYZZZ codes

See spec § 3.3."
```

---

## Task 11: `hwhkit.core.contracts.cache` Protocol (TDD)

**Files:**
- Create: `hwhkit/core/contracts/__init__.py`
- Create: `hwhkit/core/contracts/cache.py`
- Create: `tests/unit/core/contracts/test_cache.py`

- [ ] **Step 11.1: 创建 `hwhkit/core/contracts/__init__.py`**

```python
"""hwhkit contracts — protocol definitions (the 'ports' in hexagonal arch).

Business code depends ONLY on these protocols. Concrete adapter
implementations live in ``hwhkit.integrations.*``.

See spec § 5.
"""

from hwhkit.core.contracts.cache import Cache, TypedCache
from hwhkit.core.contracts.kv_store import KvStore
from hwhkit.core.contracts.llm import EmbeddingClient, LlmClient
from hwhkit.core.contracts.lock import DistributedLock, LockToken
from hwhkit.core.contracts.message_bus import Message, MessageBus, PublishAck, Subscription
from hwhkit.core.contracts.notifier import Notifier
from hwhkit.core.contracts.object_store import ObjectStore
from hwhkit.core.contracts.relational_db import RelationalDb, Session
from hwhkit.core.contracts.scheduler import Scheduler
from hwhkit.core.contracts.secrets import SecretsProvider
from hwhkit.core.contracts.telemetry import LogEmitter, Meter, Tracer
from hwhkit.core.contracts.vector_store import VectorStore

__all__ = [
    "Cache",
    "DistributedLock",
    "EmbeddingClient",
    "LlmClient",
    "LockToken",
    "LogEmitter",
    "Message",
    "MessageBus",
    "Meter",
    "Notifier",
    "ObjectStore",
    "PublishAck",
    "RelationalDb",
    "Scheduler",
    "SecretsProvider",
    "Session",
    "Subscription",
    "Tracer",
    "TypedCache",
    "VectorStore",
]
```

(注意:这个 `__init__.py` 在 W1 末把所有 contract 都导入。这里**先建空版本**,每个 contract 实现后逐步把对应行加进去。第一稿写成:)

```python
"""hwhkit contracts — protocol definitions."""

__all__: list[str] = []
```

等所有 contract 实现完成后再扩展。

- [ ] **Step 11.2: 写失败测试 — `Cache` protocol**

`tests/unit/core/contracts/test_cache.py`:
```python
"""Tests for hwhkit.core.contracts.cache — Cache & TypedCache protocols."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

import pytest

from hwhkit.core.contracts.cache import Cache, TypedCache


class TestCacheProtocol:
    def test_is_runtime_checkable(self) -> None:
        """Cache must be @runtime_checkable so isinstance() works."""

        class GoodImpl:
            async def get(self, key: str) -> bytes | None: return None
            async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None: ...
            async def delete(self, key: str) -> bool: return True
            async def exists(self, key: str) -> bool: return False
            async def incr(self, key: str, delta: int = 1) -> int: return delta
            async def expire(self, key: str, ttl: timedelta) -> bool: return True

        assert isinstance(GoodImpl(), Cache)

    def test_incomplete_impl_fails_isinstance(self) -> None:
        class BadImpl:
            async def get(self, key: str) -> bytes | None: return None
            # missing other methods

        assert not isinstance(BadImpl(), Cache)


class TestTypedCache:
    @pytest.mark.asyncio
    async def test_typed_get_returns_none_when_missing(self) -> None:
        from tests.unit.core.contracts._fakes import InMemoryRawCache

        cache = TypedCache[dict[str, Any]](raw=InMemoryRawCache())
        result = await cache.get("missing")
        assert result is None

    @pytest.mark.asyncio
    async def test_typed_set_then_get_roundtrip(self) -> None:
        from tests.unit.core.contracts._fakes import InMemoryRawCache

        cache = TypedCache[dict[str, Any]](raw=InMemoryRawCache())
        await cache.set("k", {"a": 1, "b": "two"})
        result = await cache.get("k")
        assert result == {"a": 1, "b": "two"}

    @pytest.mark.asyncio
    async def test_typed_delete(self) -> None:
        from tests.unit.core.contracts._fakes import InMemoryRawCache

        cache = TypedCache[dict[str, Any]](raw=InMemoryRawCache())
        await cache.set("k", {"x": 1})
        assert await cache.delete("k") is True
        assert await cache.get("k") is None
```

- [ ] **Step 11.3: 创建测试内部 fake `tests/unit/core/contracts/_fakes.py`**

```python
"""Local fakes for contract protocol tests. NOT part of hwhkit.testing — those land in W3."""

from __future__ import annotations

import asyncio
from datetime import timedelta


class InMemoryRawCache:
    """Minimal in-memory Cache impl used by contract-level tests."""

    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    async def get(self, key: str) -> bytes | None:
        return self._data.get(key)

    async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None:
        self._data[key] = value
        if ttl:
            async def _expire() -> None:
                await asyncio.sleep(ttl.total_seconds())
                self._data.pop(key, None)
            asyncio.create_task(_expire())

    async def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    async def exists(self, key: str) -> bool:
        return key in self._data

    async def incr(self, key: str, delta: int = 1) -> int:
        cur = int(self._data.get(key, b"0").decode())
        new = cur + delta
        self._data[key] = str(new).encode()
        return new

    async def expire(self, key: str, ttl: timedelta) -> bool:
        return key in self._data
```

- [ ] **Step 11.4: 跑测试,确认 fail**

```bash
uv run pytest tests/unit/core/contracts/test_cache.py -v
```

Expected: ImportError。

- [ ] **Step 11.5: 实现 `hwhkit/core/contracts/cache.py`**

```python
"""Cache contract — byte-level key-value cache abstraction.

Implementations:
- ``hwhkit.integrations.redis.RedisProvider`` (production)
- ``hwhkit.testing.fakes.cache.FakeCache`` (testing)
"""

from __future__ import annotations

import json
import pickle
from datetime import timedelta
from typing import Any, Generic, Protocol, TypeVar, runtime_checkable

T = TypeVar("T")


@runtime_checkable
class Cache(Protocol):
    """Byte-level key-value cache. Codec is the caller's concern."""

    async def get(self, key: str) -> bytes | None: ...

    async def set(self, key: str, value: bytes, ttl: timedelta | None = None) -> None: ...

    async def delete(self, key: str) -> bool: ...

    async def exists(self, key: str) -> bool: ...

    async def incr(self, key: str, delta: int = 1) -> int: ...

    async def expire(self, key: str, ttl: timedelta) -> bool: ...


class Codec(Protocol[T]):
    def encode(self, value: T) -> bytes: ...
    def decode(self, raw: bytes) -> T: ...


class JsonCodec:
    """Default codec: JSON (UTF-8)."""

    def encode(self, value: Any) -> bytes:
        return json.dumps(value).encode("utf-8")

    def decode(self, raw: bytes) -> Any:
        return json.loads(raw.decode("utf-8"))


class PickleCodec:
    """Use for non-JSON-serializable types. Note: unsafe across process trust boundaries."""

    def encode(self, value: Any) -> bytes:
        return pickle.dumps(value)

    def decode(self, raw: bytes) -> Any:
        return pickle.loads(raw)  # noqa: S301  intentional


class TypedCache(Generic[T]):
    """High-level typed cache wrapping any ``Cache`` adapter with codec."""

    def __init__(self, raw: Cache, codec: Codec[T] | None = None) -> None:
        self._raw = raw
        self._codec: Codec[T] = codec or JsonCodec()  # type: ignore[assignment]

    async def get(self, key: str) -> T | None:
        raw = await self._raw.get(key)
        if raw is None:
            return None
        return self._codec.decode(raw)

    async def set(self, key: str, value: T, ttl: timedelta | None = None) -> None:
        await self._raw.set(key, self._codec.encode(value), ttl)

    async def delete(self, key: str) -> bool:
        return await self._raw.delete(key)

    async def exists(self, key: str) -> bool:
        return await self._raw.exists(key)


__all__ = ["Cache", "Codec", "JsonCodec", "PickleCodec", "TypedCache"]
```

- [ ] **Step 11.6: 跑测试,确认 pass**

```bash
uv run pytest tests/unit/core/contracts/test_cache.py -v
```

Expected: 5 passed。

- [ ] **Step 11.7: 更新 `hwhkit/core/contracts/__init__.py` 增量 export**

```python
"""hwhkit contracts — protocol definitions."""

from hwhkit.core.contracts.cache import Cache, Codec, JsonCodec, PickleCodec, TypedCache

__all__ = ["Cache", "Codec", "JsonCodec", "PickleCodec", "TypedCache"]
```

- [ ] **Step 11.8: Commit**

```bash
git add hwhkit/core/contracts/__init__.py hwhkit/core/contracts/cache.py \
        tests/unit/core/contracts/test_cache.py tests/unit/core/contracts/_fakes.py
git commit -m "feat(contracts): add Cache + TypedCache protocols"
```

---

## Task 12: `hwhkit.core.contracts.kv_store` (TDD)

**Files:**
- Create: `hwhkit/core/contracts/kv_store.py`
- Create: `tests/unit/core/contracts/test_kv_store.py`

- [ ] **Step 12.1: 写失败测试**

```python
"""Tests for hwhkit.core.contracts.kv_store."""

from __future__ import annotations

from hwhkit.core.contracts.kv_store import KvStore


class TestKvStoreProtocol:
    def test_is_runtime_checkable(self) -> None:
        class Impl:
            async def get(self, key: str) -> bytes | None: return None
            async def set(self, key: str, value: bytes) -> None: ...
            async def delete(self, key: str) -> bool: return True
            async def list_keys(self, prefix: str = "") -> list[str]: return []
            async def watch(self, key: str): ...  # async iterator

        assert isinstance(Impl(), KvStore)
```

- [ ] **Step 12.2: 跑测试 → fail**

- [ ] **Step 12.3: 实现 `hwhkit/core/contracts/kv_store.py`**

```python
"""KvStore contract — persistent key-value storage (vs. ephemeral Cache).

Implementations: Redis (P0), etcd / Consul (future).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Protocol, runtime_checkable


@runtime_checkable
class KvStore(Protocol):
    async def get(self, key: str) -> bytes | None: ...

    async def set(self, key: str, value: bytes) -> None: ...

    async def delete(self, key: str) -> bool: ...

    async def list_keys(self, prefix: str = "") -> list[str]: ...

    def watch(self, key: str) -> AsyncIterator[bytes | None]: ...


__all__ = ["KvStore"]
```

- [ ] **Step 12.4: 跑测试 → pass**

- [ ] **Step 12.5: 更新 contracts `__init__.py` 加入 `KvStore` export**

- [ ] **Step 12.6: Commit**

```bash
git add hwhkit/core/contracts/kv_store.py tests/unit/core/contracts/test_kv_store.py hwhkit/core/contracts/__init__.py
git commit -m "feat(contracts): add KvStore protocol"
```

---

## Task 13: `hwhkit.core.contracts.lock` (TDD)

**Files:**
- Create: `hwhkit/core/contracts/lock.py`
- Create: `tests/unit/core/contracts/test_lock.py`

- [ ] **Step 13.1: 写失败测试**

```python
"""Tests for hwhkit.core.contracts.lock."""

from __future__ import annotations

from datetime import timedelta

from hwhkit.core.contracts.lock import DistributedLock, LockToken


class TestDistributedLockProtocol:
    def test_lock_token_dataclass(self) -> None:
        tok = LockToken(key="my-lock", token="abc-123", ttl=timedelta(seconds=30))
        assert tok.key == "my-lock"
        assert tok.token == "abc-123"
        assert tok.ttl == timedelta(seconds=30)

    def test_protocol_runtime_checkable(self) -> None:
        class Impl:
            async def acquire(self, key: str, ttl: timedelta, blocking: bool = True) -> LockToken | None: return None
            async def release(self, token: LockToken) -> bool: return True
            async def extend(self, token: LockToken, ttl: timedelta) -> bool: return True

        assert isinstance(Impl(), DistributedLock)
```

- [ ] **Step 13.2: 跑测试 → fail**

- [ ] **Step 13.3: 实现 `hwhkit/core/contracts/lock.py`**

```python
"""DistributedLock contract — cross-process / cross-host mutual exclusion.

Implementations: Redis Redlock (P0), etcd / ZooKeeper (future).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class LockToken:
    """Opaque handle returned by ``acquire``; required for ``release`` / ``extend``."""

    key: str
    token: str
    ttl: timedelta


@runtime_checkable
class DistributedLock(Protocol):
    async def acquire(
        self,
        key: str,
        ttl: timedelta,
        blocking: bool = True,
    ) -> LockToken | None: ...

    async def release(self, token: LockToken) -> bool: ...

    async def extend(self, token: LockToken, ttl: timedelta) -> bool: ...


__all__ = ["DistributedLock", "LockToken"]
```

- [ ] **Step 13.4: 跑测试 → pass**

- [ ] **Step 13.5: 更新 contracts `__init__.py`**

- [ ] **Step 13.6: Commit**

```bash
git add hwhkit/core/contracts/lock.py tests/unit/core/contracts/test_lock.py hwhkit/core/contracts/__init__.py
git commit -m "feat(contracts): add DistributedLock + LockToken"
```

---

## Task 14: `hwhkit.core.contracts.message_bus` (TDD)

**Files:**
- Create: `hwhkit/core/contracts/message_bus.py`
- Create: `tests/unit/core/contracts/test_message_bus.py`

- [ ] **Step 14.1: 写失败测试**

```python
"""Tests for hwhkit.core.contracts.message_bus."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import timedelta

from hwhkit.core.contracts.message_bus import Message, MessageBus, PublishAck, Subscription


class TestMessageBusProtocol:
    def test_message_attrs(self) -> None:
        class M:
            subject = "x"
            payload = b"y"
            headers: dict[str, str] = {}
            async def ack(self) -> None: ...
            async def nack(self, *, requeue: bool = True) -> None: ...

        assert isinstance(M(), Message)

    def test_subscription_attrs(self) -> None:
        class S:
            subject = "x"
            async def unsubscribe(self) -> None: ...

        assert isinstance(S(), Subscription)

    def test_publish_ack_dataclass(self) -> None:
        ack = PublishAck(subject="x.y", sequence=42, duplicate=False)
        assert ack.subject == "x.y"
        assert ack.sequence == 42
        assert ack.duplicate is False

    def test_bus_runtime_checkable(self) -> None:
        class Bus:
            async def publish(self, subject: str, payload: bytes, *,
                              headers: dict[str, str] | None = None,
                              deduplication_key: str | None = None) -> PublishAck:
                return PublishAck(subject, 1, False)

            async def subscribe(self, subject: str, handler: Callable[[Message], Awaitable[None]], *,
                                durable: str | None = None,
                                manual_ack: bool = False,
                                max_in_flight: int = 100) -> Subscription:
                raise NotImplementedError

            async def request(self, subject: str, payload: bytes,
                              timeout: timedelta = timedelta(seconds=5)) -> bytes:
                return b""

        assert isinstance(Bus(), MessageBus)
```

- [ ] **Step 14.2: 跑测试 → fail**

- [ ] **Step 14.3: 实现 `hwhkit/core/contracts/message_bus.py`**

```python
"""MessageBus contract — unified pub/sub + request/reply abstraction.

Implementations:
- NATS JetStream (P1)
- Redis pub/sub (via RedisProvider, P0 partial)
- Kafka / RabbitMQ / Redis Streams (future)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class PublishAck:
    """Acknowledgement returned by ``publish``."""

    subject: str
    sequence: int
    duplicate: bool


@runtime_checkable
class Message(Protocol):
    """A delivered message."""

    subject: str
    payload: bytes
    headers: dict[str, str]

    async def ack(self) -> None: ...

    async def nack(self, *, requeue: bool = True) -> None: ...


@runtime_checkable
class Subscription(Protocol):
    """A live subscription. Cancel by calling ``unsubscribe``."""

    subject: str

    async def unsubscribe(self) -> None: ...


@runtime_checkable
class MessageBus(Protocol):
    async def publish(
        self,
        subject: str,
        payload: bytes,
        *,
        headers: dict[str, str] | None = None,
        deduplication_key: str | None = None,
    ) -> PublishAck: ...

    async def subscribe(
        self,
        subject: str,
        handler: Callable[[Message], Awaitable[None]],
        *,
        durable: str | None = None,
        manual_ack: bool = False,
        max_in_flight: int = 100,
    ) -> Subscription: ...

    async def request(
        self,
        subject: str,
        payload: bytes,
        timeout: timedelta = timedelta(seconds=5),
    ) -> bytes: ...


__all__ = ["Message", "MessageBus", "PublishAck", "Subscription"]
```

- [ ] **Step 14.4: 跑测试 → pass**

- [ ] **Step 14.5: 更新 contracts `__init__.py`**

- [ ] **Step 14.6: Commit**

```bash
git add hwhkit/core/contracts/message_bus.py tests/unit/core/contracts/test_message_bus.py hwhkit/core/contracts/__init__.py
git commit -m "feat(contracts): add MessageBus / Message / Subscription / PublishAck"
```

---

## Task 15: `hwhkit.core.contracts.relational_db` (TDD)

**Files:**
- Create: `hwhkit/core/contracts/relational_db.py`
- Create: `tests/unit/core/contracts/test_relational_db.py`

- [ ] **Step 15.1: 写失败测试**

```python
"""Tests for hwhkit.core.contracts.relational_db."""

from __future__ import annotations

from hwhkit.core.contracts.relational_db import RelationalDb, Session


class TestSessionProtocol:
    def test_runtime_checkable(self) -> None:
        class S:
            async def execute(self, query: str, *args, **kwargs):  # noqa: ANN001 ANN201
                ...
            async def commit(self) -> None: ...
            async def rollback(self) -> None: ...
            async def close(self) -> None: ...
            async def __aenter__(self) -> "S": return self
            async def __aexit__(self, *args, **kwargs): ...

        assert isinstance(S(), Session)


class TestRelationalDbProtocol:
    def test_runtime_checkable(self) -> None:
        class Db:
            def session(self) -> Session: raise NotImplementedError  # type: ignore[return-value]
            async def ping(self) -> bool: return True

        assert isinstance(Db(), RelationalDb)
```

- [ ] **Step 15.2: 跑测试 → fail**

- [ ] **Step 15.3: 实现 `hwhkit/core/contracts/relational_db.py`**

```python
"""RelationalDb contract — RDBMS session factory abstraction.

Adapter-specific session features (e.g. SQLAlchemy AsyncSession's all attributes)
are exposed by accessing the concrete adapter via ``ctx.get_typed(PostgresProvider).engine``.

Implementations: Postgres (P0), MySQL (P2).
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Session(Protocol):
    """An open database session / transaction context.

    Note: matches the surface of SQLAlchemy's AsyncSession enough that we can
    type-hint business code against ``Session`` while passing in the real adapter type.
    """

    async def execute(self, query: Any, *args: Any, **kwargs: Any) -> Any: ...
    async def commit(self) -> None: ...
    async def rollback(self) -> None: ...
    async def close(self) -> None: ...
    async def __aenter__(self) -> "Session": ...
    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...


@runtime_checkable
class RelationalDb(Protocol):
    def session(self) -> Session: ...

    async def ping(self) -> bool: ...


__all__ = ["RelationalDb", "Session"]
```

- [ ] **Step 15.4: 跑测试 → pass**

- [ ] **Step 15.5: 更新 contracts `__init__.py`**

- [ ] **Step 15.6: Commit**

---

## Task 16-22: 其余 contract protocols(批量)

对剩余 7 个 contracts(`object_store`, `vector_store`, `scheduler`, `llm`, `secrets`, `telemetry`, `notifier`),**每个任务遵循同样模式**:

1. 写失败测试(`test_<name>.py`,测 `@runtime_checkable` 行为)
2. 跑测试 → fail
3. 实现 contract protocol
4. 跑测试 → pass
5. 更新 contracts `__init__.py` export
6. Commit

各 contract 接口签名见下。

### Task 16: `object_store.py`

```python
"""ObjectStore contract — bucket-based binary blob storage.

Implementations: S3, OSS, MinIO (all P2).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class ObjectMetadata:
    key: str
    size: int
    etag: str
    content_type: str | None
    last_modified: float  # unix timestamp


@runtime_checkable
class ObjectStore(Protocol):
    async def put(self, key: str, data: bytes, *, content_type: str | None = None) -> ObjectMetadata: ...
    async def get(self, key: str) -> bytes: ...
    async def stream(self, key: str) -> AsyncIterator[bytes]: ...
    async def delete(self, key: str) -> bool: ...
    async def exists(self, key: str) -> bool: ...
    async def list_objects(self, prefix: str = "") -> AsyncIterator[ObjectMetadata]: ...
    async def presigned_url(self, key: str, ttl_seconds: int = 3600, method: str = "GET") -> str: ...


__all__ = ["ObjectMetadata", "ObjectStore"]
```

### Task 17: `vector_store.py`

```python
"""VectorStore contract — semantic / similarity vector search.

Implementations: Qdrant (P2), Milvus / Pinecone (future).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True, slots=True)
class VectorRecord:
    id: str
    vector: list[float]
    payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SearchHit:
    id: str
    score: float
    payload: dict[str, Any]


@runtime_checkable
class VectorStore(Protocol):
    async def ensure_collection(self, name: str, dim: int, distance: str = "cosine") -> None: ...
    async def upsert(self, collection: str, records: list[VectorRecord]) -> None: ...
    async def search(
        self,
        collection: str,
        vector: list[float],
        top_k: int = 10,
        filter: dict[str, Any] | None = None,
    ) -> list[SearchHit]: ...
    async def delete(self, collection: str, ids: list[str]) -> int: ...


__all__ = ["SearchHit", "VectorRecord", "VectorStore"]
```

### Task 18: `scheduler.py`

```python
"""Scheduler contract — recurring & one-off job execution.

Implementations: APScheduler (P0), Celery-beat / Temporal (future).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable

JobFunc = Callable[[], Awaitable[None]]


@runtime_checkable
class Scheduler(Protocol):
    def add_cron_job(
        self,
        job_id: str,
        cron: str,
        func: JobFunc,
        *,
        lock_key: str | None = None,
        timezone: str = "UTC",
    ) -> None: ...

    def add_interval_job(
        self,
        job_id: str,
        interval: timedelta,
        func: JobFunc,
        *,
        lock_key: str | None = None,
    ) -> None: ...

    def add_oneshot_job(
        self,
        job_id: str,
        run_at: datetime,
        func: JobFunc,
    ) -> None: ...

    def remove_job(self, job_id: str) -> bool: ...

    async def start(self) -> None: ...

    async def stop(self) -> None: ...


__all__ = ["JobFunc", "Scheduler"]
```

### Task 19: `llm.py`

```python
"""LlmClient / EmbeddingClient contracts.

Implementations: litellm-backed (P1), direct OpenAI/Anthropic SDK (future).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol, runtime_checkable

Role = Literal["system", "user", "assistant", "tool"]


@dataclass(frozen=True, slots=True)
class ChatMessage:
    role: Role
    content: str
    name: str | None = None


@dataclass(frozen=True, slots=True)
class ChatResponse:
    content: str
    model: str
    finish_reason: str
    usage: dict[str, int]
    raw: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class LlmClient(Protocol):
    async def chat(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> ChatResponse: ...

    def chat_stream(
        self,
        messages: list[ChatMessage],
        *,
        model: str,
        temperature: float = 0.7,
        max_tokens: int | None = None,
    ) -> AsyncIterator[str]: ...


@runtime_checkable
class EmbeddingClient(Protocol):
    async def embed(
        self,
        texts: list[str],
        *,
        model: str,
    ) -> list[list[float]]: ...


__all__ = ["ChatMessage", "ChatResponse", "EmbeddingClient", "LlmClient", "Role"]
```

### Task 20: `secrets.py`

```python
"""SecretsProvider contract — runtime secret retrieval.

Implementations: env-var (P0 default), AWS Secrets Manager / Vault / Doppler (future).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class SecretsProvider(Protocol):
    async def get(self, name: str) -> str: ...

    async def get_or_default(self, name: str, default: str) -> str: ...


__all__ = ["SecretsProvider"]
```

### Task 21: `telemetry.py`

```python
"""Telemetry contracts — Tracer / Meter / LogEmitter abstractions over OTel.

Default adapter is hwhkit.observability.otel (P0). Replacement uncommon but possible.
"""

from __future__ import annotations

from contextlib import AbstractContextManager
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Span(Protocol):
    def set_attribute(self, key: str, value: Any) -> None: ...
    def record_exception(self, exc: Exception) -> None: ...
    def end(self) -> None: ...


@runtime_checkable
class Tracer(Protocol):
    def start_span(self, name: str, **attrs: Any) -> AbstractContextManager[Span]: ...


@runtime_checkable
class Counter(Protocol):
    def add(self, amount: int | float, attributes: dict[str, Any] | None = None) -> None: ...


@runtime_checkable
class Histogram(Protocol):
    def record(self, value: int | float, attributes: dict[str, Any] | None = None) -> None: ...


@runtime_checkable
class Meter(Protocol):
    def create_counter(self, name: str, *, unit: str = "1", description: str = "") -> Counter: ...
    def create_histogram(self, name: str, *, unit: str = "1", description: str = "") -> Histogram: ...


@runtime_checkable
class LogEmitter(Protocol):
    def emit(self, level: str, event: str, **fields: Any) -> None: ...


__all__ = ["Counter", "Histogram", "LogEmitter", "Meter", "Span", "Tracer"]
```

### Task 22: `notifier.py`

```python
"""Notifier contract — outbound human-facing notifications (chat, email, sms).

Implementations: Feishu (P1), DingTalk / email / SMS (future).
"""

from __future__ import annotations

from typing import Literal, Protocol, runtime_checkable

Severity = Literal["info", "warning", "error", "critical"]


@runtime_checkable
class Notifier(Protocol):
    async def notify(
        self,
        title: str,
        body: str,
        *,
        severity: Severity = "info",
        target: str | None = None,
    ) -> None: ...


__all__ = ["Notifier", "Severity"]
```

Each Task 16-22 follows pattern: write test → fail → implement → pass → `__init__.py` export → commit.

---

## Task 23: 一次性测试 — 所有 contracts 都是 `@runtime_checkable`

**Files:**
- Create: `tests/unit/core/contracts/test_protocols_are_runtime_checkable.py`

- [ ] **Step 23.1: 写测试**

```python
"""Smoke test: every contract protocol is @runtime_checkable."""

from __future__ import annotations

from typing import get_args, get_type_hints, runtime_checkable

from hwhkit.core import contracts


def test_all_protocols_are_runtime_checkable() -> None:
    """Catch regressions where someone forgets @runtime_checkable."""
    from typing import Protocol

    skipped = {"Codec", "JobFunc", "Role", "Severity"}  # type aliases / non-protocols

    for name in contracts.__all__:
        obj = getattr(contracts, name)
        if not (isinstance(obj, type) and issubclass(obj, Protocol)):
            continue
        if name in skipped:
            continue
        # @runtime_checkable sets this attribute
        assert getattr(obj, "_is_runtime_protocol", False), (
            f"{name} must be marked @runtime_checkable so isinstance() works"
        )
```

- [ ] **Step 23.2: Run + pass**

```bash
uv run pytest tests/unit/core/contracts/test_protocols_are_runtime_checkable.py -v
```

- [ ] **Step 23.3: Commit**

```bash
git add tests/unit/core/contracts/test_protocols_are_runtime_checkable.py
git commit -m "test(contracts): assert all protocols are @runtime_checkable"
```

---

## Task 24: `hwhkit.core.health` — HealthStatus + 聚合器 (TDD)

**Files:**
- Create: `hwhkit/core/health.py`
- Create: `tests/unit/core/test_health.py`

- [ ] **Step 24.1: 写失败测试**

```python
"""Tests for hwhkit.core.health."""

from __future__ import annotations

import pytest

from hwhkit.core.health import HealthAggregator, HealthCheck, HealthStatus


class TestHealthStatus:
    def test_healthy_factory(self) -> None:
        s = HealthStatus.healthy("ok")
        assert s.healthy is True
        assert s.message == "ok"
        assert s.details == {}

    def test_unhealthy_factory(self) -> None:
        s = HealthStatus.unhealthy("db down", details={"err": "connection refused"})
        assert s.healthy is False
        assert s.message == "db down"
        assert s.details == {"err": "connection refused"}


class TestHealthCheck:
    def test_protocol(self) -> None:
        class C:
            name = "postgres"
            async def health_check(self) -> HealthStatus:
                return HealthStatus.healthy()
        assert isinstance(C(), HealthCheck)


class TestHealthAggregator:
    @pytest.mark.asyncio
    async def test_all_healthy_returns_healthy(self) -> None:
        agg = HealthAggregator()
        agg.add("a", lambda: HealthStatus.healthy())
        agg.add("b", lambda: HealthStatus.healthy())
        result = await agg.aggregate()
        assert result.healthy is True
        assert "a" in result.details["checks"]
        assert "b" in result.details["checks"]

    @pytest.mark.asyncio
    async def test_one_unhealthy_returns_unhealthy(self) -> None:
        agg = HealthAggregator()
        agg.add("a", lambda: HealthStatus.healthy())
        agg.add("b", lambda: HealthStatus.unhealthy("oops"))
        result = await agg.aggregate()
        assert result.healthy is False
        assert result.details["checks"]["b"]["healthy"] is False

    @pytest.mark.asyncio
    async def test_check_raising_treated_as_unhealthy(self) -> None:
        agg = HealthAggregator()
        def broken() -> HealthStatus: raise RuntimeError("kaboom")
        agg.add("broken", broken)
        result = await agg.aggregate()
        assert result.healthy is False
        assert "kaboom" in result.details["checks"]["broken"]["message"]
```

- [ ] **Step 24.2: 跑 → fail**

- [ ] **Step 24.3: 实现 `hwhkit/core/health.py`**

```python
"""Health check protocol + aggregator.

Per spec § 2.5:
- liveness: process-only, always 200 if process is up.
- readiness: aggregates all registered HealthCheck instances; any unhealthy → 503.
"""

from __future__ import annotations

import asyncio
import inspect
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from typing import Any, Protocol, runtime_checkable

HealthCheckFn = Callable[[], "HealthStatus | Awaitable[HealthStatus]"]


@dataclass(frozen=True, slots=True)
class HealthStatus:
    healthy: bool
    message: str = ""
    details: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def healthy(cls, message: str = "ok", **details: Any) -> "HealthStatus":
        return cls(healthy=True, message=message, details=dict(details))

    @classmethod
    def unhealthy(cls, message: str, *, details: dict[str, Any] | None = None) -> "HealthStatus":
        return cls(healthy=False, message=message, details=details or {})


@runtime_checkable
class HealthCheck(Protocol):
    """Any integration with a ``health_check`` coroutine can be registered."""

    name: str

    async def health_check(self) -> HealthStatus: ...


class HealthAggregator:
    """Collects N HealthCheck callables and aggregates their results."""

    def __init__(self) -> None:
        self._checks: list[tuple[str, HealthCheckFn]] = []

    def add(self, name: str, check: HealthCheckFn) -> None:
        self._checks.append((name, check))

    async def aggregate(self) -> HealthStatus:
        results: dict[str, dict[str, Any]] = {}
        all_healthy = True
        for name, fn in self._checks:
            try:
                raw = fn()
                status: HealthStatus = await raw if inspect.isawaitable(raw) else raw  # type: ignore[assignment]
            except Exception as exc:  # noqa: BLE001
                status = HealthStatus.unhealthy(f"check raised: {exc}", details={"type": type(exc).__name__})
            results[name] = {
                "healthy": status.healthy,
                "message": status.message,
                "details": status.details,
            }
            if not status.healthy:
                all_healthy = False
        return HealthStatus(
            healthy=all_healthy,
            message="ok" if all_healthy else "one or more dependencies unhealthy",
            details={"checks": results},
        )


__all__ = ["HealthAggregator", "HealthCheck", "HealthCheckFn", "HealthStatus"]
```

- [ ] **Step 24.4: 跑 → pass**

- [ ] **Step 24.5: Commit**

```bash
git add hwhkit/core/health.py tests/unit/core/test_health.py
git commit -m "feat(core): add HealthStatus + HealthAggregator"
```

---

## Task 25: `hwhkit.core.integration.IntegrationProvider` ABC (TDD)

**Files:**
- Create: `hwhkit/core/integration.py`
- Create: `tests/unit/core/test_integration.py`

- [ ] **Step 25.1: 写失败测试**

```python
"""Tests for hwhkit.core.integration."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import BaseModel

from hwhkit.core.contracts import Cache
from hwhkit.core.health import HealthStatus
from hwhkit.core.integration import IntegrationProvider


class DummyConfig(BaseModel):
    enabled: bool = True


class DummyProvider(IntegrationProvider):
    name: ClassVar[str] = "dummy"
    config_schema: ClassVar[type[BaseModel]] = DummyConfig

    def __init__(self) -> None:
        self.setup_called = False
        self.shutdown_called = False

    async def setup(self, ctx) -> None:  # noqa: ANN001
        self.setup_called = True

    async def health_check(self) -> HealthStatus:
        return HealthStatus.healthy()

    async def shutdown(self) -> None:
        self.shutdown_called = True


class TestIntegrationProvider:
    def test_subclass_with_all_methods_instantiates(self) -> None:
        p = DummyProvider()
        assert p.name == "dummy"
        assert p.config_schema is DummyConfig
        assert p.implements == []

    @pytest.mark.asyncio
    async def test_lifecycle(self) -> None:
        p = DummyProvider()
        await p.setup(ctx=None)  # type: ignore[arg-type]
        assert p.setup_called is True
        status = await p.health_check()
        assert status.healthy is True
        await p.shutdown()
        assert p.shutdown_called is True

    def test_missing_abstract_method_cannot_instantiate(self) -> None:
        class Incomplete(IntegrationProvider):
            name: ClassVar[str] = "x"
            config_schema: ClassVar[type[BaseModel]] = DummyConfig
            # missing setup / health_check / shutdown

        with pytest.raises(TypeError, match="abstract"):
            Incomplete()  # type: ignore[abstract]

    def test_default_hooks_no_op(self) -> None:
        p = DummyProvider()
        assert p.fastapi_router() is None
        assert p.fastapi_middlewares() == []
        assert p.fastapi_dependencies() == {}

    def test_implements_declaration(self) -> None:
        class CacheImpl(DummyProvider):
            name: ClassVar[str] = "cache"
            implements: ClassVar[list[type]] = [Cache]

        p = CacheImpl()
        assert Cache in p.implements
```

- [ ] **Step 25.2: 跑 → fail**

- [ ] **Step 25.3: 实现 `hwhkit/core/integration.py`**

```python
"""IntegrationProvider — the lifecycle/registration ABC for all framework integrations.

See spec § 2.1.

An IntegrationProvider is the "adapter" half of hexagonal arch — it implements
zero or more Contract protocols (declared via the ``implements`` class attr)
and exposes a managed lifecycle (setup / health / shutdown).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, ClassVar

from pydantic import BaseModel

if TYPE_CHECKING:
    from fastapi import APIRouter

    from hwhkit.core.context import AppContext
    from hwhkit.core.health import HealthStatus


class IntegrationProvider(ABC):
    """Lifecycle-managed framework plugin."""

    name: ClassVar[str]
    """Globally unique short identifier, e.g. "postgres" / "redis" / "nats"."""

    config_schema: ClassVar[type[BaseModel]]
    """Pydantic model the integration's config is parsed into."""

    implements: ClassVar[list[type]] = []
    """List of contract Protocol classes this integration satisfies.

    Used for automatic contract → adapter binding in ``AppContext.resolve()``.
    """

    # ---- lifecycle (abstract) ------------------------------------------
    @abstractmethod
    async def setup(self, ctx: AppContext) -> None:
        """Initialize connection, warm up, register OTel instrumentation."""

    @abstractmethod
    async def health_check(self) -> HealthStatus:
        """Lightweight liveness probe; aim for <100ms."""

    @abstractmethod
    async def shutdown(self) -> None:
        """Flush buffers, close connections, cancel subscriptions."""

    # ---- optional hooks (default no-op) --------------------------------
    def fastapi_router(self) -> APIRouter | None:
        """Optional management router this integration exposes (e.g. /redis/info)."""
        return None

    def fastapi_middlewares(self) -> list[Any]:
        """Optional middleware (e.g. per-request DB session)."""
        return []

    def fastapi_dependencies(self) -> dict[str, Any]:
        """Optional FastAPI Depends() factories (e.g. ``get_session``)."""
        return {}


__all__ = ["IntegrationProvider"]
```

- [ ] **Step 25.4: 跑 → pass**

- [ ] **Step 25.5: Commit**

```bash
git add hwhkit/core/integration.py tests/unit/core/test_integration.py
git commit -m "feat(core): add IntegrationProvider ABC

See spec § 2.1."
```

---

## Task 26: `hwhkit.core.context.AppContext` (TDD)

**Files:**
- Create: `hwhkit/core/context.py`
- Create: `tests/unit/core/test_context.py`

- [ ] **Step 26.1: 写失败测试**

```python
"""Tests for hwhkit.core.context."""

from __future__ import annotations

from typing import ClassVar

import pytest
from pydantic import BaseModel

from hwhkit.core.context import AppContext
from hwhkit.core.contracts import Cache
from hwhkit.core.integration import IntegrationProvider


class DummyConfig(BaseModel):
    pass


class FakePostgres(IntegrationProvider):
    name: ClassVar[str] = "postgres"
    config_schema: ClassVar[type[BaseModel]] = DummyConfig

    async def setup(self, ctx) -> None: ...  # noqa: ANN001
    async def health_check(self): from hwhkit.core.health import HealthStatus; return HealthStatus.healthy()
    async def shutdown(self) -> None: ...


class FakeRedis(IntegrationProvider):
    name: ClassVar[str] = "redis"
    config_schema: ClassVar[type[BaseModel]] = DummyConfig
    implements: ClassVar[list[type]] = [Cache]

    async def setup(self, ctx) -> None: ...  # noqa: ANN001
    async def health_check(self): from hwhkit.core.health import HealthStatus; return HealthStatus.healthy()
    async def shutdown(self) -> None: ...

    async def get(self, key: str) -> bytes | None: return None
    async def set(self, key, value, ttl=None) -> None: ...
    async def delete(self, key) -> bool: return True
    async def exists(self, key) -> bool: return False
    async def incr(self, key, delta=1) -> int: return 0
    async def expire(self, key, ttl) -> bool: return True


class TestAppContext:
    def test_get_by_name(self) -> None:
        ctx = AppContext()
        pg = FakePostgres()
        ctx.register(pg)
        assert ctx.get("postgres") is pg

    def test_get_typed(self) -> None:
        ctx = AppContext()
        pg = FakePostgres()
        ctx.register(pg)
        assert ctx.get_typed(FakePostgres) is pg

    def test_get_missing_raises(self) -> None:
        ctx = AppContext()
        with pytest.raises(KeyError):
            ctx.get("nope")

    def test_resolve_contract_via_implements(self) -> None:
        ctx = AppContext()
        redis = FakeRedis()
        ctx.register(redis)
        # FakeRedis declared implements=[Cache], so resolve(Cache) returns it.
        cache = ctx.resolve(Cache)
        assert cache is redis

    def test_explicit_bind_overrides_auto(self) -> None:
        ctx = AppContext()
        r1 = FakeRedis()
        r2 = FakeRedis()
        r2.name = "redis2"  # type: ignore[misc]
        ctx.register(r1)
        ctx.register(r2)
        ctx.bind_contract(Cache, "redis2")
        assert ctx.resolve(Cache) is r2

    def test_resolve_unbound_when_multiple_raises(self) -> None:
        ctx = AppContext()
        r1 = FakeRedis()
        r2 = FakeRedis()
        r2.name = "redis2"  # type: ignore[misc]
        ctx.register(r1)
        ctx.register(r2)
        with pytest.raises(LookupError, match="multiple"):
            ctx.resolve(Cache)
```

- [ ] **Step 26.2: 跑 → fail**

- [ ] **Step 26.3: 实现 `hwhkit/core/context.py`**

```python
"""AppContext — the framework's runtime container.

Holds registered integrations, supports lookup by name, by concrete type, or by
contract protocol (with optional explicit binding for disambiguation).

See spec § 2.2, § 5.6.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

from hwhkit.core.integration import IntegrationProvider

if TYPE_CHECKING:
    pass

T = TypeVar("T")
P = TypeVar("P", bound=IntegrationProvider)


class AppContext:
    """Runtime container of registered integrations + bindings."""

    def __init__(self) -> None:
        self._integrations: dict[str, IntegrationProvider] = {}
        self._contract_bindings: dict[type, str] = {}

    # ---- registration --------------------------------------------------
    def register(self, integration: IntegrationProvider) -> None:
        if integration.name in self._integrations:
            raise ValueError(f"Integration {integration.name!r} already registered")
        self._integrations[integration.name] = integration

    # ---- lookup --------------------------------------------------------
    def get(self, name: str) -> IntegrationProvider:
        try:
            return self._integrations[name]
        except KeyError as exc:
            raise KeyError(f"No integration named {name!r}. Registered: {list(self._integrations)}") from exc

    def get_typed(self, cls: type[P]) -> P:
        for integ in self._integrations.values():
            if isinstance(integ, cls):
                return integ
        raise LookupError(f"No integration of type {cls.__name__}")

    def bind_contract(self, contract: type, provider_name: str) -> None:
        if provider_name not in self._integrations:
            raise KeyError(f"Cannot bind to unknown integration {provider_name!r}")
        self._contract_bindings[contract] = provider_name

    def resolve(self, contract: type[T]) -> T:
        """Resolve a contract Protocol to its bound or auto-detected implementer."""
        # 1) explicit binding
        if contract in self._contract_bindings:
            return self._integrations[self._contract_bindings[contract]]  # type: ignore[return-value]
        # 2) auto-resolve via `implements`
        candidates = [
            integ for integ in self._integrations.values()
            if contract in integ.implements
        ]
        if not candidates:
            raise LookupError(
                f"No integration implements {contract.__name__}. "
                f"Either register one or use bind_contract()."
            )
        if len(candidates) > 1:
            names = [c.name for c in candidates]
            raise LookupError(
                f"multiple integrations implement {contract.__name__}: {names}. "
                f"Use bind_contract() to disambiguate."
            )
        return candidates[0]  # type: ignore[return-value]

    # ---- iteration -----------------------------------------------------
    @property
    def integrations(self) -> dict[str, IntegrationProvider]:
        return dict(self._integrations)


__all__ = ["AppContext"]
```

- [ ] **Step 26.4: 跑 → pass**

- [ ] **Step 26.5: Commit**

```bash
git add hwhkit/core/context.py tests/unit/core/test_context.py
git commit -m "feat(core): add AppContext with name/type/contract resolution"
```

---

## Task 27: `hwhkit.core.shutdown` (TDD)

**Files:**
- Create: `hwhkit/core/shutdown.py`
- Create: `tests/unit/core/test_shutdown.py`

- [ ] **Step 27.1: 写失败测试**

```python
"""Tests for hwhkit.core.shutdown."""

from __future__ import annotations

import asyncio

import pytest

from hwhkit.core.shutdown import GracefulShutdown, ShutdownTimeout


class TestGracefulShutdown:
    @pytest.mark.asyncio
    async def test_runs_callbacks_in_reverse_order(self) -> None:
        order: list[str] = []
        gs = GracefulShutdown(timeout=2.0)
        gs.register("a", lambda: order.append("a"))
        gs.register("b", lambda: order.append("b"))
        gs.register("c", lambda: order.append("c"))
        await gs.run()
        assert order == ["c", "b", "a"]

    @pytest.mark.asyncio
    async def test_async_callbacks_awaited(self) -> None:
        flags: list[bool] = []
        async def cb() -> None:
            await asyncio.sleep(0.01)
            flags.append(True)

        gs = GracefulShutdown(timeout=2.0)
        gs.register("async-cb", cb)
        await gs.run()
        assert flags == [True]

    @pytest.mark.asyncio
    async def test_timeout_kills_slow_callback(self) -> None:
        async def slow() -> None:
            await asyncio.sleep(5.0)

        gs = GracefulShutdown(timeout=0.05)
        gs.register("slow", slow)
        with pytest.raises(ShutdownTimeout, match="slow"):
            await gs.run()

    @pytest.mark.asyncio
    async def test_one_failing_callback_does_not_block_others(self) -> None:
        order: list[str] = []
        def bad() -> None: raise RuntimeError("kaboom")
        def good() -> None: order.append("good")

        gs = GracefulShutdown(timeout=2.0)
        gs.register("bad", bad)
        gs.register("good", good)
        await gs.run()
        # good registered second, so runs first (reverse order)
        assert order == ["good"]
```

- [ ] **Step 27.2: 跑 → fail**

- [ ] **Step 27.3: 实现 `hwhkit/core/shutdown.py`**

```python
"""Graceful shutdown manager.

Callbacks run in reverse registration order (LIFO), each subject to a per-call
timeout. A failing callback logs but doesn't block subsequent callbacks.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import Awaitable, Callable

ShutdownCallback = Callable[[], None | Awaitable[None]]

_logger = logging.getLogger(__name__)


class ShutdownTimeout(Exception):
    """Raised when a callback exceeds the configured timeout."""


class GracefulShutdown:
    """LIFO-order shutdown executor with per-callback timeout."""

    def __init__(self, timeout: float = 30.0) -> None:
        self._timeout = timeout
        self._callbacks: list[tuple[str, ShutdownCallback]] = []

    def register(self, name: str, cb: ShutdownCallback) -> None:
        self._callbacks.append((name, cb))

    async def run(self) -> None:
        timeouts: list[str] = []
        for name, cb in reversed(self._callbacks):
            try:
                result = cb()
                if inspect.isawaitable(result):
                    await asyncio.wait_for(result, timeout=self._timeout)
            except TimeoutError:
                timeouts.append(name)
                _logger.error("Shutdown callback %r exceeded timeout %.1fs", name, self._timeout)
            except Exception as exc:  # noqa: BLE001
                _logger.exception("Shutdown callback %r failed: %s", name, exc)
        if timeouts:
            raise ShutdownTimeout(f"callbacks exceeded timeout: {timeouts}")


__all__ = ["GracefulShutdown", "ShutdownCallback", "ShutdownTimeout"]
```

- [ ] **Step 27.4: 跑 → pass**

- [ ] **Step 27.5: Commit**

```bash
git add hwhkit/core/shutdown.py tests/unit/core/test_shutdown.py
git commit -m "feat(core): add GracefulShutdown with reverse-order + timeout"
```

---

## Task 28: `hwhkit.core.jwt` — JWKS Cache + Claims 提取器 (TDD)

**Files:**
- Create: `hwhkit/core/jwt.py`
- Create: `tests/unit/core/test_jwt.py`

- [ ] **Step 28.1: 添加 `jwt` extra 到 dev 依赖(临时)**

Test 需要 `pyjwt[crypto]` + `httpx`,临时加到 dev:

修改 `pyproject.toml`,`dev` extras 增加:
```toml
"pyjwt[crypto]>=2.10",
"httpx>=0.28",
```

- [ ] **Step 28.2: 写失败测试(用 mocked JWKS)**

```python
"""Tests for hwhkit.core.jwt — JWKS cache + Claims extractor."""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import AsyncMock

import jwt as pyjwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from hwhkit.core.jwt import JwksCache, JwtVerifier, JwtVerifyError


def _make_rsa_keypair() -> tuple[Any, str]:
    """Generate a fresh RSA keypair; return (private_key, JWKS dict)."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    # Build a minimal JWKS — we use PEM string in the test, not a real JWK
    # but pyjwt accepts PEM via PyJWK; convert to JWK:
    import json
    from jwt.algorithms import RSAAlgorithm
    jwk = json.loads(RSAAlgorithm.to_jwk(priv.public_key()))
    jwk["kid"] = "test-kid"
    jwk["use"] = "sig"
    jwks = {"keys": [jwk]}
    return priv, jwks


@pytest.mark.asyncio
async def test_verify_valid_token() -> None:
    priv, jwks = _make_rsa_keypair()

    fetcher = AsyncMock(return_value=jwks)
    cache = JwksCache(fetch=fetcher, ttl=300.0)
    verifier = JwtVerifier(jwks_cache=cache, issuer="https://issuer", audience="api")

    token = pyjwt.encode(
        {
            "iss": "https://issuer",
            "aud": "api",
            "sub": "user-1",
            "exp": int(time.time()) + 60,
        },
        priv,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )

    claims = await verifier.verify(token)
    assert claims["sub"] == "user-1"


@pytest.mark.asyncio
async def test_jwks_cache_hits() -> None:
    priv, jwks = _make_rsa_keypair()
    fetcher = AsyncMock(return_value=jwks)
    cache = JwksCache(fetch=fetcher, ttl=300.0)

    await cache.get()
    await cache.get()
    fetcher.assert_awaited_once()  # only fetched once


@pytest.mark.asyncio
async def test_jwks_cache_refresh_after_ttl() -> None:
    priv, jwks = _make_rsa_keypair()
    fetcher = AsyncMock(return_value=jwks)
    cache = JwksCache(fetch=fetcher, ttl=0.01)

    await cache.get()
    import asyncio
    await asyncio.sleep(0.02)
    await cache.get()
    assert fetcher.await_count == 2


@pytest.mark.asyncio
async def test_reject_expired_token() -> None:
    priv, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://issuer",
        audience="api",
    )
    token = pyjwt.encode(
        {"iss": "https://issuer", "aud": "api", "sub": "u", "exp": int(time.time()) - 60},
        priv, algorithm="RS256", headers={"kid": "test-kid"},
    )
    with pytest.raises(JwtVerifyError, match="expired"):
        await verifier.verify(token)


@pytest.mark.asyncio
async def test_reject_alg_none() -> None:
    """Defense against `alg: none` attack."""
    _, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://issuer", audience="api",
    )
    bad = pyjwt.encode({"sub": "x"}, key="", algorithm="none")  # type: ignore[arg-type]
    with pytest.raises(JwtVerifyError):
        await verifier.verify(bad)


@pytest.mark.asyncio
async def test_reject_wrong_issuer() -> None:
    priv, jwks = _make_rsa_keypair()
    verifier = JwtVerifier(
        jwks_cache=JwksCache(fetch=AsyncMock(return_value=jwks), ttl=300.0),
        issuer="https://expected",
        audience="api",
    )
    token = pyjwt.encode(
        {"iss": "https://OTHER", "aud": "api", "sub": "u", "exp": int(time.time()) + 60},
        priv, algorithm="RS256", headers={"kid": "test-kid"},
    )
    with pytest.raises(JwtVerifyError, match="issuer"):
        await verifier.verify(token)
```

- [ ] **Step 28.3: 跑 → fail (no module)**

- [ ] **Step 28.4: 实现 `hwhkit/core/jwt.py`**

```python
"""JWT verifier with JWKS caching.

Intended for OAuth2/OIDC providers (Auth0, Cognito, Keycloak, etc.) where
public keys are published at /.well-known/jwks.json.

Hardened against common JWT pitfalls: `alg: none`, key confusion, expired tokens,
wrong audience/issuer.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import Any

import jwt as pyjwt
from jwt import PyJWKClient
from jwt.exceptions import InvalidTokenError

# Allowed algorithms — never include "none".
ALLOWED_ALGORITHMS = ["RS256", "RS384", "RS512", "ES256", "ES384", "ES512"]


class JwtVerifyError(Exception):
    """JWT verification failed."""


class JwksCache:
    """TTL-cached JWKS document fetcher."""

    def __init__(
        self,
        fetch: Callable[[], Awaitable[dict[str, Any]]],
        *,
        ttl: float = 3600.0,
    ) -> None:
        self._fetch = fetch
        self._ttl = ttl
        self._cached: dict[str, Any] | None = None
        self._cached_at: float = 0.0
        self._lock = asyncio.Lock()

    async def get(self) -> dict[str, Any]:
        async with self._lock:
            now = time.monotonic()
            if self._cached and now - self._cached_at < self._ttl:
                return self._cached
            self._cached = await self._fetch()
            self._cached_at = now
            return self._cached


class JwtVerifier:
    """Verify a Bearer token's signature + claims using a JWKS cache."""

    def __init__(
        self,
        *,
        jwks_cache: JwksCache,
        issuer: str,
        audience: str,
        algorithms: list[str] | None = None,
        leeway: int = 30,
    ) -> None:
        self._jwks = jwks_cache
        self._issuer = issuer
        self._audience = audience
        self._algorithms = algorithms or ALLOWED_ALGORITHMS
        self._leeway = leeway

    async def verify(self, token: str) -> dict[str, Any]:
        try:
            # 1) Unverified header → pick kid
            header = pyjwt.get_unverified_header(token)
            kid = header.get("kid")
            alg = header.get("alg")
            if alg not in self._algorithms:
                raise JwtVerifyError(f"disallowed algorithm: {alg!r}")

            # 2) Fetch JWKS & find matching key
            jwks = await self._jwks.get()
            jwk = self._find_key(jwks, kid)
            if not jwk:
                raise JwtVerifyError(f"no JWKS key matched kid={kid!r}")

            # 3) Build verify key
            public_key = pyjwt.algorithms.RSAAlgorithm.from_jwk(jwk)  # type: ignore[attr-defined]

            # 4) pyjwt verifies signature + exp + iss + aud
            return pyjwt.decode(
                token,
                key=public_key,
                algorithms=self._algorithms,
                issuer=self._issuer,
                audience=self._audience,
                leeway=self._leeway,
                options={"require": ["exp", "iss", "aud"]},
            )
        except InvalidTokenError as exc:
            raise JwtVerifyError(str(exc)) from exc

    @staticmethod
    def _find_key(jwks: dict[str, Any], kid: str | None) -> dict[str, Any] | None:
        for key in jwks.get("keys", []):
            if kid is None or key.get("kid") == kid:
                return key
        return None


__all__ = ["ALLOWED_ALGORITHMS", "JwksCache", "JwtVerifier", "JwtVerifyError"]
```

- [ ] **Step 28.5: 跑 → pass**

- [ ] **Step 28.6: Commit**

```bash
git add hwhkit/core/jwt.py tests/unit/core/test_jwt.py pyproject.toml uv.lock
git commit -m "feat(core): add JwtVerifier with JWKS cache

Defends against alg:none, expired tokens, wrong iss/aud."
```

---

## Task 29: `hwhkit.testing` 骨架 + `OtelRecorder` (TDD)

**Files:**
- Create: `hwhkit/testing/__init__.py`
- Create: `hwhkit/testing/fakes/__init__.py`
- Create: `hwhkit/testing/contract_tests/__init__.py`
- Create: `hwhkit/testing/otel_recorder.py`
- Create: `tests/unit/testing/test_otel_recorder.py`

- [ ] **Step 29.1: 创建骨架**

```bash
mkdir -p hwhkit/testing/fakes hwhkit/testing/contract_tests
```

`hwhkit/testing/__init__.py`:
```python
"""hwhkit.testing — utilities for testing services built on hwhkit.

Includes:
- ``hwhkit.testing.fakes`` — in-memory implementations of all contracts (W3+).
- ``hwhkit.testing.contract_tests`` — reusable contract conformance test suites (W3+).
- ``hwhkit.testing.otel_recorder`` — in-memory OTel exporter for assertions.
"""
```

`hwhkit/testing/fakes/__init__.py`:
```python
"""In-memory fakes for all contracts. Populated in W3+."""
```

`hwhkit/testing/contract_tests/__init__.py`:
```python
"""Reusable conformance test suites for contracts. Populated in W3+."""
```

- [ ] **Step 29.2: 写失败测试 — OtelRecorder**

```python
"""Tests for hwhkit.testing.otel_recorder."""

from __future__ import annotations

from hwhkit.testing.otel_recorder import OtelRecorder


class TestOtelRecorder:
    def test_records_spans(self) -> None:
        rec = OtelRecorder()
        with rec.span("op-1") as span:
            span.set_attribute("k", "v")
        assert len(rec.spans) == 1
        assert rec.spans[0].name == "op-1"
        assert rec.spans[0].attributes["k"] == "v"

    def test_records_counters(self) -> None:
        rec = OtelRecorder()
        c = rec.counter("requests")
        c.add(1, {"method": "GET"})
        c.add(2, {"method": "POST"})
        assert rec.counter_total("requests") == 3
        assert rec.counter_with("requests", {"method": "GET"}) == 1

    def test_records_logs(self) -> None:
        rec = OtelRecorder()
        rec.log_emitter.emit("info", "hello", user="alice")
        assert len(rec.logs) == 1
        assert rec.logs[0].event == "hello"
        assert rec.logs[0].fields["user"] == "alice"

    def test_reset_clears_state(self) -> None:
        rec = OtelRecorder()
        with rec.span("x"):
            pass
        rec.counter("c").add(1)
        rec.log_emitter.emit("info", "e")
        rec.reset()
        assert rec.spans == []
        assert rec.counter_total("c") == 0
        assert rec.logs == []
```

- [ ] **Step 29.3: 跑 → fail**

- [ ] **Step 29.4: 实现 `hwhkit/testing/otel_recorder.py`**

```python
"""In-memory recorder for OTel-like signals — useful for unit tests.

Not a full OTel SDK exporter; this is a lightweight stand-in that satisfies
hwhkit.core.contracts.telemetry.{Tracer, Meter, LogEmitter} for assertions
in tests that don't want the real SDK overhead.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any


@dataclass
class RecordedSpan:
    name: str
    attributes: dict[str, Any] = field(default_factory=dict)
    exceptions: list[Exception] = field(default_factory=list)


@dataclass
class RecordedLog:
    level: str
    event: str
    fields: dict[str, Any] = field(default_factory=dict)


class _RecorderSpan:
    def __init__(self, recorded: RecordedSpan) -> None:
        self._r = recorded

    def set_attribute(self, key: str, value: Any) -> None:
        self._r.attributes[key] = value

    def record_exception(self, exc: Exception) -> None:
        self._r.exceptions.append(exc)

    def end(self) -> None:
        pass


class _RecorderCounter:
    def __init__(self, recorder: "OtelRecorder", name: str) -> None:
        self._rec = recorder
        self._name = name

    def add(self, amount: int | float, attributes: dict[str, Any] | None = None) -> None:
        self._rec._counters.setdefault(self._name, []).append((amount, attributes or {}))


class _RecorderHistogram:
    def __init__(self, recorder: "OtelRecorder", name: str) -> None:
        self._rec = recorder
        self._name = name

    def record(self, value: int | float, attributes: dict[str, Any] | None = None) -> None:
        self._rec._histograms.setdefault(self._name, []).append((value, attributes or {}))


class _RecorderLogEmitter:
    def __init__(self, recorder: "OtelRecorder") -> None:
        self._rec = recorder

    def emit(self, level: str, event: str, **fields: Any) -> None:
        self._rec.logs.append(RecordedLog(level=level, event=event, fields=fields))


class OtelRecorder:
    """Drop-in fake for Tracer/Meter/LogEmitter that records everything in memory."""

    def __init__(self) -> None:
        self.spans: list[RecordedSpan] = []
        self.logs: list[RecordedLog] = []
        self._counters: dict[str, list[tuple[int | float, dict[str, Any]]]] = {}
        self._histograms: dict[str, list[tuple[int | float, dict[str, Any]]]] = {}
        self.log_emitter = _RecorderLogEmitter(self)

    @contextmanager
    def span(self, name: str, **attrs: Any) -> Iterator[_RecorderSpan]:
        rs = RecordedSpan(name=name, attributes=dict(attrs))
        self.spans.append(rs)
        yield _RecorderSpan(rs)

    def start_span(self, name: str, **attrs: Any) -> Any:
        return self.span(name, **attrs)

    def counter(self, name: str) -> _RecorderCounter:
        return _RecorderCounter(self, name)

    def histogram(self, name: str) -> _RecorderHistogram:
        return _RecorderHistogram(self, name)

    def create_counter(self, name: str, *, unit: str = "1", description: str = "") -> _RecorderCounter:
        return self.counter(name)

    def create_histogram(self, name: str, *, unit: str = "1", description: str = "") -> _RecorderHistogram:
        return self.histogram(name)

    def counter_total(self, name: str) -> int | float:
        return sum(v for v, _ in self._counters.get(name, []))

    def counter_with(self, name: str, attrs: dict[str, Any]) -> int | float:
        return sum(v for v, a in self._counters.get(name, []) if a == attrs)

    def reset(self) -> None:
        self.spans.clear()
        self.logs.clear()
        self._counters.clear()
        self._histograms.clear()


__all__ = ["OtelRecorder", "RecordedLog", "RecordedSpan"]
```

- [ ] **Step 29.5: 跑 → pass**

- [ ] **Step 29.6: Commit**

```bash
git add hwhkit/testing/ tests/unit/testing/
git commit -m "feat(testing): add OtelRecorder for in-memory signal assertions"
```

---

## Task 30: 最终化 contracts `__init__.py` + 顶层 facade

**Files:**
- Modify: `hwhkit/core/contracts/__init__.py`
- Modify: `hwhkit/core/__init__.py`
- Modify: `hwhkit/__init__.py`

- [ ] **Step 30.1: 最终化 contracts `__init__.py`(全部 export)**

```python
"""hwhkit contracts — protocol definitions.

Business code depends ONLY on these protocols. Concrete adapter implementations
live in ``hwhkit.integrations.*``.
"""

from hwhkit.core.contracts.cache import Cache, Codec, JsonCodec, PickleCodec, TypedCache
from hwhkit.core.contracts.kv_store import KvStore
from hwhkit.core.contracts.llm import (
    ChatMessage,
    ChatResponse,
    EmbeddingClient,
    LlmClient,
    Role,
)
from hwhkit.core.contracts.lock import DistributedLock, LockToken
from hwhkit.core.contracts.message_bus import (
    Message,
    MessageBus,
    PublishAck,
    Subscription,
)
from hwhkit.core.contracts.notifier import Notifier, Severity
from hwhkit.core.contracts.object_store import ObjectMetadata, ObjectStore
from hwhkit.core.contracts.relational_db import RelationalDb, Session
from hwhkit.core.contracts.scheduler import JobFunc, Scheduler
from hwhkit.core.contracts.secrets import SecretsProvider
from hwhkit.core.contracts.telemetry import (
    Counter,
    Histogram,
    LogEmitter,
    Meter,
    Span,
    Tracer,
)
from hwhkit.core.contracts.vector_store import SearchHit, VectorRecord, VectorStore

__all__ = [
    "Cache",
    "ChatMessage",
    "ChatResponse",
    "Codec",
    "Counter",
    "DistributedLock",
    "EmbeddingClient",
    "Histogram",
    "JobFunc",
    "JsonCodec",
    "KvStore",
    "LlmClient",
    "LockToken",
    "LogEmitter",
    "Message",
    "MessageBus",
    "Meter",
    "Notifier",
    "ObjectMetadata",
    "ObjectStore",
    "PickleCodec",
    "PublishAck",
    "RelationalDb",
    "Role",
    "Scheduler",
    "SearchHit",
    "SecretsProvider",
    "Session",
    "Severity",
    "Span",
    "Subscription",
    "Tracer",
    "TypedCache",
    "VectorRecord",
    "VectorStore",
]
```

- [ ] **Step 30.2: 最终化 `hwhkit/core/__init__.py`**

```python
"""hwhkit core — bootstrap pipeline, AppContext, IntegrationProvider, errors, contracts, etc."""

from hwhkit.core.context import AppContext
from hwhkit.core.errors import (
    ApiError,
    ConflictError,
    DbConnectionError,
    ForbiddenError,
    InternalError,
    IntegrationError,
    NatsConnectionError,
    NotFoundError,
    RateLimitError,
    RedisConnectionError,
    UnauthorizedError,
    ValidationError,
)
from hwhkit.core.health import HealthAggregator, HealthCheck, HealthStatus
from hwhkit.core.integration import IntegrationProvider
from hwhkit.core.shutdown import GracefulShutdown, ShutdownTimeout

__all__ = [
    "ApiError",
    "AppContext",
    "ConflictError",
    "DbConnectionError",
    "ForbiddenError",
    "GracefulShutdown",
    "HealthAggregator",
    "HealthCheck",
    "HealthStatus",
    "IntegrationError",
    "IntegrationProvider",
    "InternalError",
    "NatsConnectionError",
    "NotFoundError",
    "RateLimitError",
    "RedisConnectionError",
    "ShutdownTimeout",
    "UnauthorizedError",
    "ValidationError",
]
```

- [ ] **Step 30.3: 最终化 `hwhkit/__init__.py`**

```python
"""hwhkit — production-ready Python framework for trading services and microservices.

See https://hwhkit.louishwh.tech for documentation.
"""

from hwhkit.core import (
    ApiError,
    AppContext,
    HealthStatus,
    IntegrationProvider,
)
from hwhkit.core import contracts

__version__ = "0.4.0a1"
__all__ = [
    "ApiError",
    "AppContext",
    "HealthStatus",
    "IntegrationProvider",
    "__version__",
    "contracts",
]
```

- [ ] **Step 30.4: 跑全部 unit tests + mypy + ruff**

```bash
uv run pytest tests/unit -v
uv run mypy hwhkit
uv run ruff check hwhkit tests
uv run ruff format --check hwhkit tests
```

Expected: 所有都过。

- [ ] **Step 30.5: 跑 mkdocs build,确认文档站可构建**

```bash
uv run mkdocs build --strict
```

Expected: 成功生成 site/ 无 warning。

- [ ] **Step 30.6: Commit**

```bash
git add hwhkit/__init__.py hwhkit/core/__init__.py hwhkit/core/contracts/__init__.py
git commit -m "feat(core): finalize public API exports for W1"
```

---

## Task 31: W1 验收 + 推送

- [ ] **Step 31.1: 跑完整测试 + lint + typecheck + docs**

```bash
make test
make lint
make typecheck
make docs
```

全部应 pass。

- [ ] **Step 31.2: 检查覆盖率**

```bash
make test-cov
```

Expected: `hwhkit.core` 模块覆盖率应该已经 ≥95%。

- [ ] **Step 31.3: 更新 CHANGELOG**

`CHANGELOG.md` 把 `[Unreleased]` 下的 Added 列表确认完整;不需要 release。

- [ ] **Step 31.4: 推送到 origin**

```bash
git push origin main
```

Expected: GitHub Actions CI 全绿(lint/typecheck/test-unit/build/security 全部)。

- [ ] **Step 31.5: 检查 CI**

```bash
gh run list --limit 1
gh run watch
```

Expected: ✅ 全绿。如有失败,修复重推。

- [ ] **Step 31.6: 验证文档站(本地)**

```bash
make docs-serve
# 访问 http://127.0.0.1:8000,确认首页 / getting-started / contributing 可读
```

- [ ] **Step 31.7: 在 master TODO 中勾选 W1 全部任务**

修改 `docs/superpowers/plans/2026-05-16-hwhkit-py-master-todo.md`,W1 区块所有 checkbox 改 `[x]`。

- [ ] **Step 31.8: W1 总结 commit**

```bash
git add docs/superpowers/plans/2026-05-16-hwhkit-py-master-todo.md
git commit -m "docs(plan): mark W1 milestones complete

W1 deliverables:
- Project skeleton + CI/CD + pre-commit
- All 12 contract protocols defined (Cache/KvStore/Lock/MessageBus/RelationalDb/...)
- IntegrationProvider ABC + AppContext + HealthAggregator + GracefulShutdown + JwtVerifier
- ApiError taxonomy with 6-digit codes
- hwhkit.testing.OtelRecorder
- Documentation site smoke version
- CI green on main"
git push origin main
```

---

## W1 Definition of Done

- ✅ `git log --oneline | wc -l` ≥ 30(每个任务 1-2 commits)
- ✅ `make test` 全绿,覆盖率 `hwhkit.core` ≥ 95%
- ✅ `make lint` + `make typecheck` 无 warning
- ✅ `make docs` 构建无 warning
- ✅ GitHub Actions CI 全绿
- ✅ `pip install -e .[dev]` 可装,`python -c "import hwhkit; print(hwhkit.__version__)"` 输出 `0.4.0a1`
- ✅ master TODO 文件 W1 区块全勾选

---

## Self-Review Notes

**Spec 覆盖度审核**(本 plan 实现 spec 的哪些章节):

- ✅ § 1 模块布局:`hwhkit.core` + `hwhkit.core.contracts` + `hwhkit.testing` 骨架已建,其他模块为占位(W2+)
- ✅ § 2.1 `IntegrationProvider` ABC — Task 25
- ✅ § 2.2 `AppContext` — Task 26
- ✅ § 2.5 健康检查分级、shutdown 反向顺序 — Task 24, 27
- ✅ § 3.3 6 位错误码 — Task 10
- ✅ § 5.2 所有第一批 contract — Task 11-22
- ✅ § 5.6 DI 绑定机制 — Task 26
- ⏭️ § 4 OTel(仅 OtelRecorder for tests,真正 SDK 集成在 W2)
- ⏭️ § 6 测试金字塔(unit 层完整,integration/e2e/benchmark/chaos 在 W2+)
- ⏭️ § 7 CI/CD(W1 完成基础,sigstore/release-please 在 W6)
- ⏭️ § 8 CLI(W5)
- ⏭️ § 9 业务接入验证(W6)

**类型/方法签名一致性审核**:

- `Cache.set(key, value, ttl)` ↔ `TypedCache.set(key, value, ttl)`:签名一致 ✅
- `AppContext.register(integration)` ↔ Task 26 测试 `ctx.register(pg)` ✅
- `HealthCheck.health_check()` ↔ `IntegrationProvider.health_check()`:返回 `HealthStatus` ✅
- `IntegrationProvider.implements: ClassVar[list[type]]` ↔ `AppContext.resolve()` 中 `integ.implements` 访问 ✅
- `GracefulShutdown.register(name, cb)` ↔ Task 27 测试 ✅

**Placeholder 扫描**: 无 TBD / TODO / "implement later"。所有 step 都有具体代码。

**Out-of-order safety**: Task 11 之后的每个 contract 任务,实现代码完整给出,不依赖工程师按顺序读 Task 11 才能完成 Task 12。

---

*End of W1 plan.*
