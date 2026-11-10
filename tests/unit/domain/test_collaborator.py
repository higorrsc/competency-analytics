"""Unit tests for the Collaborator aggregate root."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.collaborator import Collaborator
from src.domain.exceptions.collaborator_errors import (
    CollaboratorValidationError,
    EnrollmentNotFoundError,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.path_id import PathId

ENROLLED_AT = datetime(2026, 1, 15, 10, 30, tzinfo=UTC)


def make_enrollment(
    *,
    path_id: PathId | None = None,
    target_level: str = "Senior",
    enrolled_at: datetime = ENROLLED_AT,
    is_active: bool = False,
) -> PathEnrollment:
    """Build a valid PathEnrollment for use in tests."""
    return PathEnrollment(
        path_id=path_id or PathId.generate(),
        target_level=target_level,
        enrolled_at=enrolled_at,
        is_active=is_active,
    )


def make_collaborator(
    *,
    collaborator_id: CollaboratorId | None = None,
    name: str = "João Silva",
    email: str = "joao.silva@company.com",
    department: str = "Engineering",
    enrollments: list[PathEnrollment] | None = None,
) -> Collaborator:
    """Build a valid Collaborator for use in tests."""
    return Collaborator(
        id=collaborator_id or CollaboratorId.generate(),
        name=name,
        email=email,
        department=department,
        enrollments=enrollments if enrollments is not None else [],
    )


class TestCollaboratorCreation:
    """Test creation and validation invariants of Collaborator."""

    def test_should_create_collaborator_when_data_is_valid(self) -> None:
        """A valid collaborator keeps all of its data."""
        collaborator_id = CollaboratorId.generate()
        enrollment = make_enrollment()

        collaborator = make_collaborator(
            collaborator_id=collaborator_id,
            enrollments=[enrollment],
        )

        assert collaborator.id == collaborator_id
        assert collaborator.name == "João Silva"
        assert collaborator.email == "joao.silva@company.com"
        assert collaborator.department == "Engineering"
        assert collaborator.enrollments == [enrollment]

    def test_should_create_collaborator_without_enrollments(self) -> None:
        """A collaborator may start without any enrollment."""
        collaborator = make_collaborator(enrollments=[])

        assert collaborator.enrollments == []

    def test_should_trim_text_fields(self) -> None:
        """Surrounding whitespace is removed from text fields."""
        collaborator = make_collaborator(
            name="  João Silva  ",
            email="  joao.silva@company.com  ",
            department="  Engineering  ",
        )

        assert collaborator.name == "João Silva"
        assert collaborator.email == "joao.silva@company.com"
        assert collaborator.department == "Engineering"

    def test_should_reject_non_collaborator_id(self) -> None:
        """The identity must be a CollaboratorId."""
        with pytest.raises(
            CollaboratorValidationError,
            match="id must be a CollaboratorId",
        ):
            make_collaborator(collaborator_id="collaborator-1")  # type: ignore[arg-type]

    def test_should_reject_blank_name(self) -> None:
        """A blank name violates the invariant."""
        with pytest.raises(
            CollaboratorValidationError,
            match="name must not be empty",
        ):
            make_collaborator(name="   ")

    def test_should_reject_blank_email(self) -> None:
        """A blank email violates the invariant."""
        with pytest.raises(
            CollaboratorValidationError,
            match="email must not be empty",
        ):
            make_collaborator(email="   ")

    @pytest.mark.parametrize(
        "email",
        [
            "not-an-email",
            "joao@company",
            "@company.com",
            "joao silva@company.com",
            "joao@@company.com",
        ],
    )
    def test_should_reject_malformed_email(self, email: str) -> None:
        """Malformed emails are rejected."""
        with pytest.raises(
            CollaboratorValidationError,
            match="is not valid",
        ):
            make_collaborator(email=email)

    def test_should_reject_blank_department(self) -> None:
        """A blank department violates the invariant."""
        with pytest.raises(
            CollaboratorValidationError,
            match="department must not be empty",
        ):
            make_collaborator(department="   ")

    def test_should_reject_non_list_enrollments(self) -> None:
        """Enrollments must be provided as a list."""
        with pytest.raises(
            CollaboratorValidationError,
            match="enrollments must be a list",
        ):
            make_collaborator(enrollments="not-a-list")  # type: ignore[arg-type]

    def test_should_reject_non_enrollment_items(self) -> None:
        """Every enrollment item must be a PathEnrollment."""
        with pytest.raises(
            CollaboratorValidationError,
            match="must be PathEnrollment instances",
        ):
            make_collaborator(enrollments=["Senior"])  # type: ignore[list-item]

    def test_should_reject_duplicate_path_enrollments_at_construction(self) -> None:
        """A collaborator cannot be enrolled twice in the same path."""
        path_id = PathId.generate()

        with pytest.raises(
            CollaboratorValidationError,
            match="already enrolled in path",
        ):
            make_collaborator(
                enrollments=[
                    make_enrollment(path_id=path_id),
                    make_enrollment(path_id=path_id),
                ]
            )

    def test_should_reject_multiple_active_enrollments_at_construction(self) -> None:
        """At most one enrollment may be active."""
        with pytest.raises(
            CollaboratorValidationError,
            match="more than one active path enrollment",
        ):
            make_collaborator(
                enrollments=[
                    make_enrollment(is_active=True),
                    make_enrollment(is_active=True),
                ]
            )

    def test_should_accept_a_single_active_enrollment(self) -> None:
        """A collaborator may have one active path."""
        enrollment = make_enrollment(is_active=True)

        collaborator = make_collaborator(enrollments=[enrollment])

        assert collaborator.active_enrollment() == enrollment


class TestCollaboratorEnrollmentManagement:
    """Test enrollment creation, lookup, and active path switching."""

    def test_should_enroll_creating_an_inactive_enrollment(self) -> None:
        """New enrollments are inactive and returned to the caller."""
        collaborator = make_collaborator()
        path_id = PathId.generate()

        enrollment = collaborator.enroll(
            path_id=path_id,
            target_level="Senior",
            enrolled_at=ENROLLED_AT,
        )

        assert enrollment.path_id == path_id
        assert enrollment.target_level == "Senior"
        assert enrollment.enrolled_at == ENROLLED_AT
        assert enrollment.is_active is False
        assert collaborator.enrollments == [enrollment]

    def test_should_default_enrollment_date_to_now(self) -> None:
        """When no date is given the current UTC time is used."""
        collaborator = make_collaborator()

        enrollment = collaborator.enroll(
            path_id=PathId.generate(),
            target_level="Senior",
        )

        assert isinstance(enrollment.enrolled_at, datetime)
        assert enrollment.enrolled_at.tzinfo is UTC

    def test_should_reject_duplicate_enrollment(self) -> None:
        """Enrolling twice in the same path is rejected."""
        path_id = PathId.generate()
        collaborator = make_collaborator(enrollments=[make_enrollment(path_id=path_id)])

        with pytest.raises(
            CollaboratorValidationError,
            match="already enrolled in path",
        ):
            collaborator.enroll(path_id=path_id, target_level="Senior")

    def test_should_reject_duplicate_add_enrollment(self) -> None:
        """Adding an enrollment for an existing path is rejected."""
        path_id = PathId.generate()
        collaborator = make_collaborator(enrollments=[make_enrollment(path_id=path_id)])

        with pytest.raises(
            CollaboratorValidationError,
            match="already enrolled in path",
        ):
            collaborator.add_enrollment(make_enrollment(path_id=path_id))

    def test_should_deactivate_previous_active_on_active_add(self) -> None:
        """Adding an active enrollment keeps the single-active invariant."""
        first = make_enrollment(is_active=True)
        second = make_enrollment(is_active=True)
        collaborator = make_collaborator(enrollments=[first])

        collaborator.add_enrollment(second)

        assert collaborator.enrollments[0].is_active is False
        assert collaborator.enrollments[1].is_active is True
        assert collaborator.active_enrollment() == second

    def test_should_switch_active_path_preserving_history(self) -> None:
        """Activating a path deactivates the previous one but keeps it."""
        first = make_enrollment(target_level="Senior")
        second = make_enrollment(target_level="Lead")
        collaborator = make_collaborator(enrollments=[first, second])
        collaborator.set_active_path(first.path_id)

        activated = collaborator.set_active_path(second.path_id)

        assert activated == second.activate()
        assert collaborator.enrollments[0].is_active is False
        assert collaborator.enrollments[1].is_active is True
        assert len(collaborator.enrollments) == 2

    def test_should_keep_active_path_when_activating_it_again(self) -> None:
        """Re-activating the current path is idempotent."""
        enrollment = make_enrollment()
        collaborator = make_collaborator(enrollments=[enrollment])
        collaborator.set_active_path(enrollment.path_id)

        collaborator.set_active_path(enrollment.path_id)

        active = collaborator.active_enrollment()
        assert active is not None
        assert active.path_id == enrollment.path_id

    def test_should_raise_when_activating_unknown_path(self) -> None:
        """Activating a path the collaborator is not enrolled in fails."""
        collaborator = make_collaborator()
        path_id = PathId.generate()

        with pytest.raises(EnrollmentNotFoundError) as error:
            collaborator.set_active_path(path_id)

        assert error.value.path_id == path_id

    def test_should_return_none_when_no_path_is_active(self) -> None:
        """A collaborator without active enrollment has no active path."""
        collaborator = make_collaborator(enrollments=[make_enrollment(is_active=False)])

        assert collaborator.active_enrollment() is None

    def test_should_find_existing_enrollment(self) -> None:
        """An enrollment can be looked up by path."""
        enrollment = make_enrollment()
        collaborator = make_collaborator(enrollments=[enrollment])

        assert collaborator.find_enrollment(enrollment.path_id) == enrollment

    def test_should_return_none_for_missing_enrollment(self) -> None:
        """An unknown path yields no enrollment."""
        collaborator = make_collaborator()

        assert collaborator.find_enrollment(PathId.generate()) is None


class TestCollaboratorTargetLevel:
    """Test target level updates on existing enrollments."""

    def test_should_update_target_level_preserving_history(self) -> None:
        """Changing the target keeps date and active status."""
        enrollment = make_enrollment(target_level="Mid", is_active=True)
        collaborator = make_collaborator(enrollments=[enrollment])

        updated = collaborator.update_target_level(
            enrollment.path_id,
            "Senior",
            available_levels=["Junior", "Mid", "Senior"],
        )

        assert updated.target_level == "Senior"
        assert updated.enrolled_at == enrollment.enrolled_at
        assert updated.is_active is True
        assert len(collaborator.enrollments) == 1

    def test_should_match_target_level_ignoring_case_and_whitespace(self) -> None:
        """Target level existence is checked case-insensitively."""
        enrollment = make_enrollment(target_level="Mid")
        collaborator = make_collaborator(enrollments=[enrollment])

        updated = collaborator.update_target_level(
            enrollment.path_id,
            "  senior ",
            available_levels=["Junior", "Mid", "Senior"],
        )

        assert updated.target_level == "Senior"

    def test_should_preserve_other_enrollments(self) -> None:
        """Updating one enrollment does not touch the others."""
        first = make_enrollment(target_level="Mid")
        second = make_enrollment(target_level="Lead")
        collaborator = make_collaborator(enrollments=[first, second])

        collaborator.update_target_level(
            first.path_id,
            "Senior",
            available_levels=["Mid", "Senior"],
        )

        assert collaborator.enrollments[1] == second

    def test_should_raise_when_updating_unknown_enrollment(self) -> None:
        """Updating a path the collaborator is not enrolled in fails."""
        collaborator = make_collaborator()
        path_id = PathId.generate()

        with pytest.raises(EnrollmentNotFoundError) as error:
            collaborator.update_target_level(
                path_id,
                "Senior",
                available_levels=["Senior"],
            )

        assert error.value.path_id == path_id

    def test_should_reject_target_level_that_does_not_exist(self) -> None:
        """A target level outside the path is rejected without mutation."""
        enrollment = make_enrollment(target_level="Mid")
        collaborator = make_collaborator(enrollments=[enrollment])

        with pytest.raises(
            CollaboratorValidationError,
            match="does not exist in path",
        ):
            collaborator.update_target_level(
                enrollment.path_id,
                "Principal",
                available_levels=["Junior", "Mid", "Senior"],
            )

        assert collaborator.enrollments[0].target_level == "Mid"

    def test_should_reject_blank_target_level(self) -> None:
        """A blank target level is rejected before any lookup."""
        enrollment = make_enrollment(target_level="Mid")
        collaborator = make_collaborator(enrollments=[enrollment])

        with pytest.raises(
            CollaboratorValidationError,
            match="Target level must not be empty",
        ):
            collaborator.update_target_level(
                enrollment.path_id,
                "   ",
                available_levels=["Mid", "Senior"],
            )

    def test_should_reject_non_collection_available_levels(self) -> None:
        """Available levels must be a collection."""
        enrollment = make_enrollment(target_level="Mid")
        collaborator = make_collaborator(enrollments=[enrollment])

        with pytest.raises(
            CollaboratorValidationError,
            match="must be a collection of level names",
        ):
            collaborator.update_target_level(
                enrollment.path_id,
                "Senior",
                available_levels=42,  # type: ignore[arg-type]
            )

    def test_should_reject_string_as_available_levels(self) -> None:
        """A plain string must not be iterated character by character."""
        enrollment = make_enrollment(target_level="Mid")
        collaborator = make_collaborator(enrollments=[enrollment])

        with pytest.raises(
            CollaboratorValidationError,
            match="must be a collection of level names",
        ):
            collaborator.update_target_level(
                enrollment.path_id,
                "Senior",
                available_levels="Senior",
            )

    def test_should_reject_non_string_available_levels(self) -> None:
        """Every available level name must be a string."""
        enrollment = make_enrollment(target_level="Mid")
        collaborator = make_collaborator(enrollments=[enrollment])

        with pytest.raises(
            CollaboratorValidationError,
            match="Available levels must be strings",
        ):
            collaborator.update_target_level(
                enrollment.path_id,
                "Senior",
                available_levels=["Mid", 3],  # type: ignore[list-item]
            )


class TestCollaboratorIdentity:
    """Test identity semantics of Collaborator."""

    def test_should_be_equal_when_ids_match(self) -> None:
        """Identity is based on the collaborator identifier."""
        collaborator_id = CollaboratorId.generate()
        first = make_collaborator(collaborator_id=collaborator_id, name="João")
        second = make_collaborator(collaborator_id=collaborator_id, name="João Silva")

        assert first == second
        assert hash(first) == hash(second)

    def test_should_differ_when_ids_differ(self) -> None:
        """Different identifiers mean different collaborators."""
        assert make_collaborator() != make_collaborator()

    def test_should_not_equal_other_types(self) -> None:
        """Comparison against unrelated types is not supported."""
        assert make_collaborator() != "João Silva"

    def test_should_provide_repr(self) -> None:
        """The representation identifies the collaborator."""
        collaborator = make_collaborator(name="João Silva")

        representation = repr(collaborator)

        assert "Collaborator(" in representation
        assert "João Silva" in representation
