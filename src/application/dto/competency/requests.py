"""Input request DTOs for the competency catalog application boundary."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

from src.domain.value_objects.proficiency_level import VALID_LEVELS


class CompetencyCreateDTO(BaseModel):
    """Input contract for creating a competency in the catalog."""

    model_config = ConfigDict(frozen=True)

    name: str
    description: str
    category_id: UUID
    group_id: UUID
    level_descriptions: dict[int, str]

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        """
        Ensure the competency name is present and meaningful.

        Args:
            value: Proposed competency name.

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
        Ensure the competency description is present and meaningful.

        Args:
            value: Proposed competency description.

        Returns:
            The trimmed description.

        Raises:
            ValueError: If the description is empty or whitespace only.
        """
        stripped = value.strip()
        if not stripped:
            raise ValueError("description must not be empty")
        return stripped

    @field_validator("level_descriptions")
    @classmethod
    def validate_level_descriptions(cls, value: dict[int, str]) -> dict[int, str]:
        """
        Ensure every proficiency level has a non-blank description.

        Args:
            value: Mapping from proficiency level to description.

        Returns:
            The validated mapping.

        Raises:
            ValueError: If the mapping does not cover exactly the 1-5 scale
                or any description is blank.
        """
        if set(value) != set(VALID_LEVELS):
            raise ValueError(
                f"level_descriptions must define exactly one description per "
                f"level {sorted(VALID_LEVELS)}"
            )
        for level, description in value.items():
            if not description.strip():
                raise ValueError(f"description for level {level} must not be empty")
        return value
