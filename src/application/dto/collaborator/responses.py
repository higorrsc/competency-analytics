"""Output response DTOs for the collaborator application boundary."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class EnrollmentDTO(BaseModel):
    """Output contract exposing a stored path enrollment."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    path_id: UUID
    target_level: str
    enrolled_at: datetime
    is_active: bool


class CollaboratorResponseDTO(BaseModel):
    """Output contract exposing a stored collaborator and enrollments."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    email: str
    department: str
    enrollments: list[EnrollmentDTO] = Field(default_factory=list[EnrollmentDTO])
