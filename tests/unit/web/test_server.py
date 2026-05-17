"""Tests for hwhkit.web.server CLI surface."""

from __future__ import annotations

import pytest
from hwhkit.web.server import main, run


def test_help_exits_zero(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0
    out = capsys.readouterr().out
    assert "hwhkit-serve" in out


def test_invalid_server_choice() -> None:
    with pytest.raises(SystemExit):
        main(["--app", "x:app", "--server", "bogus"])


def test_run_rejects_unknown_server() -> None:
    with pytest.raises(ValueError, match="unknown server"):
        run("x:app", server="bogus")


def test_granian_rejects_app_instance() -> None:
    """Granian needs an import string, not a FastAPI object — verify clear error.

    We can only test the type-check path; we don't have a granian-importable
    target in unit tests.
    """
    # Skip if granian isn't installed; this test only validates the type check
    pytest.importorskip("granian")
    from fastapi import FastAPI

    with pytest.raises(TypeError, match="import string"):
        run(FastAPI(), server="granian")
