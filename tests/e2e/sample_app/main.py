"""Sample minimal hwhkit service used by e2e tests.

Has no integrations — purely framework smoke test target.

Per Decision D1: medium-scope sample (CRUD endpoints), so W3 Postgres tests
can reuse the same business route shape.
"""

from __future__ import annotations

from fastapi import APIRouter
from hwhkit.core.bootstrap import bootstrap
from hwhkit.core.errors import NotFoundError
from hwhkit.web.responses import ApiResponse

# ---- in-memory store -------------------------------------------------------
_items: dict[int, dict[str, str | int]] = {}
_next_id = 1

router = APIRouter()


@router.get("/items/{item_id}", response_model=ApiResponse[dict])
async def get_item(item_id: int) -> ApiResponse[dict[str, str | int]]:
    if item_id not in _items:
        raise NotFoundError(f"item {item_id} not found")
    return ApiResponse(data=_items[item_id])


@router.post("/items", response_model=ApiResponse[dict], status_code=201)
async def create_item(payload: dict[str, str]) -> ApiResponse[dict[str, str | int]]:
    global _next_id
    new_id = _next_id
    _next_id += 1
    record: dict[str, str | int] = {"id": new_id, **payload}
    _items[new_id] = record
    return ApiResponse(data=record)


@router.get("/boom")
async def boom() -> None:
    raise RuntimeError("internal-secret-detail-should-not-leak")


# ---- bootstrap exposed to test ---------------------------------------------
def make_app() -> object:
    """Factory used by tests; creates a fresh FastAPI app every call.

    Also resets module-level store + id counter so tests are independent.
    """
    global _next_id
    _items.clear()
    _next_id = 1
    return bootstrap(name="sample", version="0.0.1", routers=[router])


# ASGI entry point for `hwhkit-serve --app tests.e2e.sample_app.main:app`
app = bootstrap(name="sample", version="0.0.1", routers=[router])
