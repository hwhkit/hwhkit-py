"""Tests for ``hwhkit init`` scaffolder."""

from __future__ import annotations

from pathlib import Path

import pytest
from hwhkit.cli.scaffold import init_project


def test_init_creates_expected_files(tmp_path: Path) -> None:
    target = tmp_path / "my-service"
    init_project(name="my-service", target=target)

    assert (target / "pyproject.toml").is_file()
    assert (target / "README.md").is_file()
    assert (target / "Makefile").is_file()
    assert (target / "Dockerfile").is_file()
    assert (target / ".gitignore").is_file()
    assert (target / ".env.example").is_file()
    assert (target / "my_service" / "__init__.py").is_file()
    assert (target / "my_service" / "main.py").is_file()
    assert (target / "my_service" / "config.py").is_file()
    assert (target / "my_service" / "api" / "__init__.py").is_file()
    assert (target / "tests" / "conftest.py").is_file()
    assert (target / "tests" / "unit" / "test_smoke.py").is_file()


def test_init_main_py_imports_bootstrap(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    init_project(name="demo", target=target)
    content = (target / "demo" / "main.py").read_text()
    assert "bootstrap" in content
    assert "integrations=[]" in content


def test_init_pyproject_includes_hwhkit(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    init_project(name="demo", target=target)
    content = (target / "pyproject.toml").read_text()
    assert "hwhkit" in content


def test_init_kebab_name_converts_to_snake(tmp_path: Path) -> None:
    target = tmp_path / "kebab-case-svc"
    init_project(name="kebab-case-svc", target=target)
    assert (target / "kebab_case_svc" / "main.py").is_file()


def test_init_existing_dir_without_force_fails(tmp_path: Path) -> None:
    target = tmp_path / "x"
    target.mkdir()
    with pytest.raises(FileExistsError):
        init_project(name="x", target=target)


def test_init_existing_dir_with_force_overwrites(tmp_path: Path) -> None:
    target = tmp_path / "x"
    target.mkdir()
    (target / "stale.txt").write_text("old")
    init_project(name="x", target=target, force=True)
    assert not (target / "stale.txt").exists()
    assert (target / "x" / "main.py").is_file()
