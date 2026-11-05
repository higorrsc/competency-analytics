"""Pydantic DTOs for the gap analysis application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.domain.value_objects.requirement_weight import RequirementWeight


class GapAnalysisRequestDTO(BaseModel):
    """
    Input contract for requesting gap analysis.

    The target level is explicit, so callers may analyze any path level, not
    only the collaborator's currently enrolled target.
    """

    model_config = ConfigDict(frozen=True)

    collaborator_id: UUID
    path_id: UUID
    level_id: UUID


class CompetencyGapDTO(BaseModel):
    """Output contract exposing a single competency gap."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    competency_id: UUID
    current_level: int = Field(ge=0, le=5)
    required_level: int = Field(ge=1, le=5)
    gap: int = Field(ge=0)
    weight: RequirementWeight


class ProgressionEligibilityDTO(BaseModel):
    """Output contract exposing progression eligibility."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    is_eligible: bool
    blocking_competency_ids: list[UUID] = Field(default_factory=list[UUID])


class GapAnalysisResponseDTO(BaseModel):
    """Output contract exposing prioritized gaps and eligibility."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    gaps: list[CompetencyGapDTO] = Field(default_factory=list[CompetencyGapDTO])
    eligibility: ProgressionEligibilityDTO
