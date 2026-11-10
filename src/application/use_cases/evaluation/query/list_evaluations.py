"""Query use case for listing evaluations."""

from __future__ import annotations

from src.application.dto.evaluation import EvaluationResponseDTO
from src.application.use_cases.mappers import map_evaluation
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.collaborator_id import CollaboratorId


class ListEvaluationsUseCase:
    """Use case for listing evaluations."""

    def __init__(self, repository: EvaluationRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for evaluation persistence.
        """
        self._repository = repository

    def execute(
        self, *, collaborator_id: CollaboratorId | None = None
    ) -> list[EvaluationResponseDTO]:
        """
        List evaluations, optionally filtered by collaborator.

        Args:
            collaborator_id: Optional collaborator filter.

        Returns:
            List of matching evaluation response DTOs.
        """
        evaluations = self._repository.find_all(collaborator_id=collaborator_id)
        return [map_evaluation(e) for e in evaluations]
