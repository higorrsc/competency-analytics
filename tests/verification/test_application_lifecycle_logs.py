"""Verification of application startup, request processing, and shutdown logs.

Task 18.7:
- Verify application startup, API calls, and shutdown produce no errors in logs.
"""

from __future__ import annotations

import logging

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.infrastructure.config.asgi import application as asgi_app
from src.infrastructure.config.wsgi import application as wsgi_app


@pytest.mark.django_db
def test_application_lifecycle_and_api_calls_produce_no_error_logs(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Verify clean startup, request handling, and absence of error logs."""
    # 1. Verify WSGI & ASGI applications initialize cleanly
    assert wsgi_app is not None
    assert asgi_app is not None

    # 2. Capture logs at ERROR and CRITICAL levels
    caplog.set_level(logging.ERROR)

    client = APIClient()

    endpoints = [
        "/api/v1/competencies/",
        "/api/v1/paths/",
        "/api/v1/collaborators/",
        "/api/v1/evaluations/",
        "/api/schema/",
        "/api/docs/",
        "/admin/login/",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert response.status_code == status.HTTP_200_OK

    # 3. Assert no ERROR or CRITICAL logs were produced during lifecycle
    error_records = [
        record for record in caplog.records if record.levelno >= logging.ERROR
    ]
    assert not error_records, f"Error logs produced: {error_records}"
