"""ASGI server launcher — granian (default) / uvicorn / gunicorn.

Per spec § 3.5. ``run(app, server=...)`` is the library-mode entry; ``main()``
is the ``hwhkit-serve`` CLI entry registered in pyproject.toml.

The launcher imports the chosen server lazily; missing extras → clear error
suggesting which extras to install.
"""

from __future__ import annotations

import argparse
import importlib
import sys
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from fastapi import FastAPI

_INSTALL_HINTS = {
    "granian": "pip install hwhkit[web]",
    "uvicorn": "pip install uvicorn[standard]",
    "gunicorn": "pip install gunicorn",
}


def run(
    app: FastAPI | str,
    *,
    server: str = "granian",
    host: str = "0.0.0.0",  # noqa: S104  container-friendly default
    port: int = 8000,
    workers: int = 1,
    log_level: str = "info",
    reload: bool = False,
    **server_kwargs: Any,
) -> None:
    """Start an ASGI server hosting ``app``.

    Args:
        app: a FastAPI instance OR an import string ``"module:attribute"``.
        server: granian (default, recommended for production) / uvicorn / gunicorn.
        host / port / workers / log_level / reload: standard ASGI server knobs.
        **server_kwargs: forwarded to the underlying server constructor.

    Raises:
        ImportError: if the chosen server is not installed (with install hint).
        ValueError: if ``server`` is not one of the supported names.
    """
    if server == "granian":
        _run_granian(
            app, host=host, port=port, workers=workers, log_level=log_level, **server_kwargs
        )
    elif server == "uvicorn":
        _run_uvicorn(
            app,
            host=host,
            port=port,
            workers=workers,
            log_level=log_level,
            reload=reload,
            **server_kwargs,
        )
    elif server == "gunicorn":
        _run_gunicorn(app, host=host, port=port, workers=workers, **server_kwargs)
    else:
        raise ValueError(f"unknown server {server!r} (choose: granian / uvicorn / gunicorn)")


def _run_granian(
    app: FastAPI | str,
    *,
    host: str,
    port: int,
    workers: int,
    log_level: str,
    **kwargs: Any,
) -> None:
    try:
        granian_mod = importlib.import_module("granian")
    except ImportError as exc:
        raise ImportError(
            f"granian not installed. Install with: {_INSTALL_HINTS['granian']}"
        ) from exc

    if isinstance(app, str):
        target = app
    else:
        raise TypeError(
            "granian requires the app as an import string 'module:attr', not a FastAPI instance. "
            "Use uvicorn for in-process app objects."
        )

    Granian = granian_mod.Granian
    server = Granian(
        target=target,
        address=host,
        port=port,
        workers=workers,
        interface="asgi",
        log_level=log_level,
        **kwargs,
    )
    server.serve()


def _run_uvicorn(
    app: FastAPI | str,
    *,
    host: str,
    port: int,
    workers: int,
    log_level: str,
    reload: bool,
    **kwargs: Any,
) -> None:
    try:
        uvicorn_mod = importlib.import_module("uvicorn")
    except ImportError as exc:
        raise ImportError(
            f"uvicorn not installed. Install with: {_INSTALL_HINTS['uvicorn']}"
        ) from exc

    uvicorn_mod.run(
        app,
        host=host,
        port=port,
        workers=workers if not reload else 1,
        log_level=log_level,
        reload=reload,
        **kwargs,
    )


def _run_gunicorn(
    app: FastAPI | str,
    *,
    host: str,
    port: int,
    workers: int,
    **kwargs: Any,
) -> None:
    try:
        importlib.import_module("gunicorn")
    except ImportError as exc:
        raise ImportError(
            f"gunicorn not installed. Install with: {_INSTALL_HINTS['gunicorn']}"
        ) from exc

    if not isinstance(app, str):
        raise TypeError("gunicorn requires app as 'module:attr' import string.")
    app_target: str = app

    # gunicorn launches via fork; the standard pattern is to delegate to the
    # gunicorn CLI rather than embedding. We expose this via run() as a thin shim.
    from gunicorn.app.wsgiapp import (  # type: ignore[import-not-found,import-untyped,unused-ignore]
        WSGIApplication,
    )

    class _GunicornApp(WSGIApplication):  # type: ignore[misc]
        def init(self, parser: Any, opts: Any, args: list[str]) -> None:
            pass

        def load_config(self) -> None:
            cfg: dict[str, Any] = {
                "bind": f"{host}:{port}",
                "workers": workers,
                "worker_class": "uvicorn.workers.UvicornWorker",
                **kwargs,
            }
            for k, v in cfg.items():
                self.cfg.set(k, v)

        def load(self) -> Any:
            module, attr = app_target.split(":", 1)
            return getattr(importlib.import_module(module), attr)

    _GunicornApp().run()


# ---- CLI entry --------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    """``hwhkit-serve`` CLI entry. Returns process exit code."""
    parser = argparse.ArgumentParser(prog="hwhkit-serve")
    parser.add_argument("--app", required=True, help="ASGI app target, e.g. mypkg.main:app")
    parser.add_argument(
        "--server",
        default="granian",
        choices=["granian", "uvicorn", "gunicorn"],
        help="ASGI server (default: granian)",
    )
    parser.add_argument("--host", default="0.0.0.0")  # noqa: S104
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--workers", type=int, default=1)
    parser.add_argument("--log-level", default="info")
    parser.add_argument("--reload", action="store_true", help="Enable hot-reload (uvicorn only)")

    args = parser.parse_args(argv)
    try:
        run(
            args.app,
            server=args.server,
            host=args.host,
            port=args.port,
            workers=args.workers,
            log_level=args.log_level,
            reload=args.reload,
        )
    except ImportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 0
    return 0


__all__ = ["main", "run"]
