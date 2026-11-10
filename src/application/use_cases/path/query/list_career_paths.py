"""Query use case for listing all career paths."""

from __future__ import annotations

from src.application.dto.path import PathResponseDTO
from src.application.use_cases.mappers import map_path
from src.domain.repositories.path_repository import PathRepository


class ListCareerPathsUseCase:
    """Use case for listing all career paths."""

    def __init__(self, repository: PathRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for career path persistence.
        """
        self._repository = repository

    def execute(self) -> list[PathResponseDTO]:
        """
        List all career paths in the catalog.

        Returns:
            List of career path response DTOs.
        """
        paths = self._repository.find_all()
        return [map_path(p) for p in paths]
