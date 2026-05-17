# Recipes

Real-world patterns you'll hit building services on hwhkit.

- [**Trading service skeleton**](trading-service.md) — typical layout for a
  service that talks to Postgres + Redis + NATS + Scheduler
- **Event-driven microservice** *(coming soon)* — NATS consumer with
  durable subscriptions, retries, and DLQ
- **Scheduled aggregation jobs** *(coming soon)* — `@scheduled_task`
  with distributed lock to safely run across N replicas
- **AI agent service** *(coming soon)* — `LlmProvider` + tool-calling
  loop + vector store (P2 when Qdrant lands)

If you have a pattern that should live here, open a PR against
`docs/recipes/`.
