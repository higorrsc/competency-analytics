"""Unit tests for evaluation DTOs."""

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.application.dto.evaluation_dtos import (
    EvaluationCreateDTO,
    EvaluationResponseDTO,
    MeasurementCreateDTO,
)

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
SUBMITTED_AT = datetime(2026, 4, 2, 9, 0, tzinfo=UTC)
RESPONDED_AT = datetime(2026, 4, 3, 9, 0, tzinfo=UTC)


class TestMeasurementCreateDTO:
    """Test validation of MeasurementCreateDTO."""

    def test_should_accept_valid_measurement(self) -> None:
        """A measurement within the level scale is accepted."""
        competency_id = uuid4()

        dto = MeasurementCreateDTO(
            competency_id=competency_id,
            current_level=4,
            notes="Strong skills",
            evidence="https://example.com",
        )

        assert dto.competency_id == competency_id
        assert dto.current_level == 4
        assert dto.notes == "Strong skills"

    @pytest.mark.parametrize("level", [0, 6, -1])
    def test_should_reject_level_outside_scale(self, level: int) -> None:
        """Measurement levels must be between 1 and 5."""
        with pytest.raises(ValidationError, match="current_level"):
            MeasurementCreateDTO(competency_id=uuid4(), current_level=level)

    def test_should_trim_text_fields(self) -> None:
        """Surrounding whitespace is removed from optional texts."""
        dto = MeasurementCreateDTO(
            competency_id=uuid4(),
            current_level=3,
            notes="  Strong skills  ",
            evidence="  https://example.com  ",
        )

        assert dto.notes == "Strong skills"
        assert dto.evidence == "https://example.com"

    def test_should_allow_missing_notes_and_evidence(self) -> None:
        """Notes and evidence are optional."""
        dto = MeasurementCreateDTO(competency_id=uuid4(), current_level=3)

        assert dto.notes is None
        assert dto.evidence is None

    @pytest.mark.parametrize("field", ["notes", "evidence"])
    def test_should_reject_blank_optional_text(self, field: str) -> None:
        """Optional texts must not be blank when provided."""
        with pytest.raises(ValidationError, match=field):
            MeasurementCreateDTO(
                competency_id=uuid4(), current_level=3, **{field: "   "}
            )


class TestEvaluationCreateDTO:
    """Test validation of EvaluationCreateDTO."""

    def test_should_accept_valid_evaluation(self) -> None:
        """A complete evaluation draft is accepted."""
        collaborator_id = uuid4()
        evaluator_id = uuid4()

        dto = EvaluationCreateDTO(
            collaborator_id=collaborator_id,
            evaluator_id=evaluator_id,
            period="Q1 2026",
            evaluation_date=EVALUATION_DATE,
        )

        assert dto.collaborator_id == collaborator_id
        assert dto.evaluator_id == evaluator_id
        assert dto.period == "Q1 2026"
        assert dto.evaluation_date == EVALUATION_DATE

    def test_should_trim_period(self) -> None:
        """Surrounding whitespace is removed from the period."""
        dto = EvaluationCreateDTO(
            collaborator_id=uuid4(),
            evaluator_id=uuid4(),
            period="  Q1 2026  ",
            evaluation_date=EVALUATION_DATE,
        )

        assert dto.period == "Q1 2026"

    def test_should_reject_blank_period(self) -> None:
        """A blank period is rejected."""
        with pytest.raises(ValidationError, match="period"):
            EvaluationCreateDTO(
                collaborator_id=uuid4(),
                evaluator_id=uuid4(),
                period="   ",
                evaluation_date=EVALUATION_DATE,
            )

    def test_should_reject_invalid_date(self) -> None:
        """The evaluation date must be a valid datetime."""
        with pytest.raises(ValidationError, match="evaluation_date"):
            EvaluationCreateDTO(
                collaborator_id=uuid4(),
                evaluator_id=uuid4(),
                period="Q1 2026",
                evaluation_date="not-a-date",
            )


class TestEvaluationResponseDTO:
    """Test mapping of EvaluationResponseDTO."""

    def test_should_map_evaluation_with_measurements(self) -> None:
        """Response DTOs nest measurement DTOs from attributes."""
        measurement = SimpleNamespace(
            id=uuid4(),
            competency_id=uuid4(),
            current_level=4,
            notes="Strong skills",
            evidence=None,
        )
        entity = SimpleNamespace(
            id=uuid4(),
            collaborator_id=uuid4(),
            evaluator_id=uuid4(),
            period="Q1 2026",
            evaluation_date=EVALUATION_DATE,
            status="COMPLETED",
            measurements=[measurement],
            submitted_at=SUBMITTED_AT,
            response_date=None,
            response_notes=None,
        )

        dto = EvaluationResponseDTO.model_validate(entity)

        assert dto.status.value == "COMPLETED"
        assert dto.measurements[0].current_level == 4
        assert dto.submitted_at == SUBMITTED_AT

    def test_should_map_finalized_evaluation(self) -> None:
        """Accepted evaluations carry response data."""
        entity = SimpleNamespace(
            id=uuid4(),
            collaborator_id=uuid4(),
            evaluator_id=uuid4(),
            period="Q1 2026",
            evaluation_date=EVALUATION_DATE,
            status="ACCEPTED",
            measurements=[],
            submitted_at=SUBMITTED_AT,
            response_date=RESPONDED_AT,
            response_notes="Agreed",
        )

        dto = EvaluationResponseDTO.model_validate(entity)

        assert dto.status.value == "ACCEPTED"
        assert dto.response_notes == "Agreed"

    def test_should_reject_unknown_status(self) -> None:
        """Statuses must be supported lifecycle values."""
        with pytest.raises(ValidationError, match="status"):
            EvaluationResponseDTO(
                id=uuid4(),
                collaborator_id=uuid4(),
                evaluator_id=uuid4(),
                period="Q1 2026",
                evaluation_date=EVALUATION_DATE,
                status="CANCELLED",
                measurements=[],
            )
