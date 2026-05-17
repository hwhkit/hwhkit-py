"""Tests for hwhkit.utils.http.HttpClient."""

from __future__ import annotations

import httpx
import pytest
import respx
from httpx import Response
from hwhkit.utils.http import DEFAULT_TIMEOUT, HttpClient


def test_default_timeout_is_httpx_timeout() -> None:
    assert isinstance(DEFAULT_TIMEOUT, httpx.Timeout)


@pytest.mark.asyncio
async def test_get() -> None:
    async with HttpClient() as client:
        with respx.mock(base_url="https://example.test") as mock:
            mock.get("/x").mock(return_value=Response(200, json={"ok": True}))
            r = await client.get("https://example.test/x")
            assert r.status_code == 200
            assert r.json() == {"ok": True}


@pytest.mark.asyncio
async def test_post_put_delete() -> None:
    async with HttpClient() as client:
        with respx.mock(base_url="https://example.test") as mock:
            mock.post("/x").mock(return_value=Response(201))
            mock.put("/x/1").mock(return_value=Response(204))
            mock.delete("/x/1").mock(return_value=Response(204))
            assert (await client.post("https://example.test/x")).status_code == 201
            assert (await client.put("https://example.test/x/1")).status_code == 204
            assert (await client.delete("https://example.test/x/1")).status_code == 204


@pytest.mark.asyncio
async def test_request_method() -> None:
    async with HttpClient() as client:
        with respx.mock(base_url="https://example.test") as mock:
            mock.patch("/x").mock(return_value=Response(200))
            r = await client.request("PATCH", "https://example.test/x")
            assert r.status_code == 200


@pytest.mark.asyncio
async def test_timeout_int_coerced() -> None:
    """Constructor accepts int/float and wraps into httpx.Timeout."""
    async with HttpClient(timeout=5.0) as client:
        assert client._client.timeout.connect == 5.0


@pytest.mark.asyncio
async def test_base_url_and_headers() -> None:
    async with HttpClient(base_url="https://x.test", headers={"X-Trace": "abc"}) as client:
        with respx.mock(base_url="https://x.test") as mock:
            route = mock.get("/y").mock(return_value=Response(200))
            await client.get("/y")
            assert route.called
            assert route.calls.last.request.headers.get("X-Trace") == "abc"


@pytest.mark.asyncio
async def test_aclose_idempotent() -> None:
    client = HttpClient()
    await client.aclose()
    # Second close should not crash
    await client.aclose()
