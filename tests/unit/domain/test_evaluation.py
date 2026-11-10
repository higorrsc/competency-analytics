"""Unit tests for the Evaluation aggregate root."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.evaluation import Evaluation
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

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
SUBMITTED_AT = datetime(2026, 4, 2, 9, 0, tzinfo=UTC)
RESPONDED_AT = datetime(2026, 4, 3, 9, 0, tzinfo=UTC)


def make_measurement(
    *,
    measurement_id: MeasurementId | None = None,
    competency_id: CompetencyId | None = None,
    current_level: int = 3,
    notes: str | None = "Strong skills",
    evidence: str | None = None,
) -> CompetencyMeasurement:
    """Build a valid CompetencyMeasurement for use in tests."""
    return CompetencyMeasurement(
        id=measurement_id or MeasurementId.generate(),
        competency_id=competency_id or CompetencyId.generate(),
        current_level=current_level,
        notes=notes,
        evidence=evidence,
    )


def make_evaluation(
    *,
    evaluation_id: EvaluationId | None = None,
    collaborator_id: CollaboratorId | None = None,
    evaluator_id: CollaboratorId | None = None,
    period: str = "Q1 2026",
    evaluation_date: datetime = EVALUATION_DATE,
    status: EvaluationStatus = EvaluationStatus.DRAFT,
    measurements: list[CompetencyMeasurement] | None = None,
    submitted_at: datetime | None = None,
    response_date: datetime | None = None,
    response_notes: str | None = None,
) -> Evaluation:
    """Build a lifecycle-consistent Evaluation for use in tests."""
    if measurements is None:
        measurements = [] if status is EvaluationStatus.DRAFT else [make_measurement()]
    if status is not EvaluationStatus.DRAFT and submitted_at is None:
        submitted_at = SUBMITTED_AT
    if status in (EvaluationStatus.ACCEPTED, EvaluationStatus.CONTESTED):
        if response_date is None:
            response_date = RESPONDED_AT
        if status is EvaluationStatus.CONTESTED and response_notes is None:
            response_notes = "Recent projects were not considered"
    return Evaluation(
        id=evaluation_id or EvaluationId.generate(),
        collaborator_id=collaborator_id or CollaboratorId.generate(),
        evaluator_id=evaluator_id or CollaboratorId.generate(),
        period=period,
        evaluation_date=evaluation_date,
        status=status,
        measurements=measurements,
        submitted_at=submitted_at,
        response_date=response_date,
        response_notes=response_notes,
    )


class TestEvaluationCreation:
    """Test creation and validation invariants of Evaluation."""

    def test_should_create_draft_evaluation_when_data_is_valid(self) -> None:
        """A valid evaluation starts as a draft."""
        evaluation_id = EvaluationId.generate()
        collaborator_id = CollaboratorId.generate()
        evaluator_id = CollaboratorId.generate()

        evaluation = make_evaluation(
            evaluation_id=evaluation_id,
            collaborator_id=collaborator_id,
            evaluator_id=evaluator_id,
        )

        assert evaluation.id == evaluation_id
        assert evaluation.collaborator_id == collaborator_id
        assert evaluation.evaluator_id == evaluator_id
        assert evaluation.period == "Q1 2026"
        assert evaluation.evaluation_date == EVALUATION_DATE
        assert evaluation.status is EvaluationStatus.DRAFT
        assert evaluation.measurements == []
        assert evaluation.submitted_at is None
        assert evaluation.response_date is None
        assert evaluation.response_notes is None

    def test_should_trim_period(self) -> None:
        """Surrounding whitespace is removed from the period."""
        evaluation = make_evaluation(period="  Q1 2026  ")

        assert evaluation.period == "Q1 2026"

    def test_should_reject_non_evaluation_id(self) -> None:
        """The identity must be an EvaluationId."""
        with pytest.raises(
            EvaluationValidationError,
            match="id must be an EvaluationId",
        ):
            make_evaluation(evaluation_id="evaluation-1")  # type: ignore[arg-type]

    def test_should_reject_non_collaborator_reference(self) -> None:
        """The collaborator reference must be a CollaboratorId."""
        with pytest.raises(
            EvaluationValidationError,
            match="collaborator_id must be a CollaboratorId",
        ):
            make_evaluation(collaborator_id="collaborator-1")  # type: ignore[arg-type]

    def test_should_reject_non_evaluator_reference(self) -> None:
        """The evaluator reference must be a CollaboratorId."""
        with pytest.raises(
            EvaluationValidationError,
            match="evaluator_id must be a CollaboratorId",
        ):
            make_evaluation(evaluator_id="evaluator-1")  # type: ignore[arg-type]

    def test_should_reject_blank_period(self) -> None:
        """A blank period violates the invariant."""
        with pytest.raises(
            EvaluationValidationError,
            match="period must not be empty",
        ):
            make_evaluation(period="   ")

    def test_should_reject_non_datetime_evaluation_date(self) -> None:
        """The evaluation date must be a datetime."""
        with pytest.raises(
            EvaluationValidationError,
            match="evaluation_date must be a datetime",
        ):
            make_evaluation(evaluation_date="2026-04-01")  # type: ignore[arg-type]

    def test_should_reject_non_status(self) -> None:
        """The status must be an EvaluationStatus."""
        with pytest.raises(
            EvaluationValidationError,
            match="status must be an EvaluationStatus",
        ):
            make_evaluation(status="DRAFT")  # type: ignore[arg-type]

    def test_should_reject_non_list_measurements(self) -> None:
        """Measurements must be provided as a list."""
        with pytest.raises(
            EvaluationValidationError,
            match="measurements must be a list",
        ):
            make_evaluation(measurements="not-a-list")  # type: ignore[arg-type]

    def test_should_reject_non_measurement_items(self) -> None:
        """Every item must be a CompetencyMeasurement."""
        with pytest.raises(
            EvaluationValidationError,
            match="must be CompetencyMeasurement instances",
        ):
            make_evaluation(measurements=["Python"])  # type: ignore[list-item]

    def test_should_reject_duplicate_measurement_identities(self) -> None:
        """Two measurements cannot share the same identity."""
        measurement_id = MeasurementId.generate()

        with pytest.raises(
            EvaluationValidationError,
            match="Duplicate measurement identity",
        ):
            make_evaluation(
                measurements=[
                    make_measurement(measurement_id=measurement_id),
                    make_measurement(measurement_id=measurement_id),
                ]
            )

    def test_should_reject_duplicate_competencies(self) -> None:
        """A competency may be measured at most once per evaluation."""
        competency_id = CompetencyId.generate()

        with pytest.raises(
            EvaluationValidationError,
            match="already contains a measurement for competency",
        ):
            make_evaluation(
                measurements=[
                    make_measurement(competency_id=competency_id),
                    make_measurement(competency_id=competency_id),
                ]
            )

    def test_should_reject_draft_with_submission_data(self) -> None:
        """Draft evaluations cannot carry submission or response data."""
        with pytest.raises(
            EvaluationValidationError,
            match="Draft evaluations cannot have submission or response data",
        ):
            make_evaluation(status=EvaluationStatus.DRAFT, submitted_at=SUBMITTED_AT)

    def test_should_reject_completed_without_submission_date(self) -> None:
        """Completed evaluations must record when they were submitted."""
        with pytest.raises(
            EvaluationValidationError,
            match="must have a submission date",
        ):
            Evaluation(
                id=EvaluationId.generate(),
                collaborator_id=CollaboratorId.generate(),
                evaluator_id=CollaboratorId.generate(),
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
                status=EvaluationStatus.COMPLETED,
                measurements=[make_measurement()],
            )

    def test_should_reject_non_draft_without_measurements(self) -> None:
        """Submitted or finalized evaluations must have measurements."""
        with pytest.raises(
            EvaluationValidationError,
            match="must have at least one measurement",
        ):
            Evaluation(
                id=EvaluationId.generate(),
                collaborator_id=CollaboratorId.generate(),
                evaluator_id=CollaboratorId.generate(),
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
                status=EvaluationStatus.COMPLETED,
                measurements=[],
                submitted_at=SUBMITTED_AT,
            )

    def test_should_reject_completed_with_response_data(self) -> None:
        """Completed evaluations cannot carry response data yet."""
        with pytest.raises(
            EvaluationValidationError,
            match="Completed evaluations cannot have response data",
        ):
            make_evaluation(
                status=EvaluationStatus.COMPLETED,
                response_date=RESPONDED_AT,
            )

    def test_should_reject_finalized_without_response_date(self) -> None:
        """Finalized evaluations must record when the employee responded."""
        with pytest.raises(
            EvaluationValidationError,
            match="Finalized evaluations must have a response date",
        ):
            Evaluation(
                id=EvaluationId.generate(),
                collaborator_id=CollaboratorId.generate(),
                evaluator_id=CollaboratorId.generate(),
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
                status=EvaluationStatus.ACCEPTED,
                measurements=[make_measurement()],
                submitted_at=SUBMITTED_AT,
            )

    def test_should_reject_contested_without_notes(self) -> None:
        """Contested evaluations must record the contestation notes."""
        with pytest.raises(
            EvaluationValidationError,
            match="Contested evaluations must have contestation notes",
        ):
            Evaluation(
                id=EvaluationId.generate(),
                collaborator_id=CollaboratorId.generate(),
                evaluator_id=CollaboratorId.generate(),
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
                status=EvaluationStatus.CONTESTED,
                measurements=[make_measurement()],
                submitted_at=SUBMITTED_AT,
                response_date=RESPONDED_AT,
            )

    def test_should_create_valid_completed_evaluation(self) -> None:
        """A lifecycle-consistent completed evaluation is accepted."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        assert evaluation.status is EvaluationStatus.COMPLETED
        assert evaluation.submitted_at == SUBMITTED_AT
        assert evaluation.response_date is None

    def test_should_create_valid_accepted_evaluation(self) -> None:
        """A lifecycle-consistent accepted evaluation is accepted."""
        evaluation = make_evaluation(status=EvaluationStatus.ACCEPTED)

        assert evaluation.status is EvaluationStatus.ACCEPTED
        assert evaluation.response_date == RESPONDED_AT

    def test_should_create_valid_contested_evaluation(self) -> None:
        """A lifecycle-consistent contested evaluation is accepted."""
        evaluation = make_evaluation(status=EvaluationStatus.CONTESTED)

        assert evaluation.status is EvaluationStatus.CONTESTED
        assert evaluation.response_notes is not None


