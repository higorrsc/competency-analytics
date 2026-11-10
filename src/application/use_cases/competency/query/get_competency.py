"""Query use case for retrieving a single competency by identifier."""

from __future__ import annotations

from src.application.dto.competency import CompetencyResponseDTO
from src.application.use_cases.errors import NotFoundError
from src.application.use_cases.mappers import map_competency
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.competency_id import CompetencyId


class GetCompetencyUseCase:
    """Use case for retrieving a single competency by identifier."""

    def __init__(self, repository: CompetencyRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for competency persistence.
        """
        self._repository = repository

    def execute(self, competency_id: CompetencyId) -> CompetencyResponseDTO:
        """
        Retrieve a competency by identifier.

        Args:
            competency_id: Identifier of the requested competency.

        Returns:
            The mapped competency response DTO.

        Raises:
            NotFoundError: When no competency exists with the given id.
        """
        competency = self._repository.get_by_id(competency_id)
        if competency is None:
            raise NotFoundError("Competency", competency_id.value)
        return map_competency(competency)
