"""Click command group + subcommand definitions for the ``hwhkit`` CLI."""

from __future__ import annotations

import sys
from pathlib import Path

import click

from hwhkit import __version__


@click.group()
@click.version_option(__version__, prog_name="hwhkit")
def cli() -> None:
    """hwhkit — framework CLI: init / add / doctor / list / version."""


# ---- hwhkit init <name> ----------------------------------------------------


@cli.command("init")
@click.argument("name")
@click.option(
    "--path",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
    help="Directory to create the project in (default: ./<name>).",
)
@click.option(
    "--python",
    default=None,
    help="Pin Python version in pyproject (default: matches current interpreter).",
)
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite if target directory exists.",
)
def cmd_init(name: str, path: Path | None, python: str | None, force: bool) -> None:
    """Create a new hwhkit-based project."""
    from hwhkit.cli.scaffold import init_project

    target = (path or Path(name)).resolve()
    init_project(name=name, target=target, python_version=python, force=force)
    click.echo(f"✓ Created project at {target}")
    click.echo("Next steps:")
    click.echo(f"  cd {target.name}")
    click.echo("  uv sync")
    click.echo("  uv run python -m " + _module_name(name) + ".main")


# ---- hwhkit version --------------------------------------------------------


@cli.command("version")
def cmd_version() -> None:
    """Print framework version."""
    click.echo(__version__)


# ---- hwhkit list -----------------------------------------------------------


@cli.command("list")
def cmd_list() -> None:
    """List integrations declared in the current project's pyproject.toml."""
    from hwhkit.cli.inspect import list_integrations

    project = Path.cwd()
    found = list_integrations(project)
    if not found:
        click.echo("No hwhkit extras declared in pyproject.toml.")
        return
    click.echo("Integrations enabled in pyproject.toml extras:")
    for name in sorted(found):
        click.echo(f"  - {name}")


# ---- hwhkit doctor ---------------------------------------------------------


@cli.command("doctor")
def cmd_doctor() -> None:
    """Quick project health check."""
    from hwhkit.cli.inspect import diagnose

    project = Path.cwd()
    report = diagnose(project)
    if report.problems:
        click.echo("⚠ Issues found:")
        for line in report.problems:
            click.echo(f"  - {line}")
        sys.exit(1)
    click.echo("✓ Project looks healthy")
    for line in report.info:
        click.echo(f"  - {line}")


# ---- hwhkit add <module> ---------------------------------------------------


@cli.command("add")
@click.argument(
    "modules",
    nargs=-1,
    required=True,
    type=click.Choice(
        ["postgres", "redis", "nats", "scheduler", "llm", "auth", "otel"],
        case_sensitive=False,
    ),
)
@click.option(
    "--project",
    type=click.Path(file_okay=False, dir_okay=True, exists=True, path_type=Path),
    default=None,
    help="Project root (default: cwd).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Print intended changes without writing files.",
)
def cmd_add(modules: tuple[str, ...], project: Path | None, dry_run: bool) -> None:
    """Add one or more integrations to the current project."""
    from hwhkit.cli.add import add_modules

    target = project or Path.cwd()
    for mod in modules:
        result = add_modules(target, mod.lower(), dry_run=dry_run)
        click.echo(result)


# ---- helpers ---------------------------------------------------------------


def _module_name(project_name: str) -> str:
    """Convert kebab-case project name to snake_case module name."""
    return project_name.replace("-", "_").replace(" ", "_").lower()
