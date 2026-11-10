"""DRF custom exception handling translating application errors to HTTP status codes."""

from __future__ import annotations

from typing import Any

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler

from src.application.use_cases.errors import (
    ApplicationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)


def api_exception_handler(exc: Exception, context: dict[str, Any]) -> Response | None:
    """
    Map domain and application errors into standard REST API responses.

    Mappings:
    - `NotFoundError` -> HTTP 404 Not Found
    - `ConflictError` -> HTTP 409 Conflict
    - `ValidationError` -> HTTP 400 Bad Request
    - Other exceptions are delegated to DRF's standard handler.

    Args:
        exc: Raised exception.
        context: Context dictionary passed by DRF.

    Returns:
        A Response object or None if unhandled.
    """
    if isinstance(exc, NotFoundError):
        return Response(
            {"detail": str(exc), "code": "not_found", "entity": exc.entity},
            status=status.HTTP_404_NOT_FOUND,
        )

    if isinstance(exc, ConflictError):
        return Response(
            {"detail": str(exc), "code": "conflict"},
            status=status.HTTP_409_CONFLICT,
        )

    if isinstance(exc, ValidationError):
        return Response(
            {"detail": str(exc), "code": "validation_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if isinstance(exc, ApplicationError):
        return Response(
            {"detail": str(exc), "code": "application_error"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    response: Response | None = drf_exception_handler(exc, context)
    return response
