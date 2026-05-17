# Postgres

`hwhkit.integrations.postgres.PostgresProvider` is a SQLAlchemy 2.0 async +
asyncpg adapter implementing the `RelationalDb` contract.

## Install

```bash
hwhkit add postgres
# or manually:
pip install "hwhkit[postgres]"
```

## Configuration

```bash
HWHKIT_POSTGRES__DSN=postgresql+asyncpg://user:pwd@host:5432/dbname
HWHKIT_POSTGRES__POOL_SIZE=10
HWHKIT_POSTGRES__MAX_OVERFLOW=5
HWHKIT_POSTGRES__POOL_PRE_PING=true
HWHKIT_POSTGRES__POOL_RECYCLE_SECONDS=3600
HWHKIT_POSTGRES__ECHO=false
```

## Usage in business code

```python
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hwhkit.integrations.postgres import get_session

from my_service.domain import User

router = APIRouter()


@router.get("/users/{id}")
async def get_user(id: int, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.id == id))
    return result.scalar_one_or_none()
```

`get_session()` yields a fresh `AsyncSession` per request; it auto-rolls-back
on exception. Your handler controls `commit()`.

## Direct adapter access

For Postgres-specific features:

```python
from hwhkit.integrations.postgres import PostgresProvider

pg = ctx.get_typed(PostgresProvider)
async with pg.engine.connect() as conn:
    await conn.execute(text("SELECT * FROM t WHERE data @> '{\"x\": 1}'"))
```

## Migrations

```bash
hwhkit add postgres
# scaffolds:
#   alembic.ini
#   migrations/env.py  (wired to your AsyncEngine)
#   migrations/versions/
```

Generate revisions:

```bash
uv run alembic revision --autogenerate -m "add users table"
uv run alembic upgrade head
```

## Health check

`PostgresProvider.health_check()` runs `SELECT 1` and reports unhealthy
on failure. `/readyz` aggregates this; load balancers should target
`/readyz` not `/healthz` for traffic gating.

## Testing

For unit tests of business code that uses Postgres:

```python
from hwhkit.testing.fakes import FakeRelationalDb

async def test_user_service() -> None:
    svc = UserService(db=FakeRelationalDb())
    ...
```

`FakeRelationalDb` is sqlite-in-memory under the hood — real SQL parser,
not Postgres-specific features. Use real Postgres in integration tests
(testcontainers fixtures provided).
