"""Session-scoped fixtures for integration tests using testcontainers.

Containers run per pytest session (one Postgres + one Redis), shared across
tests via fixtures. Each test gets a fresh provider instance + a clean state.

Skipped automatically if Docker is unavailable.
"""

from __future__ import annotations

import logging
import shutil
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

_logger = logging.getLogger(__name__)


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        import subprocess

        result = subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=False)
        return result.returncode == 0
    except Exception:
        return False


pytestmark_docker_required = pytest.mark.skipif(
    not _docker_available(),
    reason="Docker not available; integration tests require Docker daemon",
)


# ---- Postgres -------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_dsn() -> str:
    """Spin up a Postgres 16 container; return SQLAlchemy DSN.

    Reused across the whole pytest session to keep tests fast.
    """
    if not _docker_available():
        pytest.skip("Docker required")
    try:
        from testcontainers.postgres import PostgresContainer
    except ImportError:
        pytest.skip("testcontainers[postgres] not installed")

    with PostgresContainer("postgres:16-alpine") as pg:
        # testcontainers PostgresContainer default driver is psycopg2; we need asyncpg.
        raw = pg.get_connection_url()
        # raw looks like postgresql+psycopg2://test:test@host:port/test
        dsn = raw.replace("postgresql+psycopg2://", "postgresql+asyncpg://")
        # Some versions emit postgresql:// only — normalize:
        dsn = dsn.replace("postgresql://", "postgresql+asyncpg://")
        yield dsn


@pytest.fixture
async def postgres_provider(postgres_dsn: str) -> AsyncGenerator:
    """Per-test PostgresProvider instance; setup + cleanup."""
    from hwhkit.integrations.postgres import PostgresConfig, PostgresProvider

    cfg = PostgresConfig(dsn=postgres_dsn, pool_size=5, max_overflow=2)
    provider = PostgresProvider(config=cfg)

    # Build a minimal ctx — most tests don't actually need it
    from hwhkit.config.base import Settings
    from hwhkit.core.context import AppContext

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    try:
        yield provider
    finally:
        await provider.shutdown()


# ---- Redis ----------------------------------------------------------------


@pytest.fixture(scope="session")
def redis_url() -> str:
    if not _docker_available():
        pytest.skip("Docker required")
    try:
        from testcontainers.redis import RedisContainer
    except ImportError:
        pytest.skip("testcontainers[redis] not installed")

    with RedisContainer("redis:7-alpine") as r:
        host = r.get_container_host_ip()
        port = r.get_exposed_port(6379)
        yield f"redis://{host}:{port}/0"


@pytest.fixture
async def redis_provider(redis_url: str) -> AsyncGenerator:
    from hwhkit.config.base import Settings
    from hwhkit.core.context import AppContext
    from hwhkit.integrations.redis import RedisConfig, RedisProvider

    cfg = RedisConfig(url=redis_url, max_connections=10)
    provider = RedisProvider(config=cfg)

    ctx = AppContext()
    ctx.config = Settings()
    await provider.setup(ctx)
    # Ensure clean state per test
    await provider.client.flushdb()
    try:
        yield provider
    finally:
        await provider.shutdown()
