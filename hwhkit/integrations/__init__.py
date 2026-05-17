"""hwhkit.integrations — concrete adapter implementations.

Each subpackage corresponds to one external service. They lazy-import their
underlying driver only on ``setup()``, so the module is import-safe without
optional extras installed.

P0 (W3):
- ``postgres``  — SQLAlchemy 2.0 async, satisfies ``RelationalDb`` contract.
- ``redis``     — redis.asyncio, satisfies ``Cache`` + ``KvStore`` + ``DistributedLock`` + ``MessageBus``.

P1 (W4):
- ``nats``      — JetStream-backed MessageBus.

P2 (W6 placeholders):
- mysql / qdrant / mongodb / neo4j / s3 / oss
"""
