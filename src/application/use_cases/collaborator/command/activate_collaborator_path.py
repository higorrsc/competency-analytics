"""Command use case for activating an existing career path enrollment."""

from __future__ import annotations

from src.application.dto.collaborator_dtos import CollaboratorResponseDTO
from src.application.use_cases.errors import NotFoundError
from src.application.use_cases.mappers import map_collaborator
from src.domain.exceptions.collaborator_errors import EnrollmentNotFoundError
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_id import PathId


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
