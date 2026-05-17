"""Cover hwhkit.web.server branches via importlib-mocking the underlying servers."""

from __future__ import annotations

import sys
from types import ModuleType
from unittest.mock import MagicMock

import pytest
from hwhkit.web.server import (
    _run_granian,
    _run_gunicorn,
    _run_uvicorn,
    main,
    run,
)

# ---- run() dispatcher branches --------------------------------------------


def test_run_dispatch_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    """run(server="uvicorn") routes to uvicorn.run."""
    fake = ModuleType("uvicorn")
    fake.run = MagicMock()  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "uvicorn", fake)

    from fastapi import FastAPI

    run(FastAPI(), server="uvicorn", port=12345)
    fake.run.assert_called_once()  # type: ignore[attr-defined]
    kwargs = fake.run.call_args.kwargs  # type: ignore[attr-defined]
    assert kwargs["port"] == 12345


def test_run_dispatch_granian_string(monkeypatch: pytest.MonkeyPatch) -> None:
    """granian dispatch with an import string — verify it reaches Granian()."""
    fake = ModuleType("granian")
    granian_instance = MagicMock()
    fake.Granian = MagicMock(return_value=granian_instance)  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "granian", fake)

    run("my.module:app", server="granian", port=9001)
    fake.Granian.assert_called_once()  # type: ignore[attr-defined]
    kwargs = fake.Granian.call_args.kwargs  # type: ignore[attr-defined]
    assert kwargs["target"] == "my.module:app"
    assert kwargs["port"] == 9001
    granian_instance.serve.assert_called_once()


def test_run_granian_missing_extra_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """If granian is not installed, _run_granian raises ImportError with hint."""

    def _fail_import(name: str) -> ModuleType:
        if name == "granian":
            raise ImportError("no granian")
        raise ImportError(name)

    monkeypatch.setattr("importlib.import_module", _fail_import)

    with pytest.raises(ImportError, match="granian"):
        _run_granian(
            "x:app",
            host="0.0.0.0",
            port=8000,
            workers=1,
            log_level="info",
        )


def test_run_uvicorn_missing_extra_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_import(name: str) -> ModuleType:
        if name == "uvicorn":
            raise ImportError("no uvicorn")
        raise ImportError(name)

    monkeypatch.setattr("importlib.import_module", _fail_import)

    from fastapi import FastAPI

    with pytest.raises(ImportError, match="uvicorn"):
        _run_uvicorn(
            FastAPI(),
            host="0.0.0.0",
            port=8000,
            workers=1,
            log_level="info",
            reload=False,
        )


def test_run_gunicorn_missing_extra_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    def _fail_import(name: str) -> ModuleType:
        if name == "gunicorn":
            raise ImportError("no gunicorn")
        raise ImportError(name)

    monkeypatch.setattr("importlib.import_module", _fail_import)

    with pytest.raises(ImportError, match="gunicorn"):
        _run_gunicorn("x:app", host="0.0.0.0", port=8000, workers=1)


def test_run_gunicorn_rejects_fastapi_instance() -> None:
    """gunicorn shim requires import string, not a FastAPI object."""
    from fastapi import FastAPI

    # We need gunicorn importable to get past the missing-extra check.
    pytest.importorskip("gunicorn")
    with pytest.raises(TypeError, match="import string"):
        _run_gunicorn(FastAPI(), host="x", port=1, workers=1)  # type: ignore[arg-type]


# ---- main() CLI branches --------------------------------------------------


def test_main_keyboard_interrupt(monkeypatch: pytest.MonkeyPatch) -> None:
    """SIGINT-style cancellation returns exit code 0."""

    def _raise_kbd(*_a, **_kw):
        raise KeyboardInterrupt

    monkeypatch.setattr("hwhkit.web.server.run", _raise_kbd)
    rc = main(["--app", "x:app", "--server", "uvicorn"])
    assert rc == 0


def test_main_import_error_returns_nonzero(monkeypatch: pytest.MonkeyPatch) -> None:
    """Missing server extra → exit 1 with stderr hint."""

    def _raise_import(*_a, **_kw):
        raise ImportError("missing extra")

    monkeypatch.setattr("hwhkit.web.server.run", _raise_import)
    rc = main(["--app", "x:app", "--server", "granian"])
    assert rc == 1
