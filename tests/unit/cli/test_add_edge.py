"""Edge cases for ``hwhkit add`` codemod."""

from __future__ import annotations

from pathlib import Path

import pytest
from hwhkit.cli.add import (
    _add_extra_to_pyproject,
    _find_main_py,
    _patch_main_py,
    add_modules,
)
from hwhkit.cli.scaffold import init_project


@pytest.fixture
def project(tmp_path: Path) -> Path:
    target = tmp_path / "demo"
    init_project(name="demo", target=target)
    return target


def test_add_unknown_module(project: Path) -> None:
    result = add_modules(project, "bogus")
    assert result.skipped_reason is not None
    assert "unknown module" in result.skipped_reason


def test_add_when_pyproject_missing(tmp_path: Path) -> None:
    result = add_modules(tmp_path, "postgres")
    assert result.skipped_reason == "pyproject.toml not found"


def test_add_otel_no_provider_call(project: Path) -> None:
    """OTel: no Provider, so main.py is never patched. (pyproject may already
    have otel extra from the init template — that's fine; we only assert
    main.py is untouched and env block lands.)"""
    result = add_modules(project, "otel")
    assert result.main_py_modified is False  # observability has no Provider class
    assert result.env_modified is True


def test_add_auth_no_provider_call(project: Path) -> None:
    """Auth add wires JWT extra + .env hint, but AuthMiddleware is not a
    bootstrap-registered Provider."""
    result = add_modules(project, "auth")
    assert result.pyproject_modified is True
    assert result.main_py_modified is False


def test_add_env_idempotent(project: Path) -> None:
    add_modules(project, "postgres")
    result = add_modules(project, "postgres")
    assert result.env_modified is False


def test_find_main_py_returns_none_when_missing(tmp_path: Path) -> None:
    assert _find_main_py(tmp_path) is None


def test_find_main_py_skips_excluded_dirs(tmp_path: Path) -> None:
    # Even if .venv has a main.py, we should not pick it
    venv = tmp_path / ".venv"
    venv.mkdir()
    (venv / "main.py").write_text("# stale")
    assert _find_main_py(tmp_path) is None


def test_patch_main_py_invalid_syntax_returns_none() -> None:
    bad = "from x import\n!!!syntax error"
    result = _patch_main_py(
        bad,
        "from hwhkit.integrations.redis import RedisProvider",
        "RedisProvider()",
    )
    assert result is None


def test_add_extra_no_hwhkit_dep_returns_none() -> None:
    content = '"requests==2.0"'
    assert _add_extra_to_pyproject(content, "postgres") is None
