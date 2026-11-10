"""Query use case for listing competencies filtered by hierarchy."""

from __future__ import annotations

from src.application.dto.competency_dtos import CompetencyResponseDTO
from src.application.use_cases.mappers import map_competency
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.group_id import GroupId


class ListCompetenciesUseCase:
    """Use case for listing competencies filtered by hierarchy."""

    def __init__(self, repository: CompetencyRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for competency persistence.
        """
        self._repository = repository

    def execute(
        self,
        *,
        category_id: CategoryId | None = None,
        group_id: GroupId | None = None,
    ) -> list[CompetencyResponseDTO]:
        """
        List competencies matching the given hierarchy filters.

        Args:
            category_id: Optional category filter.
            group_id: Optional group filter.

        Returns:
            List of matching competency response DTOs.
        """
        competencies = self._repository.find_by_hierarchy(
            category_id=category_id,
            group_id=group_id,
        )
        return [map_competency(c) for c in competencies]
