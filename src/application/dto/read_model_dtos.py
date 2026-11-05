"""Pydantic DTOs produced by CQRS read models backed by database views."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from src.domain.value_objects.evaluation_status import EvaluationStatus


class CompetencyHistoryEntryDTO(BaseModel):
    """
    One competency measurement over time for a collaborator.

    Entries carry the previous level and its change when the collaborator was
    measured before; the very first measurement for a competency has ``None``
    for both fields and is reported as newly measured.
    """

    model_config = ConfigDict(frozen=True, from_attributes=True)

    collaborator_id: UUID
    competency_id: UUID
    competency_name: str
    evaluation_date: datetime
    period: str
    current_level: int = Field(ge=1, le=5)
    previous_level: int | None = None
    level_change: int | None = None
    status: EvaluationStatus

    @model_validator(mode="after")
    def validate_change_consistency(self) -> CompetencyHistoryEntryDTO:
        """
        Ensure previous level and level change are provided together.

        Returns:
            The validated entry.

        Raises:
            ValueError: If exactly one of ``previous_level`` and
                ``level_change`` is absent while the other is present.
        """
        has_previous = self.previous_level is not None
        has_change = self.level_change is not None
        if has_previous != has_change:
            raise ValueError(
                "previous_level and level_change must be provided together"
            )
        return self


class PathProgressionSummaryDTO(BaseModel):
    """Progress of a collaborator toward their target path level."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    collaborator_id: UUID
    path_id: UUID
    target_level: str
    total_requirements: int = Field(ge=1)
    requirements_met: int = Field(ge=0)
    completion_percentage: float = Field(ge=0.0, le=100.0)

    @model_validator(mode="after")
    def validate_progress_bounds(self) -> PathProgressionSummaryDTO:
        """
        Ensure met requirements never exceed the total.

        Returns:
            The validated summary.

        Raises:
            ValueError: If ``requirements_met`` is greater than
                ``total_requirements``.
        """
        if self.requirements_met > self.total_requirements:
            raise ValueError("requirements_met cannot exceed total_requirements")
        return self
