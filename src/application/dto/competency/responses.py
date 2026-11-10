"""Output response DTOs for the competency catalog application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CompetencyResponseDTO(BaseModel):
    """Output contract exposing a stored competency."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    description: str
    category_id: UUID
    group_id: UUID
    level_descriptions: dict[int, str]
