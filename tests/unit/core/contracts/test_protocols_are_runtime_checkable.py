"""Smoke test: every contract protocol is @runtime_checkable.

Catches regressions where someone forgets the decorator and isinstance() falls back
to a non-Protocol check.
"""

from __future__ import annotations

from typing import Protocol

from hwhkit.core import contracts

# Non-Protocol exports we skip (concrete classes, type aliases, dataclasses):
_NON_PROTOCOL_EXPORTS = {
    "Codec",  # generic protocol with no @runtime_checkable (parameterized)
    "JsonCodec",  # concrete class
    "PickleCodec",  # concrete class
    "TypedCache",  # concrete class
    "LockToken",  # dataclass
    "PublishAck",  # dataclass
    "ObjectMetadata",  # dataclass
    "VectorRecord",  # dataclass
    "SearchHit",  # dataclass
    "ChatMessage",  # dataclass
    "ChatResponse",  # dataclass
    "JobFunc",  # type alias (Callable)
    "Role",  # type alias (Literal)
    "Severity",  # type alias (Literal)
}


def test_all_protocols_are_runtime_checkable() -> None:
    for name in contracts.__all__:
        if name in _NON_PROTOCOL_EXPORTS:
            continue
        obj = getattr(contracts, name)
        # `isinstance(x, Protocol)` doesn't work for protocol classes themselves,
        # so we check the runtime-checkable marker attribute pyjwt sets.
        assert isinstance(obj, type), f"{name} should be a class"
        assert issubclass(obj, Protocol), f"{name} should subclass Protocol"
        assert getattr(obj, "_is_runtime_protocol", False), (
            f"{name} is a Protocol but missing @runtime_checkable; isinstance() checks will fail"
        )


def test_all_exports_are_importable() -> None:
    """Ensure no typos in __all__."""
    for name in contracts.__all__:
        assert getattr(contracts, name) is not None
