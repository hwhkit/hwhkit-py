"""Tests for hwhkit.cli.__main__.main() process entry."""

from __future__ import annotations

from hwhkit.cli.__main__ import main


def test_main_help_returns_zero(capsys) -> None:
    """Smoke: --help exits with 0 (Click standard behavior)."""
    rc = main(["--help"])
    assert rc == 0


def test_main_version_returns_zero() -> None:
    rc = main(["version"])
    assert rc == 0


def test_main_unknown_command_returns_nonzero() -> None:
    rc = main(["nonexistent-command"])
    assert rc != 0
