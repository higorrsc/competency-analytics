"""Command use case for removing a competency from the catalog."""

from __future__ import annotations

from src.application.use_cases.errors import ConflictError, NotFoundError
from src.domain.exceptions.competency_errors import CompetencyReferencedError
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.value_objects.competency_id import CompetencyId


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
            ConflictError: When the competency is referenced and cannot be
                deleted.
        """
        competency = self._repository.get_by_id(competency_id)
        if competency is None:
            raise NotFoundError("Competency", competency_id.value)
        try:
            self._repository.delete(competency_id)
        except CompetencyReferencedError as exc:
            raise ConflictError(str(exc)) from exc
