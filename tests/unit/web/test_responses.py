"""Tests for hwhkit.web.responses."""

from __future__ import annotations

import pytest
from hwhkit.web.responses import (
    ApiResponse,
    PageResponse,
    is_raw_response,
    raw_response,
)


class TestApiResponse:
    def test_defaults(self) -> None:
        r: ApiResponse[None] = ApiResponse()
        assert r.code == 0
        assert r.message == "ok"
        assert r.data is None
        assert r.trace_id is None  # no active OTel span

    def test_with_data(self) -> None:
        r: ApiResponse[dict[str, int]] = ApiResponse(data={"id": 42})
        assert r.data == {"id": 42}

    def test_error_envelope(self) -> None:
        r: ApiResponse[None] = ApiResponse(code=100404, message="not found")
        assert r.code == 100404
        assert r.message == "not found"

    def test_json_shape(self) -> None:
        r: ApiResponse[dict[str, int]] = ApiResponse(data={"x": 1})
        payload = r.model_dump()
        assert payload == {"code": 0, "message": "ok", "data": {"x": 1}, "trace_id": None}

    def test_trace_id_injected_from_active_span(self) -> None:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider

        # ensure provider with sane defaults
        if not isinstance(trace.get_tracer_provider(), TracerProvider):
            trace.set_tracer_provider(TracerProvider())
        tracer = trace.get_tracer("test")

        with tracer.start_as_current_span("op"):
            r: ApiResponse[None] = ApiResponse()
            assert r.trace_id is not None
            assert len(r.trace_id) == 32


class TestPageResponse:
    def test_defaults(self) -> None:
        p: PageResponse[int] = PageResponse()
        assert p.items == []
        assert p.total == 0
        assert p.page == 1
        assert p.page_size == 20
        assert p.has_next is False

    def test_with_items(self) -> None:
        p: PageResponse[int] = PageResponse(items=[1, 2, 3], total=100, page=2, has_next=True)
        assert p.items == [1, 2, 3]
        assert p.total == 100
        assert p.has_next is True

    def test_nested_in_api_response(self) -> None:
        page: PageResponse[dict[str, int]] = PageResponse(
            items=[{"id": 1}, {"id": 2}],
            total=2,
        )
        env: ApiResponse[PageResponse[dict[str, int]]] = ApiResponse(data=page)
        payload = env.model_dump()
        assert payload["data"]["items"] == [{"id": 1}, {"id": 2}]
        assert payload["data"]["total"] == 2


class TestRawResponse:
    def test_decorator_marks_function(self) -> None:
        @raw_response
        async def my_route() -> None:
            return None

        assert is_raw_response(my_route) is True

    def test_undecorated_function(self) -> None:
        async def normal_route() -> None:
            return None

        assert is_raw_response(normal_route) is False

    def test_decorator_preserves_callable(self) -> None:
        @raw_response
        def sync_fn(x: int) -> int:
            return x * 2

        assert sync_fn(3) == 6


def test_smoke_api_response_with_str() -> None:
    r: ApiResponse[str] = ApiResponse(data="hello")
    assert r.data == "hello"


@pytest.mark.parametrize(
    ("code", "msg"),
    [
        (100404, "not found"),
        (100422, "validation failed"),
        (500000, "internal error"),
        (500001, "integration error"),
    ],
)
def test_various_error_codes(code: int, msg: str) -> None:
    r: ApiResponse[None] = ApiResponse(code=code, message=msg)
    assert r.code == code
    assert r.message == msg
