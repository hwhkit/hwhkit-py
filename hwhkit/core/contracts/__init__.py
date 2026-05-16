"""hwhkit contracts — protocol definitions (the 'ports' in hexagonal arch).

Business code depends ONLY on these protocols. Concrete adapter
implementations live in ``hwhkit.integrations.*``.

See spec § 5.
"""

from hwhkit.core.contracts.cache import Cache, Codec, JsonCodec, PickleCodec, TypedCache
from hwhkit.core.contracts.kv_store import KvStore
from hwhkit.core.contracts.llm import (
    ChatMessage,
    ChatResponse,
    EmbeddingClient,
    LlmClient,
    Role,
)
from hwhkit.core.contracts.lock import DistributedLock, LockToken
from hwhkit.core.contracts.message_bus import (
    Message,
    MessageBus,
    PublishAck,
    Subscription,
)
from hwhkit.core.contracts.notifier import Notifier, Severity
from hwhkit.core.contracts.object_store import ObjectMetadata, ObjectStore
from hwhkit.core.contracts.relational_db import RelationalDb, Session
from hwhkit.core.contracts.scheduler import JobFunc, Scheduler
from hwhkit.core.contracts.secrets import SecretsProvider
from hwhkit.core.contracts.telemetry import (
    Counter,
    Histogram,
    LogEmitter,
    Meter,
    Span,
    Tracer,
)
from hwhkit.core.contracts.vector_store import SearchHit, VectorRecord, VectorStore

__all__ = [
    "Cache",
    "ChatMessage",
    "ChatResponse",
    "Codec",
    "Counter",
    "DistributedLock",
    "EmbeddingClient",
    "Histogram",
    "JobFunc",
    "JsonCodec",
    "KvStore",
    "LlmClient",
    "LockToken",
    "LogEmitter",
    "Message",
    "MessageBus",
    "Meter",
    "Notifier",
    "ObjectMetadata",
    "ObjectStore",
    "PickleCodec",
    "PublishAck",
    "RelationalDb",
    "Role",
    "Scheduler",
    "SearchHit",
    "SecretsProvider",
    "Session",
    "Severity",
    "Span",
    "Subscription",
    "Tracer",
    "TypedCache",
    "VectorRecord",
    "VectorStore",
]
