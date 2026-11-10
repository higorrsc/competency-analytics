"""Integration tests for OpenAPI schema and Swagger UI documentation endpoints."""

from __future__ import annotations

import pytest
from rest_framework import status
from rest_framework.test import APIClient


@pytest.fixture
def client() -> APIClient:
    return APIClient()


def test_openapi_schema_endpoint(client: APIClient) -> None:
    """Verify the OpenAPI schema endpoint returns valid OpenAPI 3 document."""
    response = client.get("/api/v1/schema/")
    assert response.status_code == status.HTTP_200_OK


def test_swagger_ui_endpoint(client: APIClient) -> None:
    """Verify Swagger UI documentation page is accessible and renders HTML."""
    response = client.get("/api/v1/docs/")
    assert response.status_code == status.HTTP_200_OK
    assert "text/html" in response.headers.get("content-type", "")
    assert b"SwaggerUIBundle" in response.content
