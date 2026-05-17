"""End-to-end tests for the ``hwhkit`` CLI entry point."""

from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from hwhkit import __version__
from hwhkit.cli.commands import cli


def test_version_command() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.output


def test_help() -> None:
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "init" in result.output
    assert "add" in result.output


def test_init_creates_project(tmp_path: Path) -> None:
    runner = CliRunner()
    target = tmp_path / "svc"
    result = runner.invoke(cli, ["init", "svc", "--path", str(target)])
    assert result.exit_code == 0, result.output
    assert (target / "pyproject.toml").is_file()
    assert (target / "svc" / "main.py").is_file()


def test_init_then_add(tmp_path: Path) -> None:
    runner = CliRunner()
    target = tmp_path / "svc"
    result = runner.invoke(cli, ["init", "svc", "--path", str(target)])
    assert result.exit_code == 0

    result = runner.invoke(cli, ["add", "postgres", "--project", str(target)])
    assert result.exit_code == 0, result.output

    main = (target / "svc" / "main.py").read_text()
    assert "PostgresProvider" in main


def test_list_in_freshly_initialized_project(tmp_path: Path) -> None:
    runner = CliRunner()
    target = tmp_path / "svc"
    runner.invoke(cli, ["init", "svc", "--path", str(target)])
    # cwd switch via with_cwd
    import os

    cwd = os.getcwd()
    try:
        os.chdir(target)
        result = runner.invoke(cli, ["list"])
        assert result.exit_code == 0
        # hwhkit[web,otel] extras come from the init template
        assert "web" in result.output or "otel" in result.output
    finally:
        os.chdir(cwd)


def test_doctor_on_init_project_is_healthy(tmp_path: Path) -> None:
    runner = CliRunner()
    target = tmp_path / "svc"
    runner.invoke(cli, ["init", "svc", "--path", str(target)])
    import os

    cwd = os.getcwd()
    try:
        os.chdir(target)
        result = runner.invoke(cli, ["doctor"])
        assert result.exit_code == 0, result.output
        assert "healthy" in result.output.lower()
    finally:
        os.chdir(cwd)


def test_doctor_outside_project_complains(tmp_path: Path) -> None:
    runner = CliRunner()
    import os

    cwd = os.getcwd()
    try:
        os.chdir(tmp_path)  # empty dir, no pyproject
        result = runner.invoke(cli, ["doctor"])
        # exit 1 expected
        assert result.exit_code == 1
        assert "pyproject" in result.output.lower()
    finally:
        os.chdir(cwd)
