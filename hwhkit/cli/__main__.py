"""``hwhkit`` CLI entrypoint.

Registered in pyproject.toml as ``[project.scripts] hwhkit = "hwhkit.cli.__main__:main"``.
"""

from __future__ import annotations

import sys


def main(argv: list[str] | None = None) -> int:
    """CLI entry. Returns process exit code."""
    try:
        import click
    except ImportError:
        print(
            "hwhkit CLI requires the [cli] extra: pip install 'hwhkit[cli]'",
            file=sys.stderr,
        )
        return 1

    from hwhkit.cli.commands import cli

    try:
        cli.main(args=argv, prog_name="hwhkit", standalone_mode=False)
    except click.exceptions.Exit as exc:
        return int(exc.exit_code)
    except click.exceptions.UsageError as exc:
        exc.show()
        return 2
    except KeyboardInterrupt:
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
