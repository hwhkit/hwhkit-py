"""Exception handlers — map ApiError / HTTPException / Exception → ApiResponse envelope.

Per spec § 3.3 handler priority:
1. ``ApiError``           → status from class.http_status + ApiResponse.code from class.code
2. ``RequestValidationError`` (FastAPI/Pydantic) → 422 + ``code=100422``
3. ``HTTPException`` (FastAPI / Starlette native) → wrap in envelope
4. ``Exception`` (catch-all) → 500 + ``code=500000`` + log full traceback,
   **never** leak traceback to client
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from hwhkit.core.errors import ApiError
from hwhkit.web.responses import ApiResponse

if TYPE_CHECKING:
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse

_logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    """Register the four-tier exception handler stack on a FastAPI app.

    Idempotent: re-registering replaces previous handlers.
    """
    from fastapi import HTTPException
    from fastapi.exceptions import RequestValidationError

    app.add_exception_handler(ApiError, _api_error_handler)
    app.add_exception_handler(RequestValidationError, _validation_error_handler)
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(Exception, _catchall_handler)


async def _api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle ``ApiError`` subclasses (recognized framework errors)."""
    from fastapi.responses import JSONResponse

    assert isinstance(exc, ApiError)
    payload: ApiResponse[Any] = ApiResponse(
        code=exc.code,
        message=exc.message,
        data=exc.details or None,
    )
    return JSONResponse(
        status_code=exc.http_status,
        content=_dump(payload),
    )


async def _validation_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI/Pydantic ``RequestValidationError``."""
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    assert isinstance(exc, RequestValidationError)
    payload: ApiResponse[Any] = ApiResponse(
        code=100422,
        message="validation failed",
        data={"errors": exc.errors()},
    )
    return JSONResponse(status_code=422, content=_dump(payload))


async def _http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle FastAPI/Starlette native ``HTTPException`` — wrap in envelope."""
    from fastapi import HTTPException
    from fastapi.responses import JSONResponse

    assert isinstance(exc, HTTPException)
    # Best-effort code mapping: derive a 6-digit code from status_code
    code = _derive_code_from_status(exc.status_code)
    payload: ApiResponse[Any] = ApiResponse(
        code=code,
        message=str(exc.detail) if exc.detail else "error",
    )
    return JSONResponse(status_code=exc.status_code, content=_dump(payload))


async def _catchall_handler(request: Request, exc: Exception) -> JSONResponse:
    """Last-resort handler — log traceback server-side, hide details from client."""
    from fastapi.responses import JSONResponse

    _logger.exception(
        "Unhandled exception in request",
        extra={"path": str(request.url), "method": request.method},
    )
    payload: ApiResponse[Any] = ApiResponse(
        code=500000,
        message="internal server error",
    )
    return JSONResponse(status_code=500, content=_dump(payload))


def _dump(payload: ApiResponse[Any]) -> dict[str, Any]:
    """Serialize ApiResponse to dict suitable for JSONResponse."""
    return payload.model_dump(mode="json")


def _derive_code_from_status(status: int) -> int:
    """Map HTTP status code to a 6-digit business code under the core ('00') module.

    1xxxxx for 4xx; 5xxxxx for 5xx.
    """
    if 400 <= status < 500:
        return 100_000 + status
    if 500 <= status < 600:
        return 500_000 + (status - 500) * 1000
    return 500000


__all__ = ["register_exception_handlers"]
