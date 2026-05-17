# Errors

hwhkit ships a uniform error taxonomy with **6-digit error codes** following
the `XYYZZZ` scheme.

## Code format

```
X    YY   ZZZ
│    │    └── specific error within the module (000-999)
│    └────── module (00=core, 01=auth, 10=postgres, 11=redis, 12=nats,
│                   13=scheduler, 14=llm, 15=web, 20-99 business)
└─────────── class (1=client, 5=server, 9=external, 6-8=business)
```

Examples:

- `100404` — client / core / not-found
- `100401` — client / core / unauthorized
- `510001` — server / postgres / connection-failed
- `512001` — server / nats / connection-failed
- `620001` — business / your-module / e.g. "insufficient balance"

## Built-in errors

| Class | HTTP | Code |
|---|---|---|
| `UnauthorizedError` | 401 | 100401 |
| `ForbiddenError` | 403 | 100403 |
| `NotFoundError` | 404 | 100404 |
| `ConflictError` | 409 | 100409 |
| `ValidationError` | 422 | 100422 |
| `RateLimitError` | 429 | 100429 |
| `InternalError` | 500 | 500000 |
| `IntegrationError` | 503 | 500001 |
| `DbConnectionError` | 503 | 510001 |
| `RedisConnectionError` | 503 | 511001 |
| `NatsConnectionError` | 503 | 512001 |

## Raising

```python
from hwhkit.core.errors import NotFoundError

@router.get("/users/{id}")
async def get_user(id: int) -> User:
    user = await load_user(id)
    if not user:
        raise NotFoundError(f"user {id}")
    return user
```

Framework's exception handler converts to:

```json
{
  "code": 100404,
  "message": "user 42",
  "data": null,
  "trace_id": "..."
}
```

with HTTP status 404.

## Defining business errors

```python
from hwhkit.core.errors import ApiError


class InsufficientBalance(ApiError):
    code = 620001
    http_status = 400
```

Pick `YY` from your business-module range (20-99). Document your map
somewhere in your project so frontend / SDK consumers can decode.

## Unhandled exceptions

Anything that escapes a handler is caught by the catch-all and rendered
as 500 / `code=500000`. **The exception message and traceback are never
returned to the client** — they go to the structured log (with the
request's `trace_id`) for server-side investigation.
