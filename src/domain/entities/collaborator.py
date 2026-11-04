"""Collaborator aggregate root for employee records and path enrollments."""

import re
from collections.abc import Collection
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import cast

from src.domain.exceptions.collaborator_errors import (
    CollaboratorValidationError,
    EnrollmentNotFoundError,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.path_id import PathId

#: Pragmatic email shape check: one "@", no whitespace, and a dot in the domain.
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(eq=False)
class Collaborator:
    """
    Aggregate root representing an employee and their career path history.

    A collaborator owns every path enrollment. The aggregate enforces the
    following invariants:

    - name, email, and department are present and meaningful;
    - the email has a valid shape;
    - a career path can be enrolled at most once per collaborator;
    - at most one enrollment is active at any moment;
    - enrollment history is preserved when the active path changes.

    Enrollments are value objects inside this aggregate. References to career
    paths use ``PathId`` only, keeping the aggregates loosely coupled.
    """

    id: CollaboratorId
    name: str
    email: str
    department: str
    enrollments: list[PathEnrollment] = field(default_factory=list[PathEnrollment])

    def __post_init__(self) -> None:
        """Validate collaborator invariants immediately after construction."""
        self._validate_id(self.id)
        self._validate_name(self.name)
        self._validate_email(self.email)
        self._validate_department(self.department)
        self._validate_enrollments(self.enrollments)
        self.name = self.name.strip()
        self.email = self.email.strip()
        self.department = self.department.strip()

    @staticmethod
    def _validate_id(collaborator_id: object) -> None:
        """
        Validate that the identity is a CollaboratorId.

        Args:
            collaborator_id: Proposed collaborator identifier.

        Raises:
            CollaboratorValidationError: If the value is not a CollaboratorId.
        """
        if not isinstance(collaborator_id, CollaboratorId):
            raise CollaboratorValidationError(
                f"Collaborator id must be a CollaboratorId, got {type(collaborator_id).__name__}"
            )

    @staticmethod
    def _validate_name(name: object) -> None:
        """
        Validate that the collaborator name is present and meaningful.

        Args:
            name: Proposed collaborator name.

        Raises:
            CollaboratorValidationError: If the name is blank.
        """
        if not isinstance(name, str) or not name.strip():
            raise CollaboratorValidationError("Collaborator name must not be empty")

    @staticmethod
    def _validate_email(email: object) -> None:
        """
        Validate that the email is present and has a valid shape.

        Args:
            email: Proposed collaborator email.

        Raises:
            CollaboratorValidationError: If the email is blank or malformed.
        """
        if not isinstance(email, str) or not email.strip():
            raise CollaboratorValidationError("Collaborator email must not be empty")
        if _EMAIL_PATTERN.fullmatch(email.strip()) is None:
            raise CollaboratorValidationError(f"Collaborator email {email!r} is not valid")

    @staticmethod
    def _validate_department(department: object) -> None:
        """
        Validate that the department is present and meaningful.

        Args:
            department: Proposed collaborator department.

        Raises:
            CollaboratorValidationError: If the department is blank.
        """
        if not isinstance(department, str) or not department.strip():
            raise CollaboratorValidationError("Collaborator department must not be empty")

    @staticmethod
    def _validate_enrollments(enrollments: object) -> None:
        """
        Validate the enrollment collection and its cross-enrollment rules.

        Args:
            enrollments: Proposed enrollment list.

        Raises:
            CollaboratorValidationError: If the value is not a list, contains
                non-enrollment items, repeats a career path, or has more than
                one active enrollment.
        """
        if not isinstance(enrollments, list):
            raise CollaboratorValidationError(
                "Collaborator enrollments must be a list of PathEnrollment"
            )

        seen_paths: set[PathId] = set()
        active_count = 0
        for enrollment in cast(list[object], enrollments):
            if not isinstance(enrollment, PathEnrollment):
                raise CollaboratorValidationError(
                    "Collaborator enrollments must be PathEnrollment instances"
                )
            if enrollment.path_id in seen_paths:
                raise CollaboratorValidationError(
                    f"Collaborator is already enrolled in path {enrollment.path_id}"
                )
            seen_paths.add(enrollment.path_id)
            if enrollment.is_active:
                active_count += 1

        if active_count > 1:
            raise CollaboratorValidationError(
                "Collaborator cannot have more than one active path enrollment"
            )

    def add_enrollment(self, enrollment: PathEnrollment) -> None:
        """
        Add an enrollment to the collaborator, preserving all invariants.

        The candidate list is validated before mutation, so a rejected
        enrollment leaves the aggregate unchanged. Adding an active enrollment
        deactivates any previously active one, enforcing the single-active-path
        rule.

        Args:
            enrollment: Enrollment to add.

        Raises:
            CollaboratorValidationError: If the collaborator is already
                enrolled in the same career path.
        """
        if self.find_enrollment(enrollment.path_id) is not None:
            raise CollaboratorValidationError(
                f"Collaborator is already enrolled in path {enrollment.path_id}"
            )

        candidate = [
            existing.deactivate() if enrollment.is_active else existing
            for existing in self.enrollments
        ]
        candidate.append(enrollment)
        self._validate_enrollments(candidate)
        self.enrollments = candidate

    def enroll(
        self,
        path_id: PathId,
        target_level: str,
        enrolled_at: datetime | None = None,
    ) -> PathEnrollment:
        """
        Enroll the collaborator in a career path as an inactive enrollment.

        New enrollments start inactive by default, as required by the
        specification. Activating a path is an explicit operation through
        ``set_active_path``.

        Args:
            path_id: Career path to enroll in.
            target_level: Level the collaborator wants to reach.
            enrolled_at: Enrollment timestamp; defaults to the current UTC time.

        Returns:
            The newly created enrollment.

        Raises:
            CollaboratorValidationError: If the collaborator is already
                enrolled in the path or the enrollment data is invalid.
        """
        enrollment = PathEnrollment(
            path_id=path_id,
            target_level=target_level,
            enrolled_at=enrolled_at or datetime.now(UTC),
        )
        self.add_enrollment(enrollment)
        return enrollment

    def find_enrollment(self, path_id: PathId) -> PathEnrollment | None:
        """
        Return the enrollment for a career path, if present.

        Args:
            path_id: Career path to look up.

        Returns:
            The matching enrollment, or ``None`` when absent.
        """
        for enrollment in self.enrollments:
            if enrollment.path_id == path_id:
                return enrollment
        return None

    def active_enrollment(self) -> PathEnrollment | None:
        """
        Return the single active enrollment, if any.

        Returns:
            The active enrollment, or ``None`` when no path is active.
        """
        for enrollment in self.enrollments:
            if enrollment.is_active:
                return enrollment
        return None

    def set_active_path(self, path_id: PathId) -> PathEnrollment:
        """
        Make a career path the collaborator's single active path.

        Any previously active enrollment is automatically deactivated while
        remaining in the enrollment history.

        Args:
            path_id: Career path to activate.

        Returns:
            The activated enrollment.

        Raises:
            EnrollmentNotFoundError: If the collaborator is not enrolled in
                the given path.
        """
        if self.find_enrollment(path_id) is None:
            raise EnrollmentNotFoundError(path_id)

        candidate = [
            enrollment.activate() if enrollment.path_id == path_id else enrollment.deactivate()
            for enrollment in self.enrollments
        ]
        self._validate_enrollments(candidate)
        self.enrollments = candidate
        activated = self.find_enrollment(path_id)
        if activated is None:  # pragma: no cover - guarded by the check above
            raise EnrollmentNotFoundError(path_id)
        return activated

    def update_target_level(
        self,
        path_id: PathId,
        target_level: str,
        *,
        available_levels: Collection[str],
    ) -> PathEnrollment:
        """
        Change the target level of an existing enrollment.

        The enrollment date, active status, and all other enrollments are
        preserved: only the target level changes. The new target must exist in
        the career path, whose level names are supplied by the application
        layer because the collaborator aggregate only references the path by
        identifier.

        Args:
            path_id: Career path whose enrollment should be updated.
            target_level: New target level name.
            available_levels: Level names that exist in the career path.

        Returns:
            The updated enrollment.

        Raises:
            EnrollmentNotFoundError: If the collaborator is not enrolled in
                the given path.
            CollaboratorValidationError: If the target level is blank or does
                not exist in the career path.
        """
        if not isinstance(cast(object, target_level), str) or not target_level.strip():
            raise CollaboratorValidationError("Target level must not be empty")

        index = self._index_of_enrollment(path_id)
        enrollment = self.enrollments[index]
        available = self._normalize_level_names(available_levels)
        normalized_target = target_level.strip().casefold()
        canonical_target = available.get(normalized_target)

        if canonical_target is None:
            raise CollaboratorValidationError(
                f"Target level {target_level!r} does not exist in path {path_id}"
            )

        updated = enrollment.with_target_level(canonical_target)
        candidate = [*self.enrollments]
        candidate[index] = updated
        self._validate_enrollments(candidate)
        self.enrollments = candidate
        return updated

    @staticmethod
    def _normalize_level_names(available_levels: object) -> dict[str, str]:
        """
        Normalize and validate the level names supplied by the application.

        Args:
            available_levels: Level names that exist in the career path.

        Returns:
            A mapping from the normalized name to the canonical path level
            name, ready for case-insensitive lookup and canonical storage.

        Raises:
            CollaboratorValidationError: If the collection contains non-string
                values.
        """
        if isinstance(available_levels, str) or not isinstance(available_levels, Collection):
            raise CollaboratorValidationError(
                "Available levels must be a collection of level names"
            )
        normalized: dict[str, str] = {}
        for level in cast(Collection[object], available_levels):
            if not isinstance(level, str):
                raise CollaboratorValidationError(
                    f"Available levels must be strings, got {type(level).__name__}"
                )
            normalized[level.strip().casefold()] = level.strip()
        return normalized

    def _index_of_enrollment(self, path_id: PathId) -> int:
        """
        Return the list index of an enrollment or raise when it is missing.

        Args:
            path_id: Career path to locate.

        Returns:
            The index of the matching enrollment.

        Raises:
            EnrollmentNotFoundError: If the collaborator is not enrolled in
                the given path.
        """
        for index, enrollment in enumerate(self.enrollments):
            if enrollment.path_id == path_id:
                return index
        raise EnrollmentNotFoundError(path_id)

    def __eq__(self, other: object) -> bool:
        """Compare collaborators by identity."""
        if not isinstance(other, Collaborator):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash collaborators by identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"Collaborator(id={self.id!r}, name={self.name!r}, enrollments={len(self.enrollments)})"
        )
