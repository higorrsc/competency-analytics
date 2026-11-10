"""Command use case for submitting an evaluation for review."""

from __future__ import annotations

from datetime import UTC, datetime

from src.application.dto.evaluation import EvaluationResponseDTO
from src.application.use_cases.errors import (
    ConflictError,
    ValidationError,
)
from src.application.use_cases.evaluation._helpers import load_evaluation
from src.application.use_cases.mappers import map_evaluation
from src.domain.exceptions.evaluation_errors import (
    EvaluationValidationError,
    InvalidStatusTransitionError,
)
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.evaluation_id import EvaluationId


class SubmitEvaluationUseCase:
    """
    Use case for submitting an evaluation for collaborator review.

    Orchestration flow:

    1. Load the draft evaluation.
    2. Delegate to ``Evaluation.submit``, which transitions DRAFT to
       COMPLETED and requires at least one measurement.
    3. Persist and return the updated DTO.
    """

    def __init__(self, evaluation_repository: EvaluationRepository) -> None:
        """
        Initialize the use case with its repository dependency.

        Args:
            evaluation_repository: Abstraction for evaluation persistence.
        """
        self._evaluation_repository = evaluation_repository

    def execute(self, evaluation_id: EvaluationId) -> EvaluationResponseDTO:
        """
        Submit a draft evaluation, making it immutable for the evaluator.

        Args:
            evaluation_id: Identifier of the draft evaluation.

        Returns:
            The updated evaluation response DTO in COMPLETED state.

        Raises:
            NotFoundError: If the evaluation does not exist.
            ConflictError: If the evaluation is not in draft state.
            ValidationError: If the evaluation has no measurements yet.
        """
        evaluation = load_evaluation(self._evaluation_repository, evaluation_id)

        try:
            evaluation.submit(submitted_at=datetime.now(UTC))
        except InvalidStatusTransitionError as exc:
            raise ConflictError(str(exc)) from exc
        except EvaluationValidationError as exc:
            raise ValidationError(str(exc)) from exc

        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)