class TestEvaluationMeasurements:
    """Test measurement management in draft evaluations."""

    def test_should_add_measurement_to_draft(self) -> None:
        """A measurement can be added while the evaluation is a draft."""
        evaluation = make_evaluation()
        measurement = make_measurement()

        evaluation.add_measurement(measurement)

        assert evaluation.measurements == [measurement]

    def test_should_reject_duplicate_measurement_identity_on_add(self) -> None:
        """Adding the same measurement identity twice is rejected."""
        measurement = make_measurement()
        evaluation = make_evaluation(measurements=[measurement])

        with pytest.raises(
            EvaluationValidationError,
            match="Duplicate measurement identity",
        ):
            evaluation.add_measurement(measurement)

    def test_should_reject_duplicate_competency_on_add(self) -> None:
        """Adding a second measurement for a competency is rejected."""
        competency_id = CompetencyId.generate()
        evaluation = make_evaluation(
            measurements=[make_measurement(competency_id=competency_id)]
        )

        with pytest.raises(
            EvaluationValidationError,
            match="already contains a measurement for competency",
        ):
            evaluation.add_measurement(make_measurement(competency_id=competency_id))

    @pytest.mark.parametrize(
        "status",
        [
            EvaluationStatus.COMPLETED,
            EvaluationStatus.ACCEPTED,
            EvaluationStatus.CONTESTED,
        ],
    )
    def test_should_block_add_measurement_after_draft(
        self, status: EvaluationStatus
    ) -> None:
        """Measurements cannot be added after the draft stage."""
        evaluation = make_evaluation(status=status)

        with pytest.raises(EvaluationImmutableError):
            evaluation.add_measurement(make_measurement())

    def test_should_update_measurement_in_draft(self) -> None:
        """A measurement can be replaced while the evaluation is a draft."""
        measurement = make_measurement(current_level=3)
        evaluation = make_evaluation(measurements=[measurement])

        evaluation.update_measurement(measurement.with_level(5))

        stored = evaluation.find_measurement_by_id(measurement.id)
        assert stored is not None
        assert stored.current_level == 5
        assert stored.id == measurement.id

    def test_should_reject_update_of_missing_measurement(self) -> None:
        """Updating a measurement that does not exist fails."""
        evaluation = make_evaluation()

        with pytest.raises(MeasurementNotFoundError):
            evaluation.update_measurement(make_measurement())

    def test_should_reject_changing_measurement_competency(self) -> None:
        """A measurement cannot be re-pointed to another competency."""
        measurement = make_measurement()
        evaluation = make_evaluation(measurements=[measurement])
        replacement = CompetencyMeasurement(
            id=measurement.id,
            competency_id=CompetencyId.generate(),
            current_level=4,
        )

        with pytest.raises(
            EvaluationValidationError,
            match="competency cannot be changed",
        ):
            evaluation.update_measurement(replacement)

    @pytest.mark.parametrize(
        "status",
        [
            EvaluationStatus.COMPLETED,
            EvaluationStatus.ACCEPTED,
            EvaluationStatus.CONTESTED,
        ],
    )
    def test_should_block_update_after_draft(self, status: EvaluationStatus) -> None:
        """Measurements cannot be updated after the draft stage."""
        measurement = make_measurement()
        evaluation = make_evaluation(status=status, measurements=[measurement])

        with pytest.raises(EvaluationImmutableError):
            evaluation.update_measurement(measurement.with_level(5))

    def test_should_remove_measurement_in_draft(self) -> None:
        """A measurement can be removed while the evaluation is a draft."""
        measurement = make_measurement()
        evaluation = make_evaluation(measurements=[measurement])

        evaluation.remove_measurement(measurement.id)

        assert evaluation.measurements == []

    def test_should_reject_removal_of_missing_measurement(self) -> None:
        """Removing a measurement that does not exist fails."""
        evaluation = make_evaluation()

        with pytest.raises(MeasurementNotFoundError):
            evaluation.remove_measurement(MeasurementId.generate())

    @pytest.mark.parametrize(
        "status",
        [
            EvaluationStatus.COMPLETED,
            EvaluationStatus.ACCEPTED,
            EvaluationStatus.CONTESTED,
        ],
    )
    def test_should_block_removal_after_draft(self, status: EvaluationStatus) -> None:
        """Measurements cannot be removed after the draft stage."""
        measurement = make_measurement()
        evaluation = make_evaluation(status=status, measurements=[measurement])

        with pytest.raises(EvaluationImmutableError):
            evaluation.remove_measurement(measurement.id)

    def test_should_find_measurement_by_competency(self) -> None:
        """A measurement can be looked up by competency."""
        competency_id = CompetencyId.generate()
        measurement = make_measurement(competency_id=competency_id)
        evaluation = make_evaluation(measurements=[measurement])

        assert evaluation.find_measurement(competency_id) == measurement
        assert evaluation.find_measurement(CompetencyId.generate()) is None

    def test_should_find_measurement_by_id(self) -> None:
        """A measurement can be looked up by identity."""
        measurement = make_measurement()
        evaluation = make_evaluation(measurements=[measurement])

        assert evaluation.find_measurement_by_id(measurement.id) == measurement
        assert evaluation.find_measurement_by_id(MeasurementId.generate()) is None


