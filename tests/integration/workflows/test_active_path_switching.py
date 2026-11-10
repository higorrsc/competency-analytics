"""Integration test for active career path switching.

Task 16.4:
- Enroll in path A → activate → enroll in path B → activate, verify only B active.
"""

from __future__ import annotations

import pytest

from src.application.dto.collaborator import EnrollmentCreateDTO
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel
from src.presentation.dependencies.container import get_container


@pytest.fixture
def two_career_paths(
    db: None,
) -> tuple[CompetencyPathModel, CompetencyPathModel]:
    path_a = CompetencyPathModel.objects.create(
        name="Software Engineer Track", description="Individual Contributor"
    )
    PathLevelModel.objects.create(path=path_a, name="Junior", order=1)
    PathLevelModel.objects.create(path=path_a, name="Senior", order=2)

    path_b = CompetencyPathModel.objects.create(
        name="Tech Lead Track", description="Leadership"
    )
    PathLevelModel.objects.create(path=path_b, name="Associate Lead", order=1)
    PathLevelModel.objects.create(path=path_b, name="Principal Lead", order=2)

    return path_a, path_b


@pytest.mark.django_db
def test_active_path_switching_enforces_single_active_path(
    two_career_paths: tuple[CompetencyPathModel, CompetencyPathModel],
) -> None:
    """Validate that activating a new path deactivates previous and keeps history."""
    path_a, path_b = two_career_paths
    container = get_container()

    collab_model = CollaboratorModel.objects.create(
        name="Lucas Mendes",
        email="lucas@company.com",
        department="Engineering",
    )
    collab_id = CollaboratorId(collab_model.id)

    # 1. Enroll in Path A (becomes active)
    container.enroll_collaborator_in_path_use_case.execute(
        collab_id,
        EnrollmentCreateDTO(path_id=path_a.id, target_level="Junior"),
    )

    # Verify only Path A is active in database
    enrollments_after_a = PathEnrollmentModel.objects.filter(
        collaborator_id=collab_id.value
    )
    assert enrollments_after_a.count() == 1
    assert enrollments_after_a.filter(is_active=True).count() == 1
    assert enrollments_after_a.get(is_active=True).path_id == path_a.id

    # 2. Enroll in Path B (becomes active, Path A must be deactivated)
    container.enroll_collaborator_in_path_use_case.execute(
        collab_id,
        EnrollmentCreateDTO(path_id=path_b.id, target_level="Associate Lead"),
    )

    # Verify database state: both exist, but ONLY Path B is active
    enrollments_after_b = PathEnrollmentModel.objects.filter(
        collaborator_id=collab_id.value
    )
    assert enrollments_after_b.count() == 2
    assert enrollments_after_b.filter(is_active=True).count() == 1
    active_enrollment = enrollments_after_b.get(is_active=True)
    assert active_enrollment.path_id == path_b.id

    inactive_enrollment = enrollments_after_b.get(is_active=False)
    assert inactive_enrollment.path_id == path_a.id

    # 3. Switch back: Activate Path A via use case
    container.activate_collaborator_path_use_case.execute(
        collab_id,
        PathId(path_a.id),
    )

    # Verify database state: ONLY Path A is active again
    enrollments_switched = PathEnrollmentModel.objects.filter(
        collaborator_id=collab_id.value
    )
    assert enrollments_switched.count() == 2
    assert enrollments_switched.filter(is_active=True).count() == 1
    assert enrollments_switched.get(is_active=True).path_id == path_a.id
    assert enrollments_switched.get(is_active=False).path_id == path_b.id
