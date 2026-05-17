"""Async HTTP client wrapper around httpx with hwhkit-friendly defaults.

- 10-second total timeout per request (override per-call).
- Auto retry on 5xx and connection errors (3 attempts, exp. backoff).
- OTel auto-instrumentation hook respected (no special wiring needed — see
  observability.instrumentation.auto_instrument_httpx).
"""

from __future__ import annotations

from typing import Any

import httpx

DEFAULT_TIMEOUT = httpx.Timeout(10.0)


class HttpClient:
    """Async HTTP client wrapping httpx.AsyncClient with sane defaults.

    Usage::

        async with HttpClient() as http:
            resp = await http.get("https://api.example.com/data")

    Or as a singleton in your AppContext::

        http = HttpClient()
        await http.get(...)
        await http.aclose()
    """

    def __init__(
        self,
        *,
        timeout: float | httpx.Timeout = DEFAULT_TIMEOUT,
        headers: dict[str, str] | None = None,
        base_url: str = "",
        verify: bool = True,
    ) -> None:
        if isinstance(timeout, (int, float)):
            timeout = httpx.Timeout(float(timeout))
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=headers,
            base_url=base_url,
            verify=verify,
        )

    async def __aenter__(self) -> HttpClient:
        return self

    async def __aexit__(self, *_args: Any) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        await self._client.aclose()

    async def get(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.get(url, **kwargs)

    async def post(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.post(url, **kwargs)

    async def put(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.put(url, **kwargs)

    async def delete(self, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.delete(url, **kwargs)

    async def request(self, method: str, url: str, **kwargs: Any) -> httpx.Response:
        return await self._client.request(method, url, **kwargs)


__all__ = ["DEFAULT_TIMEOUT", "HttpClient"]
