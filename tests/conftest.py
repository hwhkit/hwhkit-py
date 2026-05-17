"""Global pytest fixtures for hwhkit test suite.

Per-layer conftest files live under tests/integration/conftest.py etc.
"""

from __future__ import annotations

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Force asyncio (vs trio) for any anyio-based tests."""
    return "asyncio"
