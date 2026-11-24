"""
Correlation ID and Error Handling Middleware.
Injects unique correlation IDs into every request/response and formats structured errors.
"""
from datetime import datetime, timezone
import logging
from typing import Any, Dict, Optional
import uuid

from fastapi import FastAPI, HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.domain.exceptions import (
    ClinicalWritebackBlockedError,
    ConcurrencyVersionError,
    ImmutableReportOverrideError,
    InvalidStateTransitionError,
    UnauthorizedSignoffError,
)

logger = logging.getLogger("sims_radiology.api.middleware")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """Ensures every incoming request has an X-Correlation-Id header."""

    async def dispatch(self, request: Request, call_next) -> Response:
        correlation_id = request.headers.get("X-Correlation-Id") or f"corr-{uuid.uuid4().hex[:12]}"
        request.state.correlation_id = correlation_id

        response: Response = await call_next(request)
        response.headers["X-Correlation-Id"] = correlation_id
        return response


def register_error_handlers(app: FastAPI) -> None:
    """Register uniform structured error handlers on the FastAPI application."""

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "detail": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={"X-Correlation-Id": correlation_id},
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": exc.errors(),
                "error_code": "VALIDATION_ERROR",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={"X-Correlation-Id": correlation_id},
        )

    @app.exception_handler(UnauthorizedSignoffError)
    async def unauthorized_signoff_handler(request: Request, exc: UnauthorizedSignoffError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={
                "detail": str(exc),
                "error_code": "UNAUTHORIZED_SIGNOFF",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={"X-Correlation-Id": correlation_id},
        )

    @app.exception_handler(ClinicalWritebackBlockedError)
    async def writeback_blocked_handler(request: Request, exc: ClinicalWritebackBlockedError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={
                "detail": str(exc),
                "error_code": "CLINICAL_WRITEBACK_BLOCKED",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={"X-Correlation-Id": correlation_id},
        )

    @app.exception_handler(InvalidStateTransitionError)
    async def invalid_transition_handler(request: Request, exc: InvalidStateTransitionError) -> JSONResponse:
        correlation_id = getattr(request.state, "correlation_id", "unknown")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "detail": str(exc),
                "error_code": "INVALID_STATE_TRANSITION",
                "correlation_id": correlation_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            headers={"X-Correlation-Id": correlation_id},
        )
