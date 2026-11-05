"""Unit tests for the enroll collaborator in path use case."""

import pytest

from src.application.dto.collaborator_dtos import EnrollmentCreateDTO
from src.application.use_cases.collaborator_use_cases import (
    EnrollCollaboratorInPathUseCase,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.domain.entities.collaborator import Collaborator
from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.path_level import PathLevel
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.path_id import PathId
from tests.unit.application.use_cases.fakes import (
    FakeCollaboratorRepository,
    FakePathRepository,
)


def make_collaborator() -> Collaborator:
    """Build a valid collaborator aggregate for tests."""
    return Collaborator(
        id=CollaboratorId.generate(),
        name="João Silva",
        email="joao.silva@company.com",
        department="Engineering",
    )


def make_path(*levels: str) -> CompetencyPath:
    """Build a valid career path with the given ordered level names."""
    path = CompetencyPath(
        id=PathId.generate(),
        name="Software Engineer Track",
        description="Progression",
    )
    for position, name in enumerate(levels, start=1):
        path.add_level(PathLevel(id=LevelId.generate(), name=name, order=position))
    return path


class TestEnrollCollaboratorInPathUseCase:
    """Test orchestration of EnrollCollaboratorInPathUseCase."""

    def test_should_enroll_and_activate_the_path(self) -> None:
        """Enrollment adds an active entry to the collaborator history."""
        path = make_path("Junior", "Senior")
        path_repository = FakePathRepository()
        path_repository.save(path)
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = EnrollCollaboratorInPathUseCase(
            collaborator_repository, path_repository
        )

        response = use_case.execute(
            collaborator.id,
            EnrollmentCreateDTO(path_id=path.id.value, target_level="Senior"),
        )

        assert len(response.enrollments) == 1
        enrollment = response.enrollments[0]
        assert enrollment.path_id == path.id.value
        assert enrollment.target_level == "Senior"
        assert enrollment.is_active is True

    def test_should_canonicalize_target_level_casing(self) -> None:
        """The target level is stored with the canonical path level name."""
        path = make_path("Junior", "Senior")
        path_repository = FakePathRepository()
        path_repository.save(path)
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = EnrollCollaboratorInPathUseCase(
            collaborator_repository, path_repository
        )

        response = use_case.execute(
            collaborator.id,
            EnrollmentCreateDTO(path_id=path.id.value, target_level="senior"),
        )

        assert response.enrollments[0].target_level == "Senior"

    def test_should_deactivate_previous_active_path(self) -> None:
        """Enrolling in a second path switches the single active path."""
        first = make_path("Junior")
        second = make_path("Junior")
        path_repository = FakePathRepository()
        path_repository.save(first)
        path_repository.save(second)
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = EnrollCollaboratorInPathUseCase(
            collaborator_repository, path_repository
        )
        use_case.execute(
            collaborator.id,
            EnrollmentCreateDTO(path_id=first.id.value, target_level="Junior"),
        )

        response = use_case.execute(
            collaborator.id,
            EnrollmentCreateDTO(path_id=second.id.value, target_level="Junior"),
        )

        active = [
            enrollment for enrollment in response.enrollments if enrollment.is_active
        ]
        inactive = [
            enrollment
            for enrollment in response.enrollments
            if not enrollment.is_active
        ]
        assert len(active) == 1
        assert active[0].path_id == second.id.value
        assert len(inactive) == 1
        assert inactive[0].path_id == first.id.value

    def test_should_reject_unknown_collaborator(self) -> None:
        """Enrollment requires an existing collaborator."""
        use_case = EnrollCollaboratorInPathUseCase(
            FakeCollaboratorRepository(), FakePathRepository()
        )

        with pytest.raises(NotFoundError, match="Collaborator"):
            use_case.execute(
                CollaboratorId.generate(),
                EnrollmentCreateDTO(
                    path_id=PathId.generate().value, target_level="Junior"
                ),
            )

    def test_should_reject_unknown_path(self) -> None:
        """Enrollment requires an existing path."""
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = EnrollCollaboratorInPathUseCase(
            collaborator_repository, FakePathRepository()
        )

        with pytest.raises(NotFoundError, match="Path"):
            use_case.execute(
                collaborator.id,
                EnrollmentCreateDTO(
                    path_id=PathId.generate().value, target_level="Junior"
                ),
            )

    def test_should_reject_target_level_not_defined_in_path(self) -> None:
        """The target level must exist in the enrolled path."""
        path = make_path("Junior")
        path_repository = FakePathRepository()
        path_repository.save(path)
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = EnrollCollaboratorInPathUseCase(
            collaborator_repository, path_repository
        )

        with pytest.raises(ValidationError, match="is not defined in path"):
            use_case.execute(
                collaborator.id,
                EnrollmentCreateDTO(path_id=path.id.value, target_level="Architect"),
            )

    def test_should_reject_re_enrollment_in_same_path(self) -> None:
        """Re-enrolling in a path the collaborator already enrolled in fails."""
        path = make_path("Junior")
        path_repository = FakePathRepository()
        path_repository.save(path)
        collaborator_repository = FakeCollaboratorRepository()
        collaborator = make_collaborator()
        collaborator_repository.save(collaborator)
        use_case = EnrollCollaboratorInPathUseCase(
            collaborator_repository, path_repository
        )
        use_case.execute(
            collaborator.id,
            EnrollmentCreateDTO(path_id=path.id.value, target_level="Junior"),
        )

        with pytest.raises(ConflictError, match="already enrolled"):
            use_case.execute(
                collaborator.id,
                EnrollmentCreateDTO(path_id=path.id.value, target_level="Junior"),
            )
