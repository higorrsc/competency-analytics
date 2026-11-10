"""Command use case for accepting a completed evaluation."""

from __future__ import annotations

from datetime import UTC, datetime

from src.application.dto.evaluation_dtos import EvaluationResponseDTO
from src.application.use_cases.errors import ConflictError
from src.application.use_cases.evaluation._helpers import load_evaluation
from src.application.use_cases.mappers import map_evaluation
from src.domain.exceptions.evaluation_errors import InvalidStatusTransitionError
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.evaluation_id import EvaluationId


class AcceptEvaluationUseCase:
    """
    Use case for the collaborator accepting a completed evaluation.

    Orchestration flow:

    1. Load the completed evaluation.
    2. Delegate to ``Evaluation.accept``, which transitions COMPLETED to
       ACCEPTED and permanently finalizes the evaluation.
    3. Persist and return the updated DTO.
    """

    def __init__(self, evaluation_repository: EvaluationRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            evaluation_repository: Abstraction for evaluation persistence.
        """
        self._evaluation_repository = evaluation_repository

    def execute(
        self,
        evaluation_id: EvaluationId,
        response_notes: str | None = None,
    ) -> EvaluationResponseDTO:
        """
        Accept a completed evaluation on behalf of the collaborator.

        Args:
            evaluation_id: Identifier of the completed evaluation.
            response_notes: Optional free-form acknowledgment notes.

        Returns:
            The updated evaluation response DTO in ACCEPTED state.

        Raises:
            NotFoundError: If the evaluation does not exist.
            ConflictError: If the evaluation is not awaiting response.
        """
        evaluation = load_evaluation(self._evaluation_repository, evaluation_id)

        try:
            evaluation.accept(
                response_notes=response_notes,
                responded_at=datetime.now(UTC),
            )
        except InvalidStatusTransitionError as exc:
            raise ConflictError(str(exc)) from exc

        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)
