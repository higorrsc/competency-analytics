"""Evaluation aggregate root for formal competency assessments."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import cast

from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.exceptions.evaluation_errors import (
    EvaluationImmutableError,
    EvaluationValidationError,
    InvalidStatusTransitionError,
    MeasurementNotFoundError,
)
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.measurement_id import MeasurementId


@dataclass(eq=False)
class Evaluation:
    """
    Aggregate root representing a formal competency evaluation.

    Lifecycle::

        DRAFT ──submit──▶ COMPLETED ──accept──▶ ACCEPTED
                              │
                              └──contest─▶ CONTESTED

    Invariants enforced by this aggregate:

    - a new evaluation starts in ``DRAFT``;
    - measurements can only be added, changed, or removed in ``DRAFT``;
    - submitting requires at least one measurement;
    - only ``COMPLETED`` evaluations can be accepted or contested;
    - contesting requires explanatory notes;
    - ``ACCEPTED`` and ``CONTESTED`` evaluations are permanently immutable:
      no measurement, note, or status change is allowed.

    Measurements are entities inside this aggregate and are identified by
    ``MeasurementId``. Each competency may be measured at most once per
    evaluation, which keeps gap analysis deterministic.
    """

    id: EvaluationId
    collaborator_id: CollaboratorId
    evaluator_id: CollaboratorId
    period: str
    evaluation_date: datetime
    status: EvaluationStatus = EvaluationStatus.DRAFT
    measurements: list[CompetencyMeasurement] = field(default_factory=list[CompetencyMeasurement])
    submitted_at: datetime | None = None
    response_date: datetime | None = None
    response_notes: str | None = None

    def __post_init__(self) -> None:
        """Validate evaluation invariants immediately after construction."""
        self._validate_evaluation_id(self.id)
        self._validate_collaborator_id(self.collaborator_id, "collaborator_id")
        self._validate_collaborator_id(self.evaluator_id, "evaluator_id")
        self._validate_period(self.period)
        self._validate_datetime(self.evaluation_date, "evaluation_date")
        self._validate_status(self.status)
        self._validate_measurements(self.measurements)
        self._validate_optional_datetime(self.submitted_at, "submitted_at")
        self._validate_optional_datetime(self.response_date, "response_date")
        self._validate_optional_text(self.response_notes, "Response notes")
        self.period = self.period.strip()
        self.response_notes = self._normalize_text(self.response_notes)
        self._validate_lifecycle()

    @staticmethod
    def _validate_evaluation_id(evaluation_id: object) -> None:
        """
        Validate that the identity is an EvaluationId.

        Args:
            evaluation_id: Proposed evaluation identifier.

        Raises:
            EvaluationValidationError: If the value is not an EvaluationId.
        """
        if not isinstance(evaluation_id, EvaluationId):
            raise EvaluationValidationError(
                f"Evaluation id must be an EvaluationId, got {type(evaluation_id).__name__}"
            )

    @staticmethod
    def _validate_collaborator_id(value: object, field_name: str) -> None:
        """
        Validate that a collaborator reference is a CollaboratorId.

        Args:
            value: Proposed collaborator identifier.
            field_name: Field name used in the error message.

        Raises:
            EvaluationValidationError: If the value is not a CollaboratorId.
        """
        if not isinstance(value, CollaboratorId):
            raise EvaluationValidationError(
                f"{field_name} must be a CollaboratorId, got {type(value).__name__}"
            )

    @staticmethod
    def _validate_period(period: object) -> None:
        """
        Validate that the evaluation period is present and meaningful.

        Args:
            period: Proposed period label, for example ``"Q1 2026"``.

        Raises:
            EvaluationValidationError: If the period is blank.
        """
        if not isinstance(period, str) or not period.strip():
            raise EvaluationValidationError("Evaluation period must not be empty")

    @staticmethod
    def _validate_datetime(value: object, field_name: str) -> None:
        """
        Validate that a required datetime field is a datetime.

        Args:
            value: Proposed datetime value.
            field_name: Field name used in the error message.

        Raises:
            EvaluationValidationError: If the value is not a datetime.
        """
        if not isinstance(value, datetime):
            raise EvaluationValidationError(
                f"{field_name} must be a datetime, got {type(value).__name__}"
            )

    @staticmethod
    def _validate_optional_datetime(value: object, field_name: str) -> None:
        """
        Validate that an optional datetime field is a datetime or ``None``.

        Args:
            value: Proposed datetime value.
            field_name: Field name used in the error message.

        Raises:
            EvaluationValidationError: If the value is neither a datetime nor
                ``None``.
        """
        if value is not None and not isinstance(value, datetime):
            raise EvaluationValidationError(
                f"{field_name} must be a datetime or None, got {type(value).__name__}"
            )

    @staticmethod
    def _validate_status(status: object) -> None:
        """
        Validate that the status is an EvaluationStatus.

        Args:
            status: Proposed evaluation status.

        Raises:
            EvaluationValidationError: If the value is not an EvaluationStatus.
        """
        if not isinstance(status, EvaluationStatus):
            raise EvaluationValidationError(
                f"Evaluation status must be an EvaluationStatus, got {type(status).__name__}"
            )

    @staticmethod
    def _validate_measurements(measurements: object) -> None:
        """
        Validate the measurement collection and its uniqueness rules.

        Args:
            measurements: Proposed measurement list.

        Raises:
            EvaluationValidationError: If the value is not a list, contains
                non-measurement items, repeats a measurement identity, or
                repeats a competency.
        """
        if not isinstance(measurements, list):
            raise EvaluationValidationError(
                "Evaluation measurements must be a list of CompetencyMeasurement"
            )

        seen_ids: set[MeasurementId] = set()
        seen_competencies: set[CompetencyId] = set()
        for measurement in cast(list[object], measurements):
            if not isinstance(measurement, CompetencyMeasurement):
                raise EvaluationValidationError(
                    "Evaluation measurements must be CompetencyMeasurement instances"
                )
            if measurement.id in seen_ids:
                raise EvaluationValidationError(f"Duplicate measurement identity {measurement.id}")
            if measurement.competency_id in seen_competencies:
                raise EvaluationValidationError(
                    "Evaluation already contains a measurement for competency "
                    f"{measurement.competency_id}"
                )
            seen_ids.add(measurement.id)
            seen_competencies.add(measurement.competency_id)

    @staticmethod
    def _validate_optional_text(value: object, field_name: str) -> None:
        """
        Validate that an optional text field is a string or ``None``.

        Args:
            value: Proposed text value.
            field_name: Field name used in the error message.

        Raises:
            EvaluationValidationError: If the value is neither a string nor
                ``None``.
        """
        if value is not None and not isinstance(value, str):
            raise EvaluationValidationError(
                f"{field_name} must be a string or None, got {type(value).__name__}"
            )

    @staticmethod
    def _normalize_text(value: str | None) -> str | None:
        """
        Trim optional text and convert blank values to ``None``.

        Args:
            value: Text value to normalize.

        Returns:
            The trimmed text, or ``None`` when absent or blank.
        """
        if value is None:
            return None
        stripped = value.strip()
        return stripped or None

    def _validate_lifecycle(self) -> None:
        """
        Validate that status, dates, notes, and measurements are consistent.

        Raises:
            EvaluationValidationError: If the stored lifecycle data does not
                match the current status.
        """
        if self.status is EvaluationStatus.DRAFT:
            if (
                self.submitted_at is not None
                or self.response_date is not None
                or self.response_notes is not None
            ):
                raise EvaluationValidationError(
                    "Draft evaluations cannot have submission or response data"
                )
            return

        if self.submitted_at is None:
            raise EvaluationValidationError("Non-draft evaluations must have a submission date")
        if not self.measurements:
            raise EvaluationValidationError(
                "Non-draft evaluations must have at least one measurement"
            )

        if self.status is EvaluationStatus.COMPLETED:
            if self.response_date is not None or self.response_notes is not None:
                raise EvaluationValidationError("Completed evaluations cannot have response data")
            return

        if self.response_date is None:
            raise EvaluationValidationError("Finalized evaluations must have a response date")
        if self.status is EvaluationStatus.CONTESTED and self.response_notes is None:
            raise EvaluationValidationError("Contested evaluations must have contestation notes")

    def add_measurement(self, measurement: CompetencyMeasurement) -> None:
        """
        Add a competency measurement to a draft evaluation.

        Args:
            measurement: Measurement to add.

        Raises:
            EvaluationImmutableError: If the evaluation is not a draft.
            EvaluationValidationError: If the measurement identity or
                competency is already present.
        """
        self._ensure_draft()
        candidate = [*self.measurements, measurement]
        self._validate_measurements(candidate)
        self.measurements = candidate

    def update_measurement(self, measurement: CompetencyMeasurement) -> None:
        """
        Replace an existing measurement in a draft evaluation.

        The measurement identity and competency must match the stored entity;
        only level, notes, and evidence may change.

        Args:
            measurement: Updated measurement with the same identity.

        Raises:
            EvaluationImmutableError: If the evaluation is not a draft.
            MeasurementNotFoundError: If the measurement does not exist.
            EvaluationValidationError: If the competency reference changes.
        """
        self._ensure_draft()
        index = self._index_of_measurement(measurement.id)
        existing = self.measurements[index]
        if measurement.competency_id != existing.competency_id:
            raise EvaluationValidationError("Measurement competency cannot be changed")

        candidate = [*self.measurements]
        candidate[index] = measurement
        self._validate_measurements(candidate)
        self.measurements = candidate

    def remove_measurement(self, measurement_id: MeasurementId) -> None:
        """
        Remove a measurement from a draft evaluation.

        Args:
            measurement_id: Identity of the measurement to remove.

        Raises:
            EvaluationImmutableError: If the evaluation is not a draft.
            MeasurementNotFoundError: If the measurement does not exist.
        """
        self._ensure_draft()
        index = self._index_of_measurement(measurement_id)
        candidate = [*self.measurements]
        candidate.pop(index)
        self.measurements = candidate

    def find_measurement(self, competency_id: CompetencyId) -> CompetencyMeasurement | None:
        """
        Return the measurement for a competency, if present.

        Args:
            competency_id: Competency to look up.

        Returns:
            The matching measurement, or ``None`` when absent.
        """
        for measurement in self.measurements:
            if measurement.competency_id == competency_id:
                return measurement
        return None

    def find_measurement_by_id(self, measurement_id: MeasurementId) -> CompetencyMeasurement | None:
        """
        Return a measurement by identity, if present.

        Args:
            measurement_id: Measurement identity to look up.

        Returns:
            The matching measurement, or ``None`` when absent.
        """
        for measurement in self.measurements:
            if measurement.id == measurement_id:
                return measurement
        return None

    def _index_of_measurement(self, measurement_id: MeasurementId) -> int:
        """
        Return the list index of a measurement or raise when it is missing.

        Args:
            measurement_id: Measurement identity to locate.

        Returns:
            The index of the matching measurement.

        Raises:
            MeasurementNotFoundError: If no measurement has the identity.
        """
        for index, measurement in enumerate(self.measurements):
            if measurement.id == measurement_id:
                return index
        raise MeasurementNotFoundError(measurement_id)

    def submit(self, submitted_at: datetime | None = None) -> None:
        """
        Submit a draft evaluation for employee review.

        Args:
            submitted_at: Submission timestamp; defaults to the current UTC
                time.

        Raises:
            EvaluationImmutableError: If the evaluation is finalized.
            InvalidStatusTransitionError: If the evaluation is not a draft.
            EvaluationValidationError: If there are no measurements or the
                timestamp is invalid.
        """
        self._ensure_not_finalized()
        if not self.status.can_be_submitted():
            raise InvalidStatusTransitionError(self.status, EvaluationStatus.COMPLETED)
        if not self.measurements:
            raise EvaluationValidationError(
                "Evaluation must have at least one measurement to be submitted"
            )
        self._validate_optional_datetime(submitted_at, "submitted_at")
        self.status = EvaluationStatus.COMPLETED
        self.submitted_at = submitted_at or datetime.now(UTC)

    def accept(
        self,
        response_notes: str | None = None,
        responded_at: datetime | None = None,
    ) -> None:
        """
        Accept a completed evaluation, making it permanently immutable.

        Args:
            response_notes: Optional employee response notes.
            responded_at: Response timestamp; defaults to the current UTC time.

        Raises:
            EvaluationImmutableError: If the evaluation is already finalized.
            InvalidStatusTransitionError: If the evaluation is not completed.
            EvaluationValidationError: If the response data is invalid.
        """
        self._ensure_not_finalized()
        if not self.status.can_be_responded():
            raise InvalidStatusTransitionError(self.status, EvaluationStatus.ACCEPTED)
        self._validate_optional_text(response_notes, "Response notes")
        self._validate_optional_datetime(responded_at, "responded_at")
        self.status = EvaluationStatus.ACCEPTED
        self.response_date = responded_at or datetime.now(UTC)
        self.response_notes = self._normalize_text(response_notes)

    def contest(
        self,
        response_notes: str,
        responded_at: datetime | None = None,
    ) -> None:
        """
        Contest a completed evaluation, making it permanently immutable.

        Args:
            response_notes: Required explanation of the contestation.
            responded_at: Response timestamp; defaults to the current UTC time.

        Raises:
            EvaluationImmutableError: If the evaluation is already finalized.
            InvalidStatusTransitionError: If the evaluation is not completed.
            EvaluationValidationError: If the notes are missing or the
                timestamp is invalid.
        """
        self._ensure_not_finalized()
        if not self.status.can_be_responded():
            raise InvalidStatusTransitionError(self.status, EvaluationStatus.CONTESTED)
        if not isinstance(cast(object, response_notes), str) or not (response_notes.strip()):
            raise EvaluationValidationError("Contestation notes are required")
        self._validate_optional_datetime(responded_at, "responded_at")
        self.status = EvaluationStatus.CONTESTED
        self.response_date = responded_at or datetime.now(UTC)
        self.response_notes = self._normalize_text(response_notes)

    def _ensure_draft(self) -> None:
        """
        Ensure measurements may be modified.

        Raises:
            EvaluationImmutableError: If the evaluation is not a draft.
        """
        if not self.status.is_draft():
            raise EvaluationImmutableError(f"Evaluation in status {self.status.value} is immutable")

    def _ensure_not_finalized(self) -> None:
        """
        Ensure the evaluation can still change status.

        Raises:
            EvaluationImmutableError: If the evaluation is finalized.
        """
        if self.status.is_finalized():
            raise EvaluationImmutableError(
                f"Finalized evaluation in status {self.status.value} cannot be reopened or modified"
            )

    def __eq__(self, other: object) -> bool:
        """Compare evaluations by identity."""
        if not isinstance(other, Evaluation):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash evaluations by identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"Evaluation(id={self.id!r}, "
            f"collaborator_id={self.collaborator_id!r}, "
            f"period={self.period!r}, status={self.status.value}, "
            f"measurements={len(self.measurements)})"
        )
