"""Tests for hwhkit.core.shutdown."""

from __future__ import annotations

import asyncio

import pytest
from hwhkit.core.shutdown import GracefulShutdown, ShutdownTimeout


class TestGracefulShutdown:
    @pytest.mark.asyncio
    async def test_runs_callbacks_in_reverse_order(self) -> None:
        order: list[str] = []
        gs = GracefulShutdown(timeout=2.0)
        gs.register("a", lambda: order.append("a"))
        gs.register("b", lambda: order.append("b"))
        gs.register("c", lambda: order.append("c"))
        await gs.run()
        assert order == ["c", "b", "a"]

    @pytest.mark.asyncio
    async def test_async_callbacks_awaited(self) -> None:
        flags: list[bool] = []

        async def cb() -> None:
            await asyncio.sleep(0.01)
            flags.append(True)

        gs = GracefulShutdown(timeout=2.0)
        gs.register("async-cb", cb)
        await gs.run()
        assert flags == [True]

    @pytest.mark.asyncio
    async def test_timeout_kills_slow_callback(self) -> None:
        async def slow() -> None:
            await asyncio.sleep(5.0)

        gs = GracefulShutdown(timeout=0.05)
        gs.register("slow", slow)
        with pytest.raises(ShutdownTimeout, match="slow"):
            await gs.run()

    @pytest.mark.asyncio
    async def test_one_failing_callback_does_not_block_others(self) -> None:
        order: list[str] = []

        def bad() -> None:
            raise RuntimeError("kaboom")

        def good() -> None:
            order.append("good")

        gs = GracefulShutdown(timeout=2.0)
        gs.register("bad", bad)
        gs.register("good", good)
        await gs.run()
        assert order == ["good"]
