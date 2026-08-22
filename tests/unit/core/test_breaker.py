"""Tests for hwhkit.core.breaker.CircuitBreaker."""

from __future__ import annotations

import threading
import time

import pytest
from hwhkit.core.breaker import CircuitBreaker


class TestInit:
    def test_defaults(self) -> None:
        b = CircuitBreaker()
        assert b.state == "closed"
        assert b.failures == 0

    def test_rejects_zero_threshold(self) -> None:
        with pytest.raises(ValueError, match="fail_threshold"):
            CircuitBreaker(fail_threshold=0)

    def test_rejects_negative_cooldown(self) -> None:
        with pytest.raises(ValueError, match="cooldown_s"):
            CircuitBreaker(cooldown_s=-0.1)


class TestStateMachine:
    def test_closed_to_open_after_threshold(self) -> None:
        b = CircuitBreaker(fail_threshold=3, cooldown_s=10.0)
        assert b.decide() == "proceed"
        b.on_failure()
        assert b.state == "closed"
        b.on_failure()
        assert b.state == "closed"
        b.on_failure()
        assert b.state == "open", "threshold reached → must trip Open"

    def test_open_rejects_until_cooldown(self) -> None:
        b = CircuitBreaker(fail_threshold=1, cooldown_s=10.0)
        b.on_failure()
        assert b.state == "open"
        # Still inside cooldown → rejected.
        for _ in range(5):
            assert b.decide() == "rejected"
        assert b.state == "open"

    def test_open_flips_to_half_open_after_cooldown(self) -> None:
        b = CircuitBreaker(fail_threshold=1, cooldown_s=0.01)
        b.on_failure()
        assert b.state == "open"
        time.sleep(0.02)
        verdict = b.decide()
        assert verdict == "probe"
        assert b.state == "half_open"

    def test_half_open_success_closes(self) -> None:
        b = CircuitBreaker(fail_threshold=1, cooldown_s=0.01)
        b.on_failure()
        time.sleep(0.02)
        assert b.decide() == "probe"
        b.on_success()
        assert b.state == "closed"
        assert b.failures == 0

    def test_half_open_failure_reopens(self) -> None:
        b = CircuitBreaker(fail_threshold=1, cooldown_s=0.01)
        b.on_failure()
        time.sleep(0.02)
        assert b.decide() == "probe"
        b.on_failure()
        assert b.state == "open"
        # Cooldown restarted — immediate decide is rejected.
        assert b.decide() == "rejected"

    def test_success_in_closed_keeps_closed(self) -> None:
        b = CircuitBreaker(fail_threshold=3, cooldown_s=10.0)
        b.on_failure()
        b.on_success()
        assert b.state == "closed"
        assert b.failures == 0

    def test_consecutive_failures_only(self) -> None:
        """on_success clears the counter; threshold counts consecutive only."""
        b = CircuitBreaker(fail_threshold=3, cooldown_s=10.0)
        b.on_failure()
        b.on_failure()
        b.on_success()
        b.on_failure()
        b.on_failure()
        assert b.state == "closed", "non-consecutive failures must not trip"

    def test_reset_returns_to_closed(self) -> None:
        b = CircuitBreaker(fail_threshold=1, cooldown_s=10.0)
        b.on_failure()
        assert b.state == "open"
        b.reset()
        assert b.state == "closed"
        assert b.failures == 0
        assert b.decide() == "proceed"


class TestThreadSafety:
    def test_concurrent_failures_and_successes_do_not_corrupt_state(self) -> None:
        """Smoke test — N threads hammer on_failure/on_success/decide.

        We do not assert a specific terminal state (the interleaving makes
        that nondeterministic by design); we assert only that no exception
        escapes, the state ends up in a legal value, and the failures
        counter stays non-negative.
        """
        b = CircuitBreaker(fail_threshold=50, cooldown_s=0.001)
        iterations = 500
        n_threads = 8

        def hammer_fail() -> None:
            for _ in range(iterations):
                b.on_failure()
                b.decide()

        def hammer_ok() -> None:
            for _ in range(iterations):
                b.on_success()
                b.decide()

        threads = []
        for i in range(n_threads):
            target = hammer_fail if i % 2 == 0 else hammer_ok
            threads.append(threading.Thread(target=target))
        for t in threads:
            t.start()
        for t in threads:
            t.join(timeout=10.0)
            assert not t.is_alive(), "thread hung — possible deadlock"

        assert b.state in {"closed", "open", "half_open"}
        assert b.failures >= 0
