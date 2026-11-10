"""Input request DTOs for the evaluation application boundary."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class MeasurementCreateDTO(BaseModel):
    """Input contract for a competency measurement inside an evaluation."""

    model_config = ConfigDict(frozen=True)

    competency_id: UUID
    current_level: int = Field(ge=1, le=5)
    notes: str | None = None
    evidence: str | None = None

    @field_validator("notes")
    @classmethod
    def validate_notes(cls, value: str | None) -> str | None:
        """
        Ensure optional notes are non-blank when provided.

        Args:
            value: Proposed notes.

        Returns:
            The trimmed notes, or ``None``.

        Raises:
            ValueError: If the notes are empty after trimming.
        """
        if value is not None and not value.strip():
            raise ValueError("notes must not be empty")
        return None if value is None else value.strip()

    @field_validator("evidence")
    @classmethod
    def validate_evidence(cls, value: str | None) -> str | None:
        """
        Ensure optional evidence is non-blank when provided.

        Args:
            value: Proposed evidence.

        Returns:
            The trimmed evidence, or ``None``.

        Raises:
            ValueError: If the evidence is empty after trimming.
        """
        if value is not None and not value.strip():
            raise ValueError("evidence must not be empty")
        return None if value is None else value.strip()


class EvaluationCreateDTO(BaseModel):
    """Input contract for creating an evaluation in draft state."""

    model_config = ConfigDict(frozen=True)

    collaborator_id: UUID
    evaluator_id: UUID
    period: str
    evaluation_date: datetime

    @field_validator("period")
    @classmethod
    def validate_period(cls, value: str) -> str:
        """
        Ensure the evaluation period is present and meaningful.

        Args:
            value: Proposed period label, for example ``"Q1 2026"``.

        Returns:
            The trimmed period.

        Raises:
            ValueError: If the period is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("period must not be empty")
        return stripped
