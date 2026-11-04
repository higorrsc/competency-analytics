"""PathEnrollment value object for collaborator career path enrollments."""

from dataclasses import dataclass, replace
from datetime import datetime

from src.domain.exceptions.collaborator_errors import CollaboratorValidationError
from src.domain.value_objects.path_id import PathId


@dataclass(frozen=True)
class PathEnrollment:
    """
    A collaborator's enrollment in a career path.

    The enrollment records the path, the target level the collaborator wants to
    reach, when the enrollment was created, and whether it is currently the
    collaborator's active path.

    Enrollments are immutable value objects: activating, deactivating, or
    changing the target level returns a new instance and leaves the original
    untouched. This preserves enrollment history, which is an explicit business
    requirement.

    The single-active-path rule is enforced by the owning ``Collaborator``
    aggregate, because it spans multiple enrollments.
    """

    path_id: PathId
    target_level: str
    enrolled_at: datetime
    is_active: bool = False

    def __post_init__(self) -> None:
        """Validate the enrollment invariants after construction."""
        self._validate_path_id(self.path_id)
        self._validate_target_level(self.target_level)
        self._validate_enrolled_at(self.enrolled_at)
        self._validate_is_active(self.is_active)
        object.__setattr__(self, "target_level", self.target_level.strip())

    @staticmethod
    def _validate_path_id(path_id: object) -> None:
        """
        Validate that the enrollment references a career path by identifier.

        Args:
            path_id: Proposed career path identifier.

        Raises:
            CollaboratorValidationError: If the value is not a PathId.
        """
        if not isinstance(path_id, PathId):
            raise CollaboratorValidationError(
                f"Enrollment path_id must be a PathId, got {type(path_id).__name__}"
            )

    @staticmethod
    def _validate_target_level(target_level: object) -> None:
        """
        Validate that the target level is present and meaningful.

        Args:
            target_level: Proposed target level name.

        Raises:
            CollaboratorValidationError: If the target level is not a
                non-blank string.
        """
        if not isinstance(target_level, str) or not target_level.strip():
            raise CollaboratorValidationError("Target level must not be empty")

    @staticmethod
    def _validate_enrolled_at(enrolled_at: object) -> None:
        """
        Validate that the enrollment timestamp is a datetime.

        Args:
            enrolled_at: Proposed enrollment timestamp.

        Raises:
            CollaboratorValidationError: If the value is not a datetime.
        """
        if not isinstance(enrolled_at, datetime):
            raise CollaboratorValidationError(
                f"Enrolled at must be a datetime, got {type(enrolled_at).__name__}"
            )

    @staticmethod
    def _validate_is_active(is_active: object) -> None:
        """
        Validate that the active flag is a boolean.

        Args:
            is_active: Proposed active flag.

        Raises:
            CollaboratorValidationError: If the value is not a bool.
        """
        if not isinstance(is_active, bool):
            raise CollaboratorValidationError(
                f"Enrollment is_active must be a bool, got {type(is_active).__name__}"
            )

    def activate(self) -> "PathEnrollment":
        """
        Return a copy of the enrollment marked as active.

        Returns:
            A new active enrollment; the original is unchanged.
        """
        return replace(self, is_active=True)

    def deactivate(self) -> "PathEnrollment":
        """
        Return a copy of the enrollment marked as inactive.

        Returns:
            A new inactive enrollment; the original is unchanged.
        """
        return replace(self, is_active=False)

    def with_target_level(self, target_level: str) -> "PathEnrollment":
        """
        Return a copy of the enrollment with a different target level.

        The enrollment date and active status are preserved so changing the
        target does not create a new enrollment nor reset its history.

        Args:
            target_level: New target level name.

        Returns:
            A new enrollment with the given target level.

        Raises:
            CollaboratorValidationError: If the target level is blank.
        """
        self._validate_target_level(target_level)
        return replace(self, target_level=target_level.strip())

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"PathEnrollment(path_id={self.path_id!r}, "
            f"target_level={self.target_level!r}, "
            f"enrolled_at={self.enrolled_at!r}, is_active={self.is_active})"
        )
