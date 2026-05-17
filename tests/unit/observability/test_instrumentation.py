"""Tests for hwhkit.observability.instrumentation."""

from __future__ import annotations

from hwhkit.observability.instrumentation import (
    EXCLUDED_URLS,
    auto_instrument_all,
    auto_instrument_httpx,
)


def test_excluded_urls_constant() -> None:
    assert "/healthz" in EXCLUDED_URLS
    assert "/readyz" in EXCLUDED_URLS
    assert "/metrics" in EXCLUDED_URLS
    assert "/version" in EXCLUDED_URLS


def test_httpx_instrumentation_idempotent() -> None:
    # First call may install; second call must not raise either way
    auto_instrument_httpx()
    auto_instrument_httpx()


def test_auto_instrument_all_returns_map() -> None:
    result = auto_instrument_all(app=None)
    assert isinstance(result, dict)
    assert "httpx" in result
    # Each value is True (instrumented) or False (package missing) — both valid
    for v in result.values():
        assert isinstance(v, bool)
