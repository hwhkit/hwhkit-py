# Contributing

```bash
git clone https://github.com/hwhkit/hwhkit-py.git
cd hwhkit-py
make dev          # uv sync + pre-commit install
make test         # unit tests
make lint         # ruff
make typecheck    # mypy --strict
make docs-serve   # local docs at :8000
```

See the [design doc](https://github.com/hwhkit/hwhkit-py/blob/main/docs/superpowers/specs/2026-05-16-hwhkit-py-production-readiness-design.md) for architectural decisions.
