# hwhkit

> Production-ready Python framework for trading services and microservices.

`hwhkit` is the Python sibling of [hwhkit-rs](https://github.com/louishwh/hwhkit-rs) — same architectural philosophy, idiomatic for each language.

**Status**: 🚧 0.4.x alpha — under active rewrite to 1.0. See [design doc](docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md).

## Philosophy

- **Framework stays invariant, business code lives in your project.**
- **Contracts (ports) + Adapters (integrations)** for swappable infrastructure.
- **OpenTelemetry-native** observability, off by default.
- **Industrial-grade testing**: unit, integration, e2e, benchmark, chaos, security.

## Quick start

```bash
pip install hwhkit[web,postgres,redis,otel]
hwhkit init my-service && cd my-service
hwhkit add postgres redis
make dev
```

See [hwhkit.louishwh.tech](https://hwhkit.louishwh.tech) for full docs.

## License

`MIT OR Apache-2.0` — choose either. Aligned with hwhkit-rs.
