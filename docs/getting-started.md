# Getting started

!!! warning "0.4.x alpha"
    This page describes the target experience post-1.0. As of W1, only the foundation is in place; integrations land in W3+.

## Install

```bash
pip install hwhkit[web,postgres,redis,otel]
```

## Create a project

```bash
hwhkit init my-service
cd my-service
hwhkit add postgres redis
make dev
```

Your service is at <http://127.0.0.1:8000>.

## Next steps

- Concepts — how hwhkit thinks about apps (coming W2)
- Integrations — postgres, redis, NATS, ... (coming W3+)
- Recipes — real-world patterns (coming W5+)
