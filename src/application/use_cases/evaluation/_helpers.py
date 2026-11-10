"""Helper utilities for evaluation use cases."""

from __future__ import annotations

from src.application.use_cases.errors import NotFoundError
from src.domain.entities.evaluation import Evaluation
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.evaluation_id import EvaluationId


def load_evaluation(
    repository: EvaluationRepository,
    evaluation_id: EvaluationId,
) -> Evaluation:
    """
    Load an evaluation or fail when it does not exist.

    Args:
        repository: Evaluation persistence abstraction.
        evaluation_id: Identifier of the evaluation.

    Returns:
        The stored evaluation aggregate.

    Raises:
        NotFoundError: When no evaluation matches the identifier.
    """
    evaluation = repository.get_by_id(evaluation_id)
    if evaluation is None:
        raise NotFoundError("Evaluation", evaluation_id.value)
    return evaluation
