"""Circuit breaker — Closed → Open → HalfOpen state machine.

Provides a small, thread-safe breaker with the public surface aligned across
the rs/go/py implementations of hwhkit so that bench/chaos harnesses can
target the same vocabulary across languages.

State machine
-------------
* ``closed``     — calls flow through. Consecutive ``on_failure()`` calls
                    increment a counter; when the counter reaches
                    ``fail_threshold`` the breaker trips to ``open``.
* ``open``       — calls are rejected fast. After ``cooldown_s`` has elapsed
                    since the trip, the next ``decide()`` flips the breaker
                    into ``half_open`` and permits exactly one probe.
* ``half_open``  — exactly one probe is in flight. ``on_success()`` closes
                    the breaker and resets the failure counter;
                    ``on_failure()`` re-opens it and restarts the cooldown.

The ``decide()`` return is a string, not a bool, so that the caller can
distinguish a normal Closed-state "proceed" from a HalfOpen "probe" (the
caller may want to mark the probe specifically, e.g. for telemetry).

Thread safety
-------------
All public methods are guarded by a ``threading.Lock``. The breaker may be
shared across threads. ``asyncio`` callers do not need the lock for
correctness on a single event loop, but using ``threading.Lock`` here keeps
the contract uniform with the rs/go sibling breakers.
"""

from __future__ import annotations

import threading
import time

_CLOSED = "closed"
_OPEN = "open"
_HALF_OPEN = "half_open"


class CircuitBreaker:
    """Three-state circuit breaker (Closed / Open / HalfOpen).

    Parameters
    ----------
    fail_threshold:
        Consecutive ``on_failure()`` calls required to trip Closed → Open.
        Must be ``>= 1``.
    cooldown_s:
        Seconds to remain in Open before the next ``decide()`` flips the
        breaker to HalfOpen and permits a single probe. Must be ``>= 0``.

    Examples
    --------
    >>> b = CircuitBreaker(fail_threshold=2, cooldown_s=0.01)
    >>> b.decide()
    'proceed'
    >>> b.on_failure(); b.on_failure()
    >>> b.state
    'open'
    >>> b.decide()
    'rejected'
    """

    __slots__ = (
        "_cooldown_s",
        "_fail_threshold",
        "_failures",
        "_lock",
        "_opened_at",
        "_state",
    )

    def __init__(self, fail_threshold: int = 5, cooldown_s: float = 30.0) -> None:
        if fail_threshold < 1:
            raise ValueError("fail_threshold must be >= 1")
        if cooldown_s < 0:
            raise ValueError("cooldown_s must be >= 0")
        self._fail_threshold = fail_threshold
        self._cooldown_s = cooldown_s
        self._lock = threading.Lock()
        self._state = _CLOSED
        self._failures = 0
        self._opened_at = 0.0

    @property
    def state(self) -> str:
        """Current state — one of ``"closed"``, ``"open"``, ``"half_open"``."""
        with self._lock:
            return self._state

    @property
    def failures(self) -> int:
        """Consecutive-failure counter (resets on close / reset)."""
        with self._lock:
            return self._failures

    def decide(self) -> str:
        """Return the gating verdict for the next call.

        Returns
        -------
        ``"proceed"``
            Closed — the call should run normally.
        ``"probe"``
            HalfOpen — the call is the single probe; on success the breaker
            closes, on failure it re-opens.
        ``"rejected"``
            Open and still within cooldown — the caller must fail fast.

        Side effect: if the breaker is Open and the cooldown has elapsed,
        the first ``decide()`` flips state to HalfOpen and returns
        ``"probe"``.
        """
        with self._lock:
            if self._state == _CLOSED:
                return "proceed"
            if self._state == _OPEN:
                if (time.monotonic() - self._opened_at) >= self._cooldown_s:
                    self._state = _HALF_OPEN
                    return "probe"
                return "rejected"
            # HALF_OPEN — the probe is permitted exactly once. Subsequent
            # decide() calls before on_success/on_failure also return "probe";
            # the contract is that the caller drives one probe at a time.
            return "probe"

    def on_success(self) -> None:
        """Record a successful call.

        From any state, a success closes the breaker and clears the failure
        counter. (In Closed this is a no-op on state; the counter is already
        zero by construction after the last failure-or-close.)
        """
        with self._lock:
            self._state = _CLOSED
            self._failures = 0

    def on_failure(self) -> None:
        """Record a failed call.

        * Closed: increment the counter; trip Open if it reaches
          ``fail_threshold``.
        * HalfOpen: re-open the breaker and restart the cooldown clock.
        * Open: bump the counter (kept monotone), state unchanged.
        """
        with self._lock:
            self._failures += 1
            if self._state == _HALF_OPEN or (
                self._state == _CLOSED and self._failures >= self._fail_threshold
            ):
                self._state = _OPEN
                self._opened_at = time.monotonic()

    def reset(self) -> None:
        """Force the breaker back to Closed and clear the failure counter."""
        with self._lock:
            self._state = _CLOSED
            self._failures = 0
            self._opened_at = 0.0


__all__ = ["CircuitBreaker"]