class TestEvaluationLifecycle:
    """Test submission and employee response transitions."""

    def test_should_submit_draft_with_measurements(self) -> None:
        """Submitting a draft moves it to completed and records the date."""
        evaluation = make_evaluation(measurements=[make_measurement()])

        evaluation.submit()

        assert evaluation.status is EvaluationStatus.COMPLETED
        assert evaluation.submitted_at is not None
        assert evaluation.submitted_at.tzinfo is UTC

    def test_should_submit_with_explicit_timestamp(self) -> None:
        """An explicit submission timestamp is preserved."""
        evaluation = make_evaluation(measurements=[make_measurement()])

        evaluation.submit(SUBMITTED_AT)

        assert evaluation.submitted_at == SUBMITTED_AT

    def test_should_reject_submission_without_measurements(self) -> None:
        """A draft without measurements cannot be submitted."""
        evaluation = make_evaluation()

        with pytest.raises(
            EvaluationValidationError,
            match="at least one measurement",
        ):
            evaluation.submit()

        assert evaluation.status is EvaluationStatus.DRAFT

    def test_should_reject_submission_of_completed_evaluation(self) -> None:
        """Submitting an already completed evaluation fails."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        with pytest.raises(InvalidStatusTransitionError) as error:
            evaluation.submit()

        assert error.value.current is EvaluationStatus.COMPLETED
        assert error.value.target is EvaluationStatus.COMPLETED

    @pytest.mark.parametrize(
        "status",
        [EvaluationStatus.ACCEPTED, EvaluationStatus.CONTESTED],
    )
    def test_should_block_submission_of_finalized_evaluation(
        self, status: EvaluationStatus
    ) -> None:
        """Finalized evaluations cannot be resubmitted."""
        evaluation = make_evaluation(status=status)

        with pytest.raises(EvaluationImmutableError):
            evaluation.submit()

    def test_should_accept_completed_evaluation(self) -> None:
        """Accepting moves the evaluation to accepted and records the response."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        evaluation.accept("Agreed", RESPONDED_AT)

        assert evaluation.status is EvaluationStatus.ACCEPTED
        assert evaluation.response_date == RESPONDED_AT
        assert evaluation.response_notes == "Agreed"

    def test_should_accept_without_notes(self) -> None:
        """Response notes are optional on acceptance."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        evaluation.accept()

        assert evaluation.status is EvaluationStatus.ACCEPTED
        assert evaluation.response_date is not None
        assert evaluation.response_notes is None

    def test_should_trim_response_notes_on_accept(self) -> None:
        """Response notes are normalized on acceptance."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        evaluation.accept("  Agreed  ")

        assert evaluation.response_notes == "Agreed"

    def test_should_reject_acceptance_of_draft(self) -> None:
        """Only completed evaluations can be accepted."""
        evaluation = make_evaluation()

        with pytest.raises(InvalidStatusTransitionError) as error:
            evaluation.accept()

        assert error.value.current is EvaluationStatus.DRAFT
        assert error.value.target is EvaluationStatus.ACCEPTED

    @pytest.mark.parametrize(
        "status",
        [EvaluationStatus.ACCEPTED, EvaluationStatus.CONTESTED],
    )
    def test_should_block_acceptance_of_finalized_evaluation(
        self, status: EvaluationStatus
    ) -> None:
        """Finalized evaluations cannot be accepted again."""
        evaluation = make_evaluation(status=status)

        with pytest.raises(EvaluationImmutableError):
            evaluation.accept()

    def test_should_contest_completed_evaluation(self) -> None:
        """Contesting moves the evaluation to contested and records the notes."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        evaluation.contest("Recent projects were not considered", RESPONDED_AT)

        assert evaluation.status is EvaluationStatus.CONTESTED
        assert evaluation.response_date == RESPONDED_AT
        assert evaluation.response_notes == "Recent projects were not considered"

    def test_should_trim_contestation_notes(self) -> None:
        """Contestation notes are normalized."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        evaluation.contest("  Disagree  ")

        assert evaluation.response_notes == "Disagree"

    def test_should_reject_contestation_of_draft(self) -> None:
        """Only completed evaluations can be contested."""
        evaluation = make_evaluation()

        with pytest.raises(InvalidStatusTransitionError) as error:
            evaluation.contest("Disagree")

        assert error.value.current is EvaluationStatus.DRAFT
        assert error.value.target is EvaluationStatus.CONTESTED

    @pytest.mark.parametrize("notes", ["", "   "])
    def test_should_reject_contestation_without_notes(self, notes: str) -> None:
        """Contesting requires explanatory notes."""
        evaluation = make_evaluation(status=EvaluationStatus.COMPLETED)

        with pytest.raises(
            EvaluationValidationError,
            match="Contestation notes are required",
        ):
            evaluation.contest(notes)

        assert evaluation.status is EvaluationStatus.COMPLETED

    @pytest.mark.parametrize(
        "status",
        [EvaluationStatus.ACCEPTED, EvaluationStatus.CONTESTED],
    )
    def test_should_block_contestation_of_finalized_evaluation(
        self, status: EvaluationStatus
    ) -> None:
        """Finalized evaluations cannot be contested again."""
        evaluation = make_evaluation(status=status)

        with pytest.raises(EvaluationImmutableError):
            evaluation.contest("Disagree again")

    @pytest.mark.parametrize(
        "status",
        [EvaluationStatus.ACCEPTED, EvaluationStatus.CONTESTED],
    )
    def test_should_block_every_modification_after_finalization(
        self, status: EvaluationStatus
    ) -> None:
        """Finalized evaluations reject every modification operation."""
        measurement = make_measurement()
        evaluation = make_evaluation(status=status, measurements=[measurement])

        with pytest.raises(EvaluationImmutableError):
            evaluation.add_measurement(make_measurement())
        with pytest.raises(EvaluationImmutableError):
            evaluation.update_measurement(measurement.with_level(5))
        with pytest.raises(EvaluationImmutableError):
            evaluation.remove_measurement(measurement.id)
        with pytest.raises(EvaluationImmutableError):
            evaluation.submit()
        with pytest.raises(EvaluationImmutableError):
            evaluation.accept()
        with pytest.raises(EvaluationImmutableError):
            evaluation.contest("Disagree")


class TestEvaluationIdentity:
    """Test identity semantics of Evaluation."""

    def test_should_be_equal_when_ids_match(self) -> None:
        """Identity is based on the evaluation identifier."""
        evaluation_id = EvaluationId.generate()
        first = make_evaluation(evaluation_id=evaluation_id, period="Q1 2026")
        second = make_evaluation(evaluation_id=evaluation_id, period="Q2 2026")

        assert first == second
        assert hash(first) == hash(second)

    def test_should_differ_when_ids_differ(self) -> None:
        """Different identifiers mean different evaluations."""
        assert make_evaluation() != make_evaluation()

    def test_should_not_equal_other_types(self) -> None:
        """Comparison against unrelated types is not supported."""
        assert make_evaluation() != "Q1 2026"

    def test_should_provide_repr(self) -> None:
        """The representation identifies the evaluation."""
        evaluation = make_evaluation(period="Q1 2026")

        representation = repr(evaluation)

        assert "Evaluation(" in representation
        assert "Q1 2026" in representation
        assert "DRAFT" in representation
