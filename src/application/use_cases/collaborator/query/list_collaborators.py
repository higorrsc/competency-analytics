"""Query use case for listing collaborators."""

from __future__ import annotations

from src.application.dto.collaborator import CollaboratorResponseDTO
from src.application.use_cases.mappers import map_collaborator
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.value_objects.path_id import PathId


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
