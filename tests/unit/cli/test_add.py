"""Tests for ``hwhkit add`` — libcst-based integration adder."""

from __future__ import annotations

from pathlib import Path

import pytest
from hwhkit.cli.add import _add_extra_to_pyproject, _patch_main_py, add_modules
from hwhkit.cli.scaffold import init_project


@pytest.fixture
def project(tmp_path: Path) -> Path:
    target = tmp_path / "demo"
    init_project(name="demo", target=target)
    return target


def test_add_postgres_updates_pyproject_and_main(project: Path) -> None:
    result = add_modules(project, "postgres")
    assert result.pyproject_modified is True
    assert result.main_py_modified is True
    assert result.env_modified is True

    pyproject = (project / "pyproject.toml").read_text()
    assert "postgres" in pyproject

    main = (project / "demo" / "main.py").read_text()
    assert "from hwhkit.integrations.postgres import PostgresProvider" in main
    assert "PostgresProvider()" in main


def test_add_idempotent(project: Path) -> None:
    add_modules(project, "redis")
    result = add_modules(project, "redis")
    # Second run should produce no changes
    assert result.pyproject_modified is False
    assert result.main_py_modified is False
    assert result.env_modified is False


def test_add_two_integrations_both_present(project: Path) -> None:
    add_modules(project, "postgres")
    add_modules(project, "redis")

    main = (project / "demo" / "main.py").read_text()
    assert "PostgresProvider()" in main
    assert "RedisProvider()" in main

    pyproject = (project / "pyproject.toml").read_text()
    assert "postgres" in pyproject
    assert "redis" in pyproject


def test_add_dry_run_writes_nothing(project: Path) -> None:
    pyproject_before = (project / "pyproject.toml").read_text()
    main_before = (project / "demo" / "main.py").read_text()
    env_before = (project / ".env.example").read_text()

    result = add_modules(project, "postgres", dry_run=True)
    assert result.pyproject_modified is True
    assert result.dry_run is True

    assert (project / "pyproject.toml").read_text() == pyproject_before
    assert (project / "demo" / "main.py").read_text() == main_before
    assert (project / ".env.example").read_text() == env_before


def test_add_unknown_module_returns_skip() -> None:
    result = add_modules(Path("/tmp/nonexistent"), "bogus")
    assert result.skipped_reason is not None


def test_add_extra_to_pyproject_existing_brackets() -> None:
    content = '"hwhkit[web,otel]==0.4.0a1"'
    new = _add_extra_to_pyproject(content, "postgres")
    assert new is not None
    assert "[otel,postgres,web]" in new


def test_add_extra_to_pyproject_no_brackets() -> None:
    content = '"hwhkit==0.4.0a1"'
    new = _add_extra_to_pyproject(content, "postgres")
    assert new is not None
    assert '"hwhkit[postgres]==' in new


def test_add_extra_idempotent_in_pyproject() -> None:
    content = '"hwhkit[postgres,web]==0.4.0a1"'
    new = _add_extra_to_pyproject(content, "postgres")
    assert new is None  # already present → no change


def test_patch_main_py_adds_import_and_integration() -> None:
    source = """from hwhkit.core.bootstrap import bootstrap

app = bootstrap(
    name="demo",
    version="0.1.0",
    integrations=[],
    routers=[],
)
"""
    new = _patch_main_py(
        source,
        "from hwhkit.integrations.postgres import PostgresProvider",
        "PostgresProvider()",
    )
    assert new is not None
    assert "PostgresProvider" in new
    assert "PostgresProvider()" in new


def test_patch_main_py_idempotent_when_already_present() -> None:
    source = """from hwhkit.core.bootstrap import bootstrap
from hwhkit.integrations.postgres import PostgresProvider

app = bootstrap(
    name="demo",
    version="0.1.0",
    integrations=[PostgresProvider()],
    routers=[],
)
"""
    new = _patch_main_py(
        source,
        "from hwhkit.integrations.postgres import PostgresProvider",
        "PostgresProvider()",
    )
    assert new is None  # no change required
