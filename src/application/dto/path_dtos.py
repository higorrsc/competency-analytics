"""Pydantic DTOs for the career path application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from src.domain.value_objects.requirement_weight import RequirementWeight


class RequirementCreateDTO(BaseModel):
    """Input contract for a competency requirement attached to a level."""

    model_config = ConfigDict(frozen=True)

    competency_id: UUID
    minimum_level: int = Field(ge=1, le=5)
    weight: RequirementWeight


class RequirementResponseDTO(BaseModel):
    """Output contract exposing a stored competency requirement."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    competency_id: UUID
    minimum_level: int
    weight: RequirementWeight


class LevelCreateDTO(BaseModel):
    """Input contract for a career path level."""

    model_config = ConfigDict(frozen=True)

    name: str
    order: int = Field(ge=1)
    requirements: list[RequirementCreateDTO] = Field(default_factory=list[RequirementCreateDTO])

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Ensure the level name is present and meaningful.

        Args:
            value: Proposed level name.

        Returns:
            The trimmed name.

        Raises:
            ValueError: If the name is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped


class LevelResponseDTO(BaseModel):
    """Output contract exposing a stored career path level."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    order: int
    requirements: list[RequirementResponseDTO]


class PathCreateDTO(BaseModel):
    """Input contract for creating a career path."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    levels: list[LevelCreateDTO] = Field(default_factory=list[LevelCreateDTO])

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Ensure the path name is present and meaningful.

        Args:
            value: Proposed path name.

        Returns:
            The trimmed name.

        Raises:
            ValueError: If the name is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("name must not be empty")
        return stripped

    @field_validator("description")
    @classmethod
    def validate_description(cls, value: str) -> str:
        """
        Ensure the path description is present and meaningful.

        Args:
            value: Proposed path description.

        Returns:
            The trimmed description.

        Raises:
            ValueError: If the description is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("description must not be empty")
        return stripped


class PathResponseDTO(BaseModel):
    """Output contract exposing a stored career path."""

    model_config = ConfigDict(frozen=True, from_attributes=True)

    id: UUID
    name: str
    description: str
    levels: list[LevelResponseDTO]
