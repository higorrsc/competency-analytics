"""Command use case for adding a competency measurement to a draft evaluation."""

from __future__ import annotations

from src.application.dto.evaluation_dtos import (
    EvaluationResponseDTO,
    MeasurementCreateDTO,
)
from src.application.use_cases.errors import (
    ConflictError,
    NotFoundError,
)
from src.application.use_cases.evaluation._helpers import load_evaluation
from src.application.use_cases.mappers import map_evaluation
from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.exceptions.evaluation_errors import (
    EvaluationImmutableError,
    EvaluationValidationError,
)
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.measurement_id import MeasurementId


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
        evaluation = load_evaluation(self._evaluation_repository, evaluation_id)

        competency = self._competency_repository.get_by_id(
            CompetencyId(dto.competency_id)
        )
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
