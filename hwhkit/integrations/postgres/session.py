"""FastAPI Depends helper: ``get_session(request)`` yields per-request AsyncSession.

Auto-commits at end of handler on success; rolls back on exception. Business
code uses it like::

    @router.get("/items/{id}")
    async def get_item(
        id: int,
        session: AsyncSession = Depends(get_session),
    ) -> Item:
        result = await session.execute(select(Item).where(Item.id == id))
        return result.scalar_one()

Routes that need finer transaction control (e.g. SAVEPOINTs, multi-commit jobs)
should use ``ctx.get_typed(PostgresProvider).session()`` directly.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from starlette.requests import Request


async def get_session(request: Request) -> AsyncIterator[Any]:
    """FastAPI dependency; lazily resolves PostgresProvider from AppContext.

    Yields the SQLAlchemy AsyncSession. Caller's responsibility to ``commit()``;
    if the request raises, ``rollback()`` is invoked automatically.
    """
    from hwhkit.integrations.postgres.provider import PostgresProvider

    ctx = request.app.state.ctx
    provider: PostgresProvider = ctx.get_typed(PostgresProvider)
    async with provider.session() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise


__all__ = ["get_session"]
