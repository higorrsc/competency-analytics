"""Output response DTOs for the evaluation application boundary."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.value_objects.evaluation_status import EvaluationStatus


class MeasurementDTO(BaseModel):
    """Output contract exposing a stored competency measurement."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    competency_id: UUID
    current_level: int
    notes: str | None = None
    evidence: str | None = None


class EvaluationResponseDTO(BaseModel):
    """Output contract exposing a stored evaluation and its measurements."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    collaborator_id: UUID
    evaluator_id: UUID
    period: str
    evaluation_date: datetime
    status: EvaluationStatus
    measurements: list[MeasurementDTO] = Field(default_factory=list[MeasurementDTO])
    submitted_at: datetime | None = None
    response_date: datetime | None = None
    response_notes: str | None = None
