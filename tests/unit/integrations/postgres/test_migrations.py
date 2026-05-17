"""Cover hwhkit.integrations.postgres.migrations module surface."""

from __future__ import annotations

from hwhkit.integrations.postgres.migrations import (
    ENV_PY_TEMPLATE,
    run_migrations_offline,
    run_migrations_online,
)


def test_env_py_template_is_valid_python() -> None:
    # The template is a string we'll write to user projects; ensure it parses
    compile(ENV_PY_TEMPLATE, "<env.py>", "exec")


def test_env_py_template_contains_required_calls() -> None:
    assert "run_migrations_online" in ENV_PY_TEMPLATE
    assert "run_migrations_offline" in ENV_PY_TEMPLATE
    assert "create_async_engine" in ENV_PY_TEMPLATE


def test_run_migrations_offline_imports() -> None:
    """Smoke: ensure the function is callable (alembic raises if no migrations)."""
    assert callable(run_migrations_offline)


def test_run_migrations_online_imports() -> None:
    assert callable(run_migrations_online)
