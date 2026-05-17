"""``hwhkit init`` — project scaffolder.

Generates a minimal hwhkit project skeleton from inline templates (no jinja
files on disk yet — templates are kept as module strings for simplicity at
W5 and can be externalized to ``hwhkit/cli/templates/project/*.j2`` later if
they grow).
"""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

from hwhkit import __version__


def init_project(
    *,
    name: str,
    target: Path,
    python_version: str | None = None,
    force: bool = False,
) -> None:
    """Create a new hwhkit project at ``target``."""
    if target.exists():
        if not force:
            raise FileExistsError(
                f"target directory {target} already exists (use --force to overwrite)"
            )
        if target.is_dir():
            shutil.rmtree(target)
        else:
            target.unlink()

    target.mkdir(parents=True)
    module = _module_name(name)
    py = python_version or f"{sys.version_info.major}.{sys.version_info.minor}"

    _write(target / "pyproject.toml", _PYPROJECT_TEMPLATE.format(name=name, py=py))
    _write(target / "README.md", _README_TEMPLATE.format(name=name))
    _write(target / ".gitignore", _GITIGNORE)
    _write(target / ".python-version", py + "\n")
    _write(target / "Makefile", _MAKEFILE.format(module=module))
    _write(target / ".env.example", _ENV_EXAMPLE)
    _write(target / "Dockerfile", _DOCKERFILE.format(module=module, py=py))
    _write(target / "docker-compose.yml", _DOCKER_COMPOSE)

    pkg = target / module
    pkg.mkdir()
    _write(pkg / "__init__.py", _PKG_INIT.format(module=module))
    _write(pkg / "main.py", _MAIN_PY.format(name=name, module=module))
    _write(pkg / "config.py", _CONFIG_PY)
    (pkg / "api").mkdir()
    _write(pkg / "api" / "__init__.py", _API_INIT.format(module=module))
    (pkg / "services").mkdir()
    _write(pkg / "services" / "__init__.py", "")
    (pkg / "domain").mkdir()
    _write(pkg / "domain" / "__init__.py", "")
    (pkg / "adapters").mkdir()
    _write(pkg / "adapters" / "__init__.py", "")

    tests = target / "tests"
    tests.mkdir()
    _write(tests / "__init__.py", "")
    _write(tests / "conftest.py", _CONFTEST)
    (tests / "unit").mkdir()
    _write(tests / "unit" / "__init__.py", "")
    _write(tests / "unit" / "test_smoke.py", _SMOKE_TEST.format(module=module))


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def _module_name(project_name: str) -> str:
    return project_name.replace("-", "_").replace(" ", "_").lower()


# ---- templates -------------------------------------------------------------

_PYPROJECT_TEMPLATE = f"""[project]
name = "{{name}}"
version = "0.1.0"
description = "hwhkit-based service"
requires-python = ">={{py}}"
dependencies = [
    "hwhkit[web,otel]=={__version__}",
]

[project.optional-dependencies]
dev = ["pytest>=8", "pytest-asyncio", "ruff>=0.14", "mypy>=1.13"]

[build-system]
requires = ["hatchling>=1.27"]
build-backend = "hatchling.build"
"""

_README_TEMPLATE = """# {name}

hwhkit-based service.

## Run

```bash
uv sync
uv run python -m {name_module}.main
```
""".replace("{name_module}", "{name}")

_GITIGNORE = """__pycache__/
*.py[cod]
.venv/
.pytest_cache/
.mypy_cache/
.ruff_cache/
.coverage
htmlcov/
dist/
build/
.env
.env.local
.DS_Store
"""

_MAKEFILE = """.PHONY: dev test lint typecheck run

dev:
\tuv sync --extra dev
\tuv run pre-commit install || true

test:
\tuv run pytest tests/unit -v

lint:
\tuv run ruff check {module} tests
\tuv run ruff format --check {module} tests

typecheck:
\tuv run mypy {module}

run:
\tuv run python -m {module}.main
"""

_ENV_EXAMPLE = """# Edit and rename to .env (NEVER commit)
HWHKIT_APP__NAME=my-service
HWHKIT_APP__VERSION=0.1.0
HWHKIT_OBSERVABILITY__ENABLED=false
"""

_DOCKERFILE = """FROM python:{py}-slim

WORKDIR /app

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock* ./
RUN uv sync --frozen --no-dev || uv sync --no-dev

COPY . .

EXPOSE 8000
CMD ["uv", "run", "python", "-m", "{module}.main"]
"""

_DOCKER_COMPOSE = """# Local development dependencies. Uncomment what you need.
# version: "3.9"
# services:
#   postgres:
#     image: postgres:16-alpine
#     environment:
#       POSTGRES_USER: postgres
#       POSTGRES_PASSWORD: postgres
#       POSTGRES_DB: postgres
#     ports:
#       - "5432:5432"
#   redis:
#     image: redis:7-alpine
#     ports:
#       - "6379:6379"
"""

_PKG_INIT = """\"\"\"{module} — hwhkit-based service.\"\"\"

__version__ = "0.1.0"
"""

_MAIN_PY = """\"\"\"{name} service — bootstrap entry point.\"\"\"

from __future__ import annotations

from hwhkit.core.bootstrap import bootstrap

from {module}.api import api_router

app = bootstrap(
    name="{name}",
    version="0.1.0",
    integrations=[],
    routers=[api_router],
)


if __name__ == "__main__":
    from hwhkit.web.server import run

    run(app, server="uvicorn", host="127.0.0.1", port=8000, reload=False)
"""

_CONFIG_PY = '''"""Project-specific config (extends hwhkit Settings).

Add integration config sections here as you `hwhkit add` more modules.
"""

from __future__ import annotations

from hwhkit.config.base import Settings


class AppSettings(Settings):
    """Per-service settings; extend with sections you `hwhkit add`."""
'''

_API_INIT = """\"\"\"{module}.api — HTTP routes.\"\"\"

from __future__ import annotations

from fastapi import APIRouter

api_router = APIRouter()


@api_router.get("/")
async def root() -> dict:
    return {{"hello": "world"}}
"""

_CONFTEST = '''"""Project pytest fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"
'''

_SMOKE_TEST = """\"\"\"Smoke test — verify the service bootstraps.\"\"\"

from __future__ import annotations

from fastapi.testclient import TestClient


def test_healthz() -> None:
    from {module}.main import app

    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {{"ok": True}}
"""


__all__ = ["init_project"]
