"""Output response DTOs for the career path application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from src.domain.value_objects.requirement_weight import RequirementWeight


class RequirementResponseDTO(BaseModel):
    """Output contract exposing a stored competency requirement."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    competency_id: UUID
    minimum_level: int
    weight: RequirementWeight


class LevelResponseDTO(BaseModel):
    """Output contract exposing a stored career path level."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    order: int
    requirements: list[RequirementResponseDTO]


class PathResponseDTO(BaseModel):
    """Output contract exposing a stored career path."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    description: str
    levels: list[LevelResponseDTO]
