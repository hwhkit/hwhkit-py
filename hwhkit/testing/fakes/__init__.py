"""In-memory contract implementations for business unit tests.

Each fake passes the corresponding contract conformance tests, ensuring
semantic equivalence with the real adapter.

Imports::

    from hwhkit.testing.fakes import (
        FakeCache,
        FakeDistributedLock,
        FakeKvStore,
        FakeMessageBus,
        FakeRelationalDb,
    )
"""

from hwhkit.testing.fakes.cache import FakeCache
from hwhkit.testing.fakes.kv_store import FakeKvStore
from hwhkit.testing.fakes.lock import FakeDistributedLock
from hwhkit.testing.fakes.message_bus import FakeMessageBus

__all__ = [
    "FakeCache",
    "FakeDistributedLock",
    "FakeKvStore",
    "FakeMessageBus",
]
