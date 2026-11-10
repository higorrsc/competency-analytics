"""CompetencyMeasurement entity belonging to an evaluation aggregate."""

from __future__ import annotations

from dataclasses import dataclass, replace

from src.domain.exceptions.evaluation_errors import EvaluationValidationError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.measurement_id import MeasurementId
from src.domain.value_objects.proficiency_level import VALID_LEVELS, is_valid_level


@dataclass(frozen=True, eq=False)
class CompetencyMeasurement:
    """
    A single competency measurement inside an evaluation.

    A measurement records the assessed proficiency level for a competency,
    together with optional supporting notes and evidence. Measurements are
    immutable: changing a level, note, or evidence returns a new instance.
    The owning ``Evaluation`` replaces the stored measurement, which lets it
    enforce draft-only modification and finalization rules centrally.

    Identity is based on ``id`` only, so the same measurement can evolve while
    remaining the same entity inside the aggregate.
    """

    id: MeasurementId
    competency_id: CompetencyId
    current_level: int
    notes: str | None = None
    evidence: str | None = None

    def __post_init__(self) -> None:
        """Validate measurement invariants after construction."""
        self._validate_id(self.id)
        self._validate_competency_id(self.competency_id)
        self._validate_level(self.current_level)
        self._validate_optional_text(self.notes, "Notes")
        self._validate_optional_text(self.evidence, "Evidence")
        object.__setattr__(self, "notes", self._normalize_text(self.notes))
        object.__setattr__(self, "evidence", self._normalize_text(self.evidence))

    @staticmethod
    def _validate_id(measurement_id: object) -> None:
        """
        Validate that the identity is a MeasurementId.

        Args:
            measurement_id: Proposed measurement identifier.

        Raises:
            EvaluationValidationError: If the value is not a MeasurementId.
        """
        if not isinstance(measurement_id, MeasurementId):
            raise EvaluationValidationError(
                f"Measurement id must be a MeasurementId, got "
                f"{type(measurement_id).__name__}"
            )

    @staticmethod
    def _validate_competency_id(competency_id: object) -> None:
        """
        Validate that the measured competency reference is a CompetencyId.

        Args:
            competency_id: Proposed competency identifier.

        Raises:
            EvaluationValidationError: If the value is not a CompetencyId.
        """
        if not isinstance(competency_id, CompetencyId):
            raise EvaluationValidationError(
                "Measurement competency_id must be a CompetencyId, "
                f"got {type(competency_id).__name__}"
            )

    @staticmethod
    def _validate_level(level: object) -> None:
        """
        Validate that the measured level belongs to the 1-5 scale.

        Args:
            level: Proposed proficiency level.

        Raises:
            EvaluationValidationError: If the level is not an integer between
                1 and 5.
        """
        if not is_valid_level(level):
            raise EvaluationValidationError(
                f"Measurement level must be one of {sorted(VALID_LEVELS)}, "
                f"got {level!r}"
            )

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

    def with_level(self, level: int) -> CompetencyMeasurement:
        """
        Return a copy of the measurement with a different level.

        Args:
            level: New proficiency level between 1 and 5.

        Returns:
            A new measurement with the given level.

        Raises:
            EvaluationValidationError: If the level is outside the 1-5 scale.
        """
        self._validate_level(level)
        return replace(self, current_level=level)

    def with_notes(self, notes: str | None) -> CompetencyMeasurement:
        """
        Return a copy of the measurement with different notes.

        Args:
            notes: New notes, or ``None`` to clear them.

        Returns:
            A new measurement with the given notes.

        Raises:
            EvaluationValidationError: If notes are not a string or ``None``.
        """
        self._validate_optional_text(notes, "Notes")
        return replace(self, notes=self._normalize_text(notes))

    def with_evidence(self, evidence: str | None) -> CompetencyMeasurement:
        """
        Return a copy of the measurement with different evidence.

        Args:
            evidence: New evidence, or ``None`` to clear it.

        Returns:
            A new measurement with the given evidence.

        Raises:
            EvaluationValidationError: If evidence is not a string or ``None``.
        """
        self._validate_optional_text(evidence, "Evidence")
        return replace(self, evidence=self._normalize_text(evidence))

    def __eq__(self, other: object) -> bool:
        """Compare measurements by identity."""
        if not isinstance(other, CompetencyMeasurement):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash measurements by identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"CompetencyMeasurement(id={self.id!r}, "
            f"competency_id={self.competency_id!r}, "
            f"current_level={self.current_level})"
        )
