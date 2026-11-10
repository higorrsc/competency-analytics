"""Command use case for enrolling a collaborator in a career path."""

from __future__ import annotations

from datetime import UTC, datetime

from src.application.dto.collaborator import (
    CollaboratorResponseDTO,
    EnrollmentCreateDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.mappers import map_collaborator
from src.domain.exceptions.collaborator_errors import (
    CollaboratorValidationError,
    EnrollmentNotFoundError,
)
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.repositories.path_repository import PathRepository
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId


class EnrollCollaboratorInPathUseCase:
    """
    Use case for enrolling a collaborator in a career path.

    Orchestration flow:

    1. Load the collaborator and the target path.
    2. Canonicalize the requested target level against the path's defined
       levels (case-insensitive).
    3. Add the enrollment to the collaborator aggregate.
    4. Activate the enrollment, which deactivates any previous active path,
       enforcing the single-active-path rule at the aggregate level.
    5. Persist the aggregate and return the updated collaborator DTO.

    Enrollment history is preserved: previous enrollments keep their entries
    with ``is_active=False``.
    """

    def __init__(
        self,
        collaborator_repository: CollaboratorRepository,
        path_repository: PathRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependencies.

        Args:
            collaborator_repository: Abstraction for collaborator persistence.
            path_repository: Abstraction used to resolve the target path.
        """
        self._collaborator_repository = collaborator_repository
        self._path_repository = path_repository

    def execute(
        self,
        collaborator_id: CollaboratorId,
        dto: EnrollmentCreateDTO,
    ) -> CollaboratorResponseDTO:
        """
        Enroll a collaborator in a career path and make it their active path.

        Args:
            collaborator_id: Identifier of the collaborator to enroll.
            dto: Validated input with the path identifier and target level.

        Returns:
            The updated collaborator response DTO, including the full
            enrollment history.

        Raises:
            NotFoundError: If the collaborator or the path does not exist.
            ValidationError: If the target level is not defined in the path.
            ConflictError: If the collaborator is already enrolled in the
                same path (re-enrollment is not allowed).
        """
        collaborator = self._collaborator_repository.get_by_id(collaborator_id)
        if collaborator is None:
            raise NotFoundError("Collaborator", collaborator_id.value)
        path_id = PathId(dto.path_id)
        path = self._path_repository.get_by_id(path_id)
        if path is None:
            raise NotFoundError("Path", dto.path_id)

        level = path.find_level_by_name(dto.target_level)
        if level is None:
            raise ValidationError(
                f"target level {dto.target_level!r} is not defined in path "
                f"{path.name!r}"
            )

        try:
            collaborator.enroll(path_id, level.name, enrolled_at=datetime.now(UTC))
        except CollaboratorValidationError as exc:
            raise ConflictError(str(exc)) from exc
        try:
            collaborator.set_active_path(path_id)
        except EnrollmentNotFoundError as exc:
            raise NotFoundError("Enrollment", path_id.value) from exc

        self._collaborator_repository.save(collaborator)
        return map_collaborator(collaborator)
