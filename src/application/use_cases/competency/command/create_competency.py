"""Command use case for creating a competency in the catalog."""

from __future__ import annotations

from src.application.dto.competency_dtos import (
    CompetencyCreateDTO,
    CompetencyResponseDTO,
)
from src.application.use_cases.errors import ValidationError
from src.application.use_cases.mappers import map_competency
from src.domain.entities.competency import Competency
from src.domain.exceptions.competency_errors import CompetencyValidationError
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId


class CreateCompetencyUseCase:
    """
    Use case for creating a competency in the catalog.

    Orchestration flow:

    1. Build the domain entity (which runs all catalog invariants).
    2. Persist through the repository.
    3. Return the response DTO.

    The use case depends on the repository abstraction only; no storage or
    framework concern is involved.
    """

    def __init__(self, repository: CompetencyRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for competency persistence.
        """
        self._repository = repository

    def execute(self, dto: CompetencyCreateDTO) -> CompetencyResponseDTO:
        """
        Create and persist a new competency.

        Args:
            dto: Validated input describing the competency and the five
                proficiency level descriptions.

        Returns:
            The response DTO describing the stored competency.

        Raises:
            ValidationError: If the catalog invariants reject the input, for
                example a blank name or an incomplete level description map.
        """
        try:
            competency = Competency(
                id=CompetencyId.generate(),
                name=dto.name,
                description=dto.description,
                category_id=CategoryId(dto.category_id),
                group_id=GroupId(dto.group_id),
                level_descriptions=dto.level_descriptions,
            )
        except CompetencyValidationError as exc:
            raise ValidationError(str(exc)) from exc

        self._repository.save(competency)
        return map_competency(competency)
