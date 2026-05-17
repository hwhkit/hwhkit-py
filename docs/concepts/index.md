# Concepts

hwhkit is built around four ideas. Read them in order — each one builds on
the previous.

1. [**Bootstrap**](bootstrap.md) — one function call wires the whole framework
   and returns a runnable FastAPI app.
2. [**IntegrationProvider**](integration-provider.md) — the lifecycle-managed
   plugin abstraction. Every connection (Postgres / Redis / NATS / …) is one.
3. [**Contracts & Adapters**](contracts.md) — business code talks to interfaces;
   adapters fulfill them. Swap Redis → Memcached, NATS → Kafka without touching
   business code.
4. [**AppContext**](app-context.md) — runtime container; how business code
   reaches integrations.

After those:

- [**Errors**](errors.md) — the 6-digit error code taxonomy and how to extend it
- [**Observability**](observability.md) — OpenTelemetry-native, opt-in
- [**Configuration**](configuration.md) — pydantic-settings, layered sources
- [**Testing**](testing.md) — fakes, contract conformance, pyramid
