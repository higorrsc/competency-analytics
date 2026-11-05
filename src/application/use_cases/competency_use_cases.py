"""Use cases for the hierarchical competency catalog."""

from src.application.dto.competency_dtos import (
    CompetencyCreateDTO,
    CompetencyResponseDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.mappers import map_competency
from src.domain.entities.competency import Competency
from src.domain.exceptions.competency_errors import (
    CompetencyReferencedError,
    CompetencyValidationError,
)
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


class DeleteCompetencyUseCase:
    """
    Use case for removing a competency from the catalog.

    Rejects deletion if the competency is referenced by paths or evaluations.
    """

    def __init__(self, repository: CompetencyRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for competency persistence.
        """
        self._repository = repository

    def execute(self, competency_id: CompetencyId) -> None:
        """
        Delete a competency from the catalog.

        Args:
            competency_id: Identifier of the competency to remove.

        Raises:
            NotFoundError: When no competency exists with the given id.
            ConflictError: When the competency is referenced and cannot be deleted.
        """
        competency = self._repository.get_by_id(competency_id)
        if competency is None:
            raise NotFoundError("Competency", competency_id.value)
        try:
            self._repository.delete(competency_id)
        except CompetencyReferencedError as exc:
            raise ConflictError(str(exc)) from exc
