"""Tests for hwhkit.utils.decorators."""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from hwhkit.utils.decorators import retry, safe_execute, timed

# ---- @retry ---------------------------------------------------------------


def test_retry_sync_succeeds_after_failures() -> None:
    calls: list[int] = []

    @retry(attempts=3, exceptions=ValueError, backoff=0.001, jitter=False)
    def go(x: int) -> int:
        calls.append(x)
        if len(calls) < 3:
            raise ValueError("nope")
        return x * 2

    assert go(5) == 10
    assert len(calls) == 3


def test_retry_sync_propagates_after_exhaust() -> None:
    @retry(attempts=2, exceptions=ValueError, backoff=0.001, jitter=False)
    def go() -> None:
        raise ValueError("always")

    with pytest.raises(ValueError, match="always"):
        go()


def test_retry_unlisted_exception_propagates_immediately() -> None:
    calls: list[Any] = []

    @retry(attempts=5, exceptions=ValueError, backoff=0.001, jitter=False)
    def go() -> None:
        calls.append(1)
        raise TypeError("different")

    with pytest.raises(TypeError):
        go()
    assert len(calls) == 1  # no retry


@pytest.mark.asyncio
async def test_retry_async() -> None:
    calls: list[int] = []

    @retry(attempts=3, exceptions=RuntimeError, backoff=0.001, jitter=False)
    async def go() -> str:
        calls.append(1)
        if len(calls) < 3:
            raise RuntimeError("nope")
        return "ok"

    assert await go() == "ok"
    assert len(calls) == 3


def test_retry_invalid_attempts() -> None:
    with pytest.raises(ValueError, match="attempts must"):
        retry(attempts=0)


# ---- @timed ---------------------------------------------------------------


def test_timed_returns_value_unchanged() -> None:
    @timed("custom-label")
    def add(a: int, b: int) -> int:
        return a + b

    assert add(2, 3) == 5


@pytest.mark.asyncio
async def test_timed_async() -> None:
    @timed()
    async def go() -> int:
        await asyncio.sleep(0.001)
        return 42

    assert await go() == 42


# ---- @safe_execute --------------------------------------------------------


def test_safe_execute_returns_default_on_exception() -> None:
    @safe_execute(default="fallback")
    def boom() -> str:
        raise RuntimeError("nope")

    assert boom() == "fallback"


def test_safe_execute_returns_value_when_ok() -> None:
    @safe_execute(default="fallback")
    def ok() -> str:
        return "good"

    assert ok() == "good"


@pytest.mark.asyncio
async def test_safe_execute_async() -> None:
    @safe_execute(default=-1)
    async def boom() -> int:
        raise RuntimeError("nope")

    assert await boom() == -1
