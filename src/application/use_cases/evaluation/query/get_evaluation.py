"""Query use case for retrieving an evaluation by identifier."""

from __future__ import annotations

from src.application.dto.evaluation import EvaluationResponseDTO
from src.application.use_cases.evaluation._helpers import load_evaluation
from src.application.use_cases.mappers import map_evaluation
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.evaluation_id import EvaluationId


class GetEvaluationUseCase:
    """Use case for retrieving an evaluation by identifier."""

    def __init__(self, repository: EvaluationRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            repository: Abstraction for evaluation persistence.
        """
        self._repository = repository

    def execute(self, evaluation_id: EvaluationId) -> EvaluationResponseDTO:
        """
        Retrieve an evaluation by identifier.

        Args:
            evaluation_id: Identifier of the requested evaluation.

        Returns:
            The mapped evaluation response DTO.

        Raises:
            NotFoundError: When no evaluation matches the identifier.
        """
        evaluation = load_evaluation(self._repository, evaluation_id)
        return map_evaluation(evaluation)
