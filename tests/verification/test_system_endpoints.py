"""System verification test for endpoint accessibility.

Task 18.1:
- Start development server environment and verify all endpoints are accessible.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.mark.django_db
def test_all_api_and_admin_endpoints_accessible() -> None:
    """Verify that all REST API, OpenAPI, and Admin endpoints are accessible."""
    client = APIClient()

    category = CategoryModel.objects.create(name="QA Testing")
    group = CompetencyGroupModel.objects.create(name="Test", category=category)
    competency = CompetencyModel.objects.create(
        name="Test Automation",
        description="E2E testing",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    path = CompetencyPathModel.objects.create(
        name="QA Engineering", description="QA track"
    )
    level = PathLevelModel.objects.create(path=path, name="Junior QA", order=1)
    CompetencyRequirementModel.objects.create(
        path_level=level,
        competency=competency,
        minimum_level=2,
        weight=RequirementWeight.CORE.value,
    )

    collab = CollaboratorModel.objects.create(
        name="System Test", email="test@corp.com", department="QA"
    )
    evaluator = CollaboratorModel.objects.create(
        name="QA Lead", email="qalead@corp.com", department="QA"
    )

    now = datetime.now(UTC)
    ev = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.H1",
        evaluation_date=now,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev, competency=competency, current_level=3
    )
    ev.status = "ACCEPTED"
    ev.submitted_at = now
    ev.response_date = now
    ev.response_notes = "Accepted"
    ev.save()

    endpoints = [
        # REST API resources
        ("/api/v1/competencies/", status.HTTP_200_OK),
        ("/api/v1/paths/", status.HTTP_200_OK),
        ("/api/v1/collaborators/", status.HTTP_200_OK),
        ("/api/v1/evaluations/", status.HTTP_200_OK),
        (
            f"/api/v1/history/?collaborator_id={collab.id}",
            status.HTTP_200_OK,
        ),
        (
            f"/api/v1/progression/?collaborator_id={collab.id}&path_id={path.id}",
            status.HTTP_200_OK,
        ),
        (
            f"/api/v1/gap-analysis/?collaborator_id={collab.id}&path_id={path.id}&level_id={level.id}",
            status.HTTP_200_OK,
        ),
        # OpenAPI schema & documentation consoles (both versioned and top-level)
        ("/api/schema/", status.HTTP_200_OK),
        ("/api/docs/", status.HTTP_200_OK),
        ("/api/v1/schema/", status.HTTP_200_OK),
        ("/api/v1/docs/", status.HTTP_200_OK),
        # Django Admin login
        ("/admin/login/", status.HTTP_200_OK),
    ]

    for endpoint, expected_status in endpoints:
        response = client.get(endpoint)
        assert response.status_code == expected_status, (
            f"Endpoint '{endpoint}' returned {response.status_code}, "
            f"expected {expected_status}"
        )
