"""Query use case for retrieving a single career path by identifier."""

from __future__ import annotations

from src.application.dto.path import PathResponseDTO
from src.application.use_cases.errors import NotFoundError
from src.application.use_cases.mappers import map_path
from src.domain.repositories.path_repository import PathRepository
from src.domain.value_objects.path_id import PathId


class GetCareerPathUseCase:
    """Use case for retrieving a single career path by identifier."""

    def __init__(self, repository: PathRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for career path persistence.
        """
        self._repository = repository

    def execute(self, path_id: PathId) -> PathResponseDTO:
        """
        Retrieve a career path by identifier.

        Args:
            path_id: Identifier of the requested path.

        Returns:
            The mapped path response DTO with levels and requirements.

        Raises:
            NotFoundError: When no path exists with the given id.
        """
        path = self._repository.get_by_id(path_id)
        if path is None:
            raise NotFoundError("CareerPath", path_id.value)
        return map_path(path)
