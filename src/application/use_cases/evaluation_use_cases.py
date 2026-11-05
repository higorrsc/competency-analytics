"""Use cases for the evaluation lifecycle.

Orchestration covers the full lifecycle:

    DRAFT --submit--> COMPLETED --accept/contest--> ACCEPTED | CONTESTED

All state rules are enforced by the ``Evaluation`` aggregate; use cases load
aggregates, delegate to domain behavior, translate domain errors into
application errors, persist, and map to response DTOs.
"""

from datetime import UTC, datetime
from uuid import UUID

from src.application.dto.evaluation_dtos import (
    EvaluationCreateDTO,
    EvaluationResponseDTO,
    MeasurementCreateDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
    ValidationError,
)
from src.application.use_cases.mappers import map_evaluation
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.evaluation import Evaluation
from src.domain.exceptions.evaluation_errors import (
    EvaluationImmutableError,
    EvaluationValidationError,
    InvalidStatusTransitionError,
)
from src.domain.repositories.collaborator_repository import CollaboratorRepository
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.measurement_id import MeasurementId


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
        collaborator = self._collaborator_repository.get_by_id(CollaboratorId(identifier))
        if collaborator is None:
            raise NotFoundError(entity, identifier)


class AddMeasurementToEvaluationUseCase:
    """
    Use case for adding a competency measurement to a draft evaluation.

    Orchestration flow:

    1. Load the target evaluation.
    2. Validate that the measured competency exists in the catalog.
    3. Build the measurement value object.
    4. Attach it to the aggregate, which enforces that the evaluation is
       still a draft and that the competency was not measured yet.
    5. Persist and return the updated evaluation DTO.
    """

    def __init__(
        self,
        evaluation_repository: EvaluationRepository,
        competency_repository: CompetencyRepository,
    ) -> None:
        """
        Initialize the use case with its repository dependencies.

        Args:
            evaluation_repository: Abstraction for evaluation persistence.
            competency_repository: Abstraction used to validate the measured
                competency.
        """
        self._evaluation_repository = evaluation_repository
        self._competency_repository = competency_repository

    def execute(
        self,
        evaluation_id: EvaluationId,
        dto: MeasurementCreateDTO,
    ) -> EvaluationResponseDTO:
        """
        Add a competency measurement to a draft evaluation.

        Args:
            evaluation_id: Identifier of the draft evaluation.
            dto: Validated input describing the measured competency and the
                achieved level.

        Returns:
            The updated evaluation response DTO.

        Raises:
            NotFoundError: If the evaluation or the competency does not
                exist.
            ConflictError: If the evaluation is no longer a draft, or the
                competency was already measured in this evaluation.
            ValidationError: If the domain rejects the measurement data.
        """
        evaluation = _load_evaluation(self._evaluation_repository, evaluation_id)

        competency = self._competency_repository.get_by_id(CompetencyId(dto.competency_id))
        if competency is None:
            raise NotFoundError("Competency", dto.competency_id)

        measurement = CompetencyMeasurement(
            id=MeasurementId.generate(),
            competency_id=CompetencyId(dto.competency_id),
            current_level=dto.current_level,
            notes=dto.notes,
            evidence=dto.evidence,
        )
        try:
            evaluation.add_measurement(measurement)
        except EvaluationImmutableError as exc:
            raise ConflictError(str(exc)) from exc
        except EvaluationValidationError as exc:
            raise ConflictError(str(exc)) from exc

        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)


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
        evaluation = _load_evaluation(self._evaluation_repository, evaluation_id)

        try:
            evaluation.submit(submitted_at=datetime.now(UTC))
        except InvalidStatusTransitionError as exc:
            raise ConflictError(str(exc)) from exc
        except EvaluationValidationError as exc:
            raise ValidationError(str(exc)) from exc

        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)


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
        evaluation = _load_evaluation(self._evaluation_repository, evaluation_id)

        try:
            evaluation.accept(
                response_notes=response_notes,
                responded_at=datetime.now(UTC),
            )
        except InvalidStatusTransitionError as exc:
            raise ConflictError(str(exc)) from exc

        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)


class ContestEvaluationUseCase:
    """
    Use case for the collaborator contesting a completed evaluation.

    Orchestration flow:

    1. Load the completed evaluation.
    2. Delegate to ``Evaluation.contest``, which transitions COMPLETED to
       CONTESTED and requires non-blank contestation notes.
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
        response_notes: str,
    ) -> EvaluationResponseDTO:
        """
        Contest a completed evaluation with mandatory notes.

        Args:
            evaluation_id: Identifier of the completed evaluation.
            response_notes: Required statement explaining the contestation.

        Returns:
            The updated evaluation response DTO in CONTESTED state.

        Raises:
            NotFoundError: If the evaluation does not exist.
            ValidationError: If the contestation notes are blank.
            ConflictError: If the evaluation is not awaiting response.
        """
        evaluation = _load_evaluation(self._evaluation_repository, evaluation_id)

        try:
            evaluation.contest(
                response_notes=response_notes,
                responded_at=datetime.now(UTC),
            )
        except InvalidStatusTransitionError as exc:
            raise ConflictError(str(exc)) from exc
        except EvaluationValidationError as exc:
            raise ValidationError(str(exc)) from exc

        self._evaluation_repository.save(evaluation)
        return map_evaluation(evaluation)


def _load_evaluation(
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
