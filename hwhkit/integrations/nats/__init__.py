"""NATS adapter — JetStream MessageBus impl.

Public surface::

    from hwhkit.integrations.nats import NatsProvider, NatsConfig
"""

from hwhkit.integrations.nats.config import NatsConfig
from hwhkit.integrations.nats.provider import NatsProvider

__all__ = ["NatsConfig", "NatsProvider"]
