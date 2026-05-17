"""Postgres adapter — SQLAlchemy 2.0 async + asyncpg.

Public surface::

    from hwhkit.integrations.postgres import PostgresProvider, PostgresConfig, get_session
"""

from hwhkit.integrations.postgres.config import PostgresConfig
from hwhkit.integrations.postgres.provider import PostgresProvider
from hwhkit.integrations.postgres.session import get_session

__all__ = ["PostgresConfig", "PostgresProvider", "get_session"]
