"""Framework-supplied FastAPI middlewares.

Stack order (from outermost to innermost, executed before/after handler):

1. ``GZipMiddleware``         — FastAPI built-in, compresses response bodies.
2. ``CORSMiddleware``         — FastAPI built-in, configured via WebConfig.cors.
3. ``RequestIDMiddleware``    — ensures every request has X-Request-ID.
4. ``LoggingMiddleware``      — structured access log per request.
5. ``MetricsMiddleware``      — OTel histogram of request duration.
6. ``AuthMiddleware``         — optional JWT verification.

Items 1-2 are configured by ``build_app()`` directly; 3-6 live here.
"""

from hwhkit.web.middleware.logging import LoggingMiddleware
from hwhkit.web.middleware.metrics import MetricsMiddleware
from hwhkit.web.middleware.request_id import REQUEST_ID_HEADER, RequestIDMiddleware

__all__ = [
    "REQUEST_ID_HEADER",
    "LoggingMiddleware",
    "MetricsMiddleware",
    "RequestIDMiddleware",
]
