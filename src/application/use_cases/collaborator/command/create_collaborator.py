"""Command use case for registering a new collaborator."""

from __future__ import annotations

from src.application.dto.collaborator_dtos import (
    CollaboratorCreateDTO,
    CollaboratorResponseDTO,
)
from src.application.use_cases.errors import ConflictError, ValidationError
from src.application.use_cases.mappers import map_collaborator
from src.domain.entities.collaborator import Collaborator
from src.domain.exceptions.collaborator_errors import CollaboratorValidationError
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.value_objects.collaborator_id import CollaboratorId


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
