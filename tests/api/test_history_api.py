"""Integration tests for CQRS read models API endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from rest_framework import status
from rest_framework.test import APIClient

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
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def history_setup(
    db: None,
) -> tuple[CollaboratorModel, CompetencyModel, CompetencyPathModel]:
    collab = CollaboratorModel.objects.create(
        name="History Tester", email="hist@company.com", department="Eng"
    )
    evaluator = CollaboratorModel.objects.create(
        name="History Evaluator", email="eval@company.com", department="Eng"
    )

    cat = CategoryModel.objects.create(name="Tech")
    group = CompetencyGroupModel.objects.create(name="Dev", category=cat)
    comp = CompetencyModel.objects.create(
        name="Python",
        description="Backend",
        category=cat,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    path = CompetencyPathModel.objects.create(name="Backend Track", description="Track")
    level = PathLevelModel.objects.create(path=path, name="Mid", order=1)
    CompetencyRequirementModel.objects.create(
        path_level=level, competency=comp, minimum_level=3, weight="CORE"
    )

    base_time = datetime(2025, 1, 1, 10, 0, 0, tzinfo=UTC)

    PathEnrollmentModel.objects.create(
        collaborator=collab,
        path=path,
        target_level="Mid",
        is_active=True,
        enrolled_at=base_time,
    )

    # Eval 1 (2025.Q1): level 2
    ev1 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.Q1",
        evaluation_date=base_time,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev1, competency=comp, current_level=2
    )
    ev1.status = "ACCEPTED"
    ev1.submitted_at = base_time
    ev1.response_date = base_time
    ev1.response_notes = "OK"
    ev1.save()

    # Eval 2 (2026.Q1): level 4 (+2 change)
    eval2_time = base_time + timedelta(days=365)
    ev2 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2026.Q1",
        evaluation_date=eval2_time,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev2, competency=comp, current_level=4
    )
    ev2.status = "ACCEPTED"
    ev2.submitted_at = eval2_time
    ev2.response_date = eval2_time
    ev2.response_notes = "Great progress"
    ev2.save()

    return collab, comp, path


@pytest.mark.django_db
def test_competency_history_query(
    client: APIClient,
    history_setup: tuple[CollaboratorModel, CompetencyModel, CompetencyPathModel],
) -> None:
    collab, comp, _ = history_setup

    res = client.get(
        f"/api/v1/history/?collaborator_id={collab.id}&competency_id={comp.id}"
    )
    assert res.status_code == status.HTTP_200_OK
    entries = res.json()
    assert len(entries) == 2

    # First entry (2025.Q1): level 2, no previous level
    assert entries[0]["period"] == "2025.Q1"
    assert entries[0]["current_level"] == 2
    assert entries[0]["previous_level"] is None
    assert entries[0]["level_change"] is None

    # Second entry (2026.Q1): level 4, previous 2, change +2
    assert entries[1]["period"] == "2026.Q1"
    assert entries[1]["current_level"] == 4
    assert entries[1]["previous_level"] == 2
    assert entries[1]["level_change"] == 2


@pytest.mark.django_db
def test_competency_history_requires_collaborator_id(
    client: APIClient,
) -> None:
    res = client.get("/api/v1/history/")
    assert res.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_path_progression_query(
    client: APIClient,
    history_setup: tuple[CollaboratorModel, CompetencyModel, CompetencyPathModel],
) -> None:
    collab, _, path = history_setup

    res = client.get(
        f"/api/v1/progression/?collaborator_id={collab.id}&path_id={path.id}"
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert data["collaborator_id"] == str(collab.id)
    assert data["path_id"] == str(path.id)
    assert data["target_level"] == "Mid"
    assert data["total_requirements"] == 1
    assert data["requirements_met"] == 1
    assert data["completion_percentage"] == 100.0
