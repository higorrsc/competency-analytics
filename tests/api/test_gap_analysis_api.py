"""Integration tests for Competency Gap Analysis REST API endpoint."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

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
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.fixture
def client() -> APIClient:
    return APIClient()


@pytest.fixture
def gap_setup(
    db: None,
) -> tuple[CollaboratorModel, CompetencyPathModel, PathLevelModel]:
    collab = CollaboratorModel.objects.create(
        name="Engineer One", email="eng1@company.com", department="Eng"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Manager One", email="mgr1@company.com", department="Eng"
    )

    cat = CategoryModel.objects.create(name="Tech")
    group = CompetencyGroupModel.objects.create(name="Dev", category=cat)

    comp_python = CompetencyModel.objects.create(
        name="Python",
        description="Backend",
        category=cat,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )
    comp_docker = CompetencyModel.objects.create(
        name="Docker",
        description="Containers",
        category=cat,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )
    comp_arch = CompetencyModel.objects.create(
        name="Architecture",
        description="System Design",
        category=cat,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    # Career path with Senior level
    path = CompetencyPathModel.objects.create(name="Backend Track", description="Track")
    senior_level = PathLevelModel.objects.create(path=path, name="Senior", order=1)

    # Requirements:
    # 1. Python: min 4, CORE
    # 2. Docker: min 3, IMPORTANT
    # 3. Architecture: min 3, DESIRABLE
    CompetencyRequirementModel.objects.create(
        path_level=senior_level,
        competency=comp_python,
        minimum_level=4,
        weight="CORE",
    )
    CompetencyRequirementModel.objects.create(
        path_level=senior_level,
        competency=comp_docker,
        minimum_level=3,
        weight="IMPORTANT",
    )
    CompetencyRequirementModel.objects.create(
        path_level=senior_level,
        competency=comp_arch,
        minimum_level=3,
        weight="DESIRABLE",
    )

    # Finalized Evaluation:
    # Python: level 3 (gap 1, CORE)
    # Docker: level 3 (gap 0, met)
    # Architecture: not measured (gap 3, full gap, DESIRABLE)
    now = datetime.now(UTC)
    evaluation = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2026.Q1",
        evaluation_date=now,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=evaluation,
        competency=comp_python,
        current_level=3,
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=evaluation,
        competency=comp_docker,
        current_level=3,
    )
    evaluation.status = "ACCEPTED"
    evaluation.submitted_at = now
    evaluation.response_date = now
    evaluation.response_notes = "Finalized"
    evaluation.save()

    return collab, path, senior_level


@pytest.mark.django_db
def test_calculate_competency_gaps_get_request(
    client: APIClient,
    gap_setup: tuple[CollaboratorModel, CompetencyPathModel, PathLevelModel],
) -> None:
    collab, path, level = gap_setup

    url = (
        f"/api/v1/gap-analysis/?collaborator_id={collab.id}"
        f"&path_id={path.id}&level_id={level.id}"
    )
    response = client.get(url)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["collaborator_id"] == str(collab.id)
    assert data["path_id"] == str(path.id)
    assert data["level_id"] == str(level.id)

    # Gaps prioritization: CORE first, then IMPORTANT, then DESIRABLE
    gaps = data["gaps"]
    assert len(gaps) == 3

    # First is CORE (Python, gap 1)
    assert gaps[0]["weight"] == "CORE"
    assert gaps[0]["current_level"] == 3
    assert gaps[0]["required_level"] == 4
    assert gaps[0]["gap"] == 1

    # Docker is met (gap 0)
    docker_gap = next(
        g for g in gaps if g["required_level"] == 3 and g["current_level"] == 3
    )
    assert docker_gap["gap"] == 0

    # Architecture is unmeasured (current_level 0, gap 3)
    arch_gap = next(g for g in gaps if g["weight"] == "DESIRABLE")
    assert arch_gap["current_level"] == 0
    assert arch_gap["gap"] == 3

    # Progression eligibility: Not eligible because CORE Python requirement is unmet
    assert data["eligibility"]["is_eligible"] is False
    assert len(data["eligibility"]["blocking_competency_ids"]) == 1


@pytest.mark.django_db
def test_calculate_competency_gaps_post_request(
    client: APIClient,
    gap_setup: tuple[CollaboratorModel, CompetencyPathModel, PathLevelModel],
) -> None:
    collab, path, level = gap_setup
    payload = {
        "collaborator_id": str(collab.id),
        "path_id": str(path.id),
        "level_id": str(level.id),
    }
    response = client.post("/api/v1/gap-analysis/", payload, format="json")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["collaborator_id"] == str(collab.id)


@pytest.mark.django_db
def test_calculate_gaps_missing_collaborator_returns_not_found(
    client: APIClient,
    gap_setup: tuple[CollaboratorModel, CompetencyPathModel, PathLevelModel],
) -> None:
    _, path, level = gap_setup
    payload = {
        "collaborator_id": str(uuid4()),
        "path_id": str(path.id),
        "level_id": str(level.id),
    }
    response = client.post("/api/v1/gap-analysis/", payload, format="json")
    # No finalized evaluation for this missing collaborator
    assert response.status_code == status.HTTP_404_NOT_FOUND
