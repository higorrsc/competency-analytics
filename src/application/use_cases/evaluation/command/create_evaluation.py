"""Command use case for creating a draft evaluation."""

from __future__ import annotations

from uuid import UUID

from src.application.dto.evaluation_dtos import (
    EvaluationCreateDTO,
    EvaluationResponseDTO,
)
from src.application.use_cases.errors import NotFoundError
from src.application.use_cases.mappers import map_evaluation
from src.domain.entities.evaluation import Evaluation
from src.domain.repositories.collaborator_repository import (
    CollaboratorRepository,
)
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.evaluation_id import EvaluationId


class CreateEvaluationUseCase:
    """
    Use case for creating a draft evaluation.

    Orchestration flow:

    1. Validate that both the evaluated collaborator and the evaluator exist.
    2. Build the draft aggregate, which enforces lifecycle invariants.
    3. Persist and return the response DTO.
    """

    def __init__(
        self,
        evaluation_repository: EvaluationRepository,
        collaborator_repository: CollaboratorRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependencies.

        Args:
            evaluation_repository: Abstraction for evaluation persistence.
            collaborator_repository: Abstraction used to validate the
                collaborator and the evaluator.
        """
        self._evaluation_repository = evaluation_repository
        self._collaborator_repository = collaborator_repository

    def execute(self, dto: EvaluationCreateDTO) -> EvaluationResponseDTO:
        """
        Create and persist a draft evaluation.

        Args:
            dto: Validated input describing the evaluated collaborator, the
                evaluator, the period label, and the evaluation date.

        Returns:
            The response DTO describing the stored draft evaluation.

        Raises:
            NotFoundError: If the collaborator or the evaluator does not
                exist.
        """
        self._require_collaborator(dto.collaborator_id, "Collaborator")
        self._require_collaborator(dto.evaluator_id, "Evaluator")

        evaluation = Evaluation(
            id=EvaluationId.generate(),
            collaborator_id=CollaboratorId(dto.collaborator_id),
            evaluator_id=CollaboratorId(dto.evaluator_id),
            period=dto.period,
            evaluation_date=dto.evaluation_date,
        )
        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)

    def _require_collaborator(self, identifier: UUID, entity: str) -> None:
        """
        Ensure a collaborator exists, raising when it does not.

        Args:
            identifier: Bare UUID of the collaborator or evaluator.
            entity: Entity label used in the not-found error.

        Raises:
            NotFoundError: When the collaborator does not exist.
        """
        collaborator = self._collaborator_repository.get_by_id(
            CollaboratorId(identifier)
        )
        if collaborator is None:
            raise NotFoundError(entity, identifier)
