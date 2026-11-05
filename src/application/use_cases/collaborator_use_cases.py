"""Use cases for collaborator registration and path enrollment."""

from datetime import UTC, datetime

from src.application.dto.collaborator_dtos import (
    CollaboratorCreateDTO,
    CollaboratorResponseDTO,
    EnrollmentCreateDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.mappers import map_collaborator
from src.domain.entities.collaborator import Collaborator
from src.domain.exceptions.collaborator_errors import (
    CollaboratorValidationError,
    EnrollmentNotFoundError,
)
from src.domain.repositories.collaborator_repository import CollaboratorRepository
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


class CreateCollaboratorUseCase:
    """Use case for registering a new collaborator."""

    def __init__(
        self,
        collaborator_repository: CollaboratorRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            collaborator_repository: Abstraction for collaborator persistence.
        """
        self._collaborator_repository = collaborator_repository

    def execute(self, dto: CollaboratorCreateDTO) -> CollaboratorResponseDTO:
        """
        Register a new collaborator.

        Args:
            dto: Input contract with name, email, and department.

        Returns:
            The created collaborator response DTO.

        Raises:
            ValidationError: When name, email, or department invariants fail.
            ConflictError: When a collaborator with the email already exists.
        """
        try:
            collaborator = Collaborator(
                id=CollaboratorId.generate(),
                name=dto.name,
                email=dto.email,
                department=dto.department,
            )
        except CollaboratorValidationError as exc:
            raise ValidationError(str(exc)) from exc

        try:
            self._collaborator_repository.save(collaborator)
        except Exception as exc:
            raise ConflictError(
                f"Collaborator with email {dto.email!r} already exists"
            ) from exc

        return map_collaborator(collaborator)


class GetCollaboratorUseCase:
    """Use case for retrieving a collaborator by identifier."""

    def __init__(
        self,
        collaborator_repository: CollaboratorRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            collaborator_repository: Abstraction for collaborator persistence.
        """
        self._collaborator_repository = collaborator_repository

    def execute(self, collaborator_id: CollaboratorId) -> CollaboratorResponseDTO:
        """
        Retrieve a collaborator by identifier.

        Args:
            collaborator_id: Identifier of the requested collaborator.

        Returns:
            The mapped collaborator response DTO.

        Raises:
            NotFoundError: When no collaborator exists with the given id.
        """
        collaborator = self._collaborator_repository.get_by_id(collaborator_id)
        if collaborator is None:
            raise NotFoundError("Collaborator", collaborator_id.value)
        return map_collaborator(collaborator)


class ListCollaboratorsUseCase:
    """Use case for listing collaborators."""

    def __init__(
        self,
        collaborator_repository: CollaboratorRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            collaborator_repository: Abstraction for collaborator persistence.
        """
        self._collaborator_repository = collaborator_repository

    def execute(
        self,
        *,
        path_id: PathId | None = None,
        active_only: bool = False,
    ) -> list[CollaboratorResponseDTO]:
        """
        List collaborators optionally filtered by path.

        Args:
            path_id: Optional career path filter.
            active_only: When True, return only active enrollments.

        Returns:
            List of matching collaborator response DTOs.
        """
        if path_id is not None:
            collaborators = self._collaborator_repository.find_by_path(
                path_id, active_only=active_only
            )
        else:
            collaborators = self._collaborator_repository.find_all()
        return [map_collaborator(c) for c in collaborators]


class ActivateCollaboratorPathUseCase:
    """Use case for making an existing enrollment the single active path."""

    def __init__(
        self,
        collaborator_repository: CollaboratorRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            collaborator_repository: Abstraction for collaborator persistence.
        """
        self._collaborator_repository = collaborator_repository

    def execute(
        self,
        collaborator_id: CollaboratorId,
        path_id: PathId,
    ) -> CollaboratorResponseDTO:
        """
        Activate an existing enrollment, deactivating any previously active path.

        Args:
            collaborator_id: Identifier of the collaborator.
            path_id: Career path to activate.

        Returns:
            The updated collaborator response DTO.

        Raises:
            NotFoundError: When collaborator or enrollment does not exist.
        """
        collaborator = self._collaborator_repository.get_by_id(collaborator_id)
        if collaborator is None:
            raise NotFoundError("Collaborator", collaborator_id.value)
        try:
            collaborator.set_active_path(path_id)
        except EnrollmentNotFoundError as exc:
            raise NotFoundError("Enrollment", path_id.value) from exc

        self._collaborator_repository.save(collaborator)
        return map_collaborator(collaborator)
