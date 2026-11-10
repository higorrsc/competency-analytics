"""Query use case for retrieving a collaborator by identifier."""

from __future__ import annotations

from src.application.dto.collaborator import CollaboratorResponseDTO
from src.application.use_cases.errors import NotFoundError
from src.application.use_cases.mappers import map_collaborator
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.value_objects.collaborator_id import CollaboratorId


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
