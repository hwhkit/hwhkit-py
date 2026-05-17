"""hwhkit.web — FastAPI integration layer.

Provides:
- ``build_app(ctx, routers, integrations)`` — app factory used by bootstrap.
- ``ApiResponse[T]`` / ``PageResponse[T]`` — unified JSON envelope.
- ``register_exception_handlers(app)`` — maps ApiError/HTTPException/Exception to envelope.
- Standard middlewares: RequestID / Logging / Metrics / Auth.
- ``hwhkit-serve`` CLI: ``run(app, server=granian|uvicorn|gunicorn, ...)``.

See spec § 3.
"""

from hwhkit.web.responses import ApiResponse, PageResponse, raw_response

__all__ = ["ApiResponse", "PageResponse", "raw_response"]
