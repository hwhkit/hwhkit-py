# Integrations

| Status | Module | Contract(s) | Extra |
|---|---|---|---|
| ✅ P0 | [Postgres](postgres.md) | `RelationalDb` | `[postgres]` |
| ✅ P0 | [Redis](redis.md) | `Cache`, `KvStore`, `DistributedLock`, `MessageBus` | `[redis]` |
| ✅ P0 | [Scheduler](scheduler.md) | `Scheduler` | `[scheduler]` |
| ✅ P1 | [NATS](nats.md) | `MessageBus` (JetStream durable) | `[nats]` |
| ✅ P1 | [LLM](llm.md) | `LlmClient`, `EmbeddingClient` (via litellm) | `[llm]` |
| 🟡 P2 placeholder | MySQL | `RelationalDb` | `[mysql]` |
| 🟡 P2 placeholder | Qdrant | `VectorStore` | `[qdrant]` |
| 🟡 P2 placeholder | MongoDB | `DocumentDb` | `[mongodb]` |
| 🟡 P2 placeholder | Neo4j | `GraphDb` | `[neo4j]` |
| 🟡 P2 placeholder | S3 | `ObjectStore` | `[s3]` |
| 🟡 P2 placeholder | Aliyun OSS | `ObjectStore` | `[oss]` |

P2 placeholders ship as importable classes that raise `NotImplementedError`
on `setup()`. They reserve the API surface so future concrete impls land
without breaking imports.

## Adding an integration to your project

```bash
hwhkit add postgres
```

That command:

1. Adds the extra to your `pyproject.toml` (e.g. `hwhkit[postgres,...]`)
2. Inserts `from hwhkit.integrations.postgres import PostgresProvider`
   into your `main.py`
3. Appends `PostgresProvider()` to the `integrations=[...]` arg of `bootstrap(...)`
4. Adds a section to `.env.example` for the required environment variables

Idempotent: re-running is a no-op. Use `--dry-run` to preview changes.

See each adapter page below for configuration and usage details.
