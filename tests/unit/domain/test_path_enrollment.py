"""Unit tests for the PathEnrollment value object."""

from datetime import UTC, datetime

import pytest

from src.domain.exceptions.collaborator_errors import CollaboratorValidationError
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


class TestPathEnrollmentCreation:
    """Test creation and validation invariants of PathEnrollment."""

    def test_should_create_enrollment_when_data_is_valid(self) -> None:
        """A valid enrollment keeps all of its data."""
        path_id = PathId.generate()

        enrollment = make_enrollment(
            path_id=path_id,
            target_level="Senior",
            enrolled_at=ENROLLED_AT,
        )

        assert enrollment.path_id == path_id
        assert enrollment.target_level == "Senior"
        assert enrollment.enrolled_at == ENROLLED_AT

    def test_should_be_inactive_by_default(self) -> None:
        """New enrollments start inactive unless activation is explicit."""
        enrollment = PathEnrollment(
            path_id=PathId.generate(),
            target_level="Senior",
            enrolled_at=ENROLLED_AT,
        )

        assert enrollment.is_active is False

    def test_should_trim_target_level(self) -> None:
        """Surrounding whitespace is removed from the target level."""
        enrollment = make_enrollment(target_level="  Senior  ")

        assert enrollment.target_level == "Senior"

    def test_should_reject_non_path_id(self) -> None:
        """The path reference must be a PathId."""
        with pytest.raises(
            CollaboratorValidationError,
            match="path_id must be a PathId",
        ):
            make_enrollment(path_id="path-1")  # type: ignore[arg-type]

    def test_should_reject_blank_target_level(self) -> None:
        """A blank target level violates the invariant."""
        with pytest.raises(
            CollaboratorValidationError,
            match="Target level must not be empty",
        ):
            make_enrollment(target_level="   ")

    def test_should_reject_non_string_target_level(self) -> None:
        """The target level must be a string."""
        with pytest.raises(
            CollaboratorValidationError,
            match="Target level must not be empty",
        ):
            make_enrollment(target_level=3)  # type: ignore[arg-type]

    def test_should_reject_non_datetime_enrolled_at(self) -> None:
        """The enrollment timestamp must be a datetime."""
        with pytest.raises(
            CollaboratorValidationError,
            match="Enrolled at must be a datetime",
        ):
            make_enrollment(enrolled_at="2026-01-15")  # type: ignore[arg-type]

    def test_should_reject_non_boolean_active_flag(self) -> None:
        """The active flag must be a real boolean, not a truthy integer."""
        with pytest.raises(
            CollaboratorValidationError,
            match="is_active must be a bool",
        ):
            make_enrollment(is_active=1)  # type: ignore[arg-type]

    def test_should_be_immutable(self) -> None:
        """Enrollments are frozen value objects."""
        enrollment = make_enrollment()

        with pytest.raises(AttributeError):
            enrollment.target_level = "Mid"  # type: ignore[misc]


class TestPathEnrollmentTransitions:
    """Test activation, deactivation, and target level changes."""

    def test_should_activate_returning_a_new_instance(self) -> None:
        """Activation produces an active copy and keeps the original."""
        enrollment = make_enrollment(is_active=False)

        activated = enrollment.activate()

        assert activated.is_active is True
        assert enrollment.is_active is False
        assert activated.path_id == enrollment.path_id
        assert activated.enrolled_at == enrollment.enrolled_at

    def test_should_deactivate_returning_a_new_instance(self) -> None:
        """Deactivation produces an inactive copy and keeps the original."""
        enrollment = make_enrollment(is_active=True)

        deactivated = enrollment.deactivate()

        assert deactivated.is_active is False
        assert enrollment.is_active is True

    def test_should_change_target_level_preserving_history(self) -> None:
        """Changing the target preserves path, date, and active status."""
        enrollment = make_enrollment(target_level="Mid", is_active=True)

        updated = enrollment.with_target_level("Senior")

        assert updated.target_level == "Senior"
        assert updated.path_id == enrollment.path_id
        assert updated.enrolled_at == enrollment.enrolled_at
        assert updated.is_active is True
        assert enrollment.target_level == "Mid"

    def test_should_trim_new_target_level(self) -> None:
        """The new target level is normalized."""
        enrollment = make_enrollment(target_level="Mid")

        updated = enrollment.with_target_level("  Senior  ")

        assert updated.target_level == "Senior"

    def test_should_reject_blank_new_target_level(self) -> None:
        """A blank target level is rejected without changing the original."""
        enrollment = make_enrollment(target_level="Mid")

        with pytest.raises(
            CollaboratorValidationError,
            match="Target level must not be empty",
        ):
            enrollment.with_target_level("   ")

        assert enrollment.target_level == "Mid"

    def test_should_provide_repr(self) -> None:
        """The representation exposes the enrollment fields."""
        enrollment = make_enrollment(target_level="Senior")

        representation = repr(enrollment)

        assert "PathEnrollment(" in representation
        assert "Senior" in representation
        assert "is_active=False" in representation
