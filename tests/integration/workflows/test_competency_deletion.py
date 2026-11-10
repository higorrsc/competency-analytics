"""Integration test for preventing deletion of referenced competencies.

Task 16.7:
- Competency used in path -> attempt delete, verify rejection with reference error.
- Competency used in evaluation -> attempt delete, verify rejection.
- Unreferenced competency -> delete succeeds.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.application.use_cases.errors import ConflictError, NotFoundError
from src.domain.exceptions.competency_errors import CompetencyReferencedError
from src.domain.value_objects.competency_id import CompetencyId
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
from src.presentation.dependencies.container import get_container


@pytest.fixture
def catalog_setup(
    db: None,
) -> tuple[CategoryModel, CompetencyGroupModel, CompetencyModel]:
    category = CategoryModel.objects.create(name="Engineering")
    group = CompetencyGroupModel.objects.create(name="Backend", category=category)
    competency = CompetencyModel.objects.create(
        name="Python Programming",
        description="Python development skills",
        category=category,
        group=group,
        level_descriptions={str(i): f"Level {i}" for i in range(1, 6)},
    )
    return category, group, competency


@pytest.mark.django_db
def test_cannot_delete_competency_referenced_in_career_path(
    catalog_setup: tuple[CategoryModel, CompetencyGroupModel, CompetencyModel],
) -> None:
    """Deleting a competency referenced by a path requirement must fail."""
    _, _, competency = catalog_setup
    container = get_container()

    # Create path, level and attach competency requirement
    path = CompetencyPathModel.objects.create(
        name="Backend Engineer", description="Backend track"
    )
    level = PathLevelModel.objects.create(path=path, name="Junior", order=1)
    CompetencyRequirementModel.objects.create(
        path_level=level,
        competency=competency,
        minimum_level=2,
        weight="MANDATORY",
    )

    # Repository level check
    with pytest.raises(CompetencyReferencedError) as exc_info:
        container.competency_repository.delete(CompetencyId(competency.id))
    assert "career paths" in str(exc_info.value)

    # Use case level check
    with pytest.raises(ConflictError) as exc_info:
        container.delete_competency_use_case.execute(CompetencyId(competency.id))
    assert "referenced" in str(exc_info.value)

    # Competency must still exist in database
    assert CompetencyModel.objects.filter(id=competency.id).exists()


@pytest.mark.django_db
def test_cannot_delete_competency_referenced_in_evaluation(
    catalog_setup: tuple[CategoryModel, CompetencyGroupModel, CompetencyModel],
) -> None:
    """Deleting a competency referenced by an evaluation measurement must fail."""
    _, _, competency = catalog_setup
    container = get_container()

    collab = CollaboratorModel.objects.create(
        name="Alice Doe", email="alice@corp.com", department="Tech"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Bob Manager", email="bob@corp.com", department="Tech"
    )

    evaluation = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.H1",
        evaluation_date=datetime.now(UTC),
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=evaluation, competency=competency, current_level=3
    )

    # Repository level check
    with pytest.raises(CompetencyReferencedError) as exc_info:
        container.competency_repository.delete(CompetencyId(competency.id))
    assert "evaluations" in str(exc_info.value)

    # Use case level check
    with pytest.raises(ConflictError) as exc_info:
        container.delete_competency_use_case.execute(CompetencyId(competency.id))
    assert "referenced" in str(exc_info.value)

    # Competency must still exist in database
    assert CompetencyModel.objects.filter(id=competency.id).exists()


@pytest.mark.django_db
def test_delete_unreferenced_competency_succeeds(
    catalog_setup: tuple[CategoryModel, CompetencyGroupModel, CompetencyModel],
) -> None:
    """Deleting an unreferenced competency must succeed."""
    _, _, competency = catalog_setup
    container = get_container()

    container.delete_competency_use_case.execute(CompetencyId(competency.id))

    # Must be deleted from database
    assert not CompetencyModel.objects.filter(id=competency.id).exists()

    # Subsequent deletion must raise NotFoundError
    with pytest.raises(NotFoundError):
        container.delete_competency_use_case.execute(CompetencyId(competency.id))


@pytest.mark.django_db
def test_api_delete_referenced_competency_returns_409(
    catalog_setup: tuple[CategoryModel, CompetencyGroupModel, CompetencyModel],
) -> None:
    """API endpoint returns 409 Conflict when deleting referenced competency."""
    _, _, competency = catalog_setup
    client = APIClient()

    path = CompetencyPathModel.objects.create(
        name="DevOps Path", description="Infra track"
    )
    level = PathLevelModel.objects.create(path=path, name="Associate", order=1)
    CompetencyRequirementModel.objects.create(
        path_level=level,
        competency=competency,
        minimum_level=1,
        weight="MANDATORY",
    )

    response = client.delete(f"/api/v1/competencies/{competency.id}/")
    assert response.status_code == status.HTTP_409_CONFLICT
    assert CompetencyModel.objects.filter(id=competency.id).exists()
