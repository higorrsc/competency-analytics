"""Unit tests for the CompetencyMeasurement entity."""

import pytest

from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.exceptions.evaluation_errors import EvaluationValidationError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.measurement_id import MeasurementId


def make_measurement(
    *,
    measurement_id: MeasurementId | None = None,
    competency_id: CompetencyId | None = None,
    current_level: int = 3,
    notes: str | None = "Strong backend skills",
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


class TestCompetencyMeasurementCreation:
    """Test creation and validation invariants of CompetencyMeasurement."""

    def test_should_create_measurement_when_data_is_valid(self) -> None:
        """A valid measurement keeps all of its data."""
        measurement_id = MeasurementId.generate()
        competency_id = CompetencyId.generate()

        measurement = make_measurement(
            measurement_id=measurement_id,
            competency_id=competency_id,
            current_level=4,
            notes="Strong backend skills",
            evidence="https://example.com/evidence",
        )

        assert measurement.id == measurement_id
        assert measurement.competency_id == competency_id
        assert measurement.current_level == 4
        assert measurement.notes == "Strong backend skills"
        assert measurement.evidence == "https://example.com/evidence"

    def test_should_allow_missing_notes_and_evidence(self) -> None:
        """Notes and evidence are optional."""
        measurement = make_measurement(notes=None, evidence=None)

        assert measurement.notes is None
        assert measurement.evidence is None

    def test_should_trim_notes_and_evidence(self) -> None:
        """Surrounding whitespace is removed from text fields."""
        measurement = make_measurement(
            notes="  Strong skills  ",
            evidence="  https://example.com  ",
        )

        assert measurement.notes == "Strong skills"
        assert measurement.evidence == "https://example.com"

    def test_should_convert_blank_text_to_none(self) -> None:
        """Blank notes and evidence are stored as absent."""
        measurement = make_measurement(notes="   ", evidence="   ")

        assert measurement.notes is None
        assert measurement.evidence is None

    def test_should_reject_non_measurement_id(self) -> None:
        """The identity must be a MeasurementId."""
        with pytest.raises(
            EvaluationValidationError,
            match="id must be a MeasurementId",
        ):
            make_measurement(measurement_id="measurement-1")  # type: ignore[arg-type]

    def test_should_reject_non_competency_id(self) -> None:
        """The competency reference must be a CompetencyId."""
        with pytest.raises(
            EvaluationValidationError,
            match="competency_id must be a CompetencyId",
        ):
            make_measurement(competency_id="python")  # type: ignore[arg-type]

    @pytest.mark.parametrize("level", [0, 6, -1])
    def test_should_reject_level_outside_scale(self, level: int) -> None:
        """Levels outside 1-5 are rejected."""
        with pytest.raises(
            EvaluationValidationError,
            match="Measurement level must be one of",
        ):
            make_measurement(current_level=level)

    def test_should_reject_boolean_level(self) -> None:
        """Booleans are rejected despite subclassing int."""
        with pytest.raises(
            EvaluationValidationError,
            match="Measurement level must be one of",
        ):
            make_measurement(current_level=True)  # type: ignore[arg-type]

    def test_should_reject_non_string_notes(self) -> None:
        """Notes must be a string or None."""
        with pytest.raises(
            EvaluationValidationError,
            match="Notes must be a string or None",
        ):
            make_measurement(notes=42)  # type: ignore[arg-type]

    def test_should_reject_non_string_evidence(self) -> None:
        """Evidence must be a string or None."""
        with pytest.raises(
            EvaluationValidationError,
            match="Evidence must be a string or None",
        ):
            make_measurement(evidence=42)  # type: ignore[arg-type]

    def test_should_be_immutable(self) -> None:
        """Measurements are frozen entities."""
        measurement = make_measurement()

        with pytest.raises(AttributeError):
            measurement.current_level = 5  # type: ignore[misc]


class TestCompetencyMeasurementChanges:
    """Test immutable changes to level, notes, and evidence."""

    def test_should_change_level_returning_a_new_instance(self) -> None:
        """Changing the level preserves identity and other fields."""
        measurement = make_measurement(current_level=3)

        updated = measurement.with_level(5)

        assert updated.current_level == 5
        assert updated.id == measurement.id
        assert updated.notes == measurement.notes
        assert measurement.current_level == 3

    def test_should_reject_invalid_level_on_change(self) -> None:
        """Changing to a level outside 1-5 fails."""
        measurement = make_measurement()

        with pytest.raises(
            EvaluationValidationError,
            match="Measurement level must be one of",
        ):
            measurement.with_level(6)

    def test_should_change_notes_returning_a_new_instance(self) -> None:
        """Notes can be replaced and cleared."""
        measurement = make_measurement(notes="Old notes")

        updated = measurement.with_notes("New notes")
        cleared = measurement.with_notes(None)

        assert updated.notes == "New notes"
        assert cleared.notes is None
        assert measurement.notes == "Old notes"

    def test_should_change_evidence_returning_a_new_instance(self) -> None:
        """Evidence can be replaced and cleared."""
        measurement = make_measurement(evidence="Old evidence")

        updated = measurement.with_evidence("New evidence")
        cleared = measurement.with_evidence(None)

        assert updated.evidence == "New evidence"
        assert cleared.evidence is None
        assert measurement.evidence == "Old evidence"


class TestCompetencyMeasurementIdentity:
    """Test identity semantics of CompetencyMeasurement."""

    def test_should_be_equal_when_ids_match(self) -> None:
        """Identity is based on the measurement identifier."""
        measurement_id = MeasurementId.generate()
        first = make_measurement(measurement_id=measurement_id, current_level=3)
        second = make_measurement(measurement_id=measurement_id, current_level=5)

        assert first == second
        assert hash(first) == hash(second)

    def test_should_differ_when_ids_differ(self) -> None:
        """Different identifiers mean different measurements."""
        assert make_measurement() != make_measurement()

    def test_should_not_equal_other_types(self) -> None:
        """Comparison against unrelated types is not supported."""
        assert make_measurement() != "Python"

    def test_should_provide_repr(self) -> None:
        """The representation identifies the measurement."""
        measurement = make_measurement(current_level=4)

        representation = repr(measurement)

        assert "CompetencyMeasurement(" in representation
        assert "current_level=4" in representation
