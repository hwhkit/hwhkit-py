"""RelationalDb contract — RDBMS session factory abstraction.

Implementations: Postgres (P0), MySQL (P2).

Adapter-specific session features are accessed via
``ctx.get_typed(PostgresProvider).engine``.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class Session(Protocol):
    """An open database session / transaction context."""

    async def execute(self, query: Any, *args: Any, **kwargs: Any) -> Any: ...

    async def commit(self) -> None: ...

    async def rollback(self) -> None: ...

    async def close(self) -> None: ...

    async def __aenter__(self) -> Session: ...

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None: ...


@runtime_checkable
class RelationalDb(Protocol):
    def session(self) -> Session: ...

    async def ping(self) -> bool: ...


__all__ = ["RelationalDb", "Session"]
