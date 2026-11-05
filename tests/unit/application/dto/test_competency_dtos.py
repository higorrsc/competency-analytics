"""Unit tests for competency catalog DTOs."""

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.application.dto.competency_dtos import (
    CompetencyCreateDTO,
    CompetencyResponseDTO,
)

LEVEL_DESCRIPTIONS = {1: "None", 2: "Basic", 3: "Good", 4: "Strong", 5: "Expert"}


class TestCompetencyCreateDTO:
    """Test validation of CompetencyCreateDTO."""

    def test_should_accept_valid_input(self) -> None:
        """A complete competency definition is accepted."""
        category_id = uuid4()
        group_id = uuid4()

        dto = CompetencyCreateDTO(
            name="Python",
            description="Programming language",
            category_id=category_id,
            group_id=group_id,
            level_descriptions=LEVEL_DESCRIPTIONS,
        )

        assert dto.name == "Python"
        assert dto.description == "Programming language"
        assert dto.category_id == category_id
        assert dto.group_id == group_id
        assert dto.level_descriptions == LEVEL_DESCRIPTIONS

    def test_should_trim_text_fields(self) -> None:
        """Surrounding whitespace is removed from text fields."""
        dto = CompetencyCreateDTO(
            name="  Python  ",
            description="  Programming language  ",
            category_id=uuid4(),
            group_id=uuid4(),
            level_descriptions=LEVEL_DESCRIPTIONS,
        )

        assert dto.name == "Python"
        assert dto.description == "Programming language"

    @pytest.mark.parametrize("field", ["name", "description"])
    def test_should_reject_blank_text_fields(self, field: str) -> None:
        """Blank names and descriptions are rejected."""
        data = {
            "name": "Python",
            "description": "Programming language",
            "category_id": uuid4(),
            "group_id": uuid4(),
            "level_descriptions": LEVEL_DESCRIPTIONS,
        }
        data[field] = "   "

        with pytest.raises(ValidationError, match=field):
            CompetencyCreateDTO(**data)  # type: ignore[arg-type]

    def test_should_reject_malformed_ids(self) -> None:
        """Identifiers must be valid UUIDs."""
        with pytest.raises(ValidationError, match="category_id"):
            CompetencyCreateDTO(
                name="Python",
                description="Programming language",
                category_id="not-a-uuid",
                group_id=uuid4(),
                level_descriptions=LEVEL_DESCRIPTIONS,
            )

    def test_should_reject_partial_level_descriptions(self) -> None:
        """All five levels must be described."""
        with pytest.raises(
            ValidationError,
            match="exactly one description per level",
        ):
            CompetencyCreateDTO(
                name="Python",
                description="Programming language",
                category_id=uuid4(),
                group_id=uuid4(),
                level_descriptions={1: "None", 2: "Basic", 3: "Good", 4: "Strong"},
            )

    def test_should_reject_extra_level_descriptions(self) -> None:
        """Levels outside the 1-5 scale are rejected."""
        with pytest.raises(
            ValidationError,
            match="exactly one description per level",
        ):
            CompetencyCreateDTO(
                name="Python",
                description="Programming language",
                category_id=uuid4(),
                group_id=uuid4(),
                level_descriptions={**LEVEL_DESCRIPTIONS, 6: "Beyond"},
            )

    def test_should_reject_blank_level_description(self) -> None:
        """Each level description must be present and meaningful."""
        with pytest.raises(ValidationError, match="level 3"):
            CompetencyCreateDTO(
                name="Python",
                description="Programming language",
                category_id=uuid4(),
                group_id=uuid4(),
                level_descriptions={**LEVEL_DESCRIPTIONS, 3: "  "},
            )


class TestCompetencyResponseDTO:
    """Test mapping of CompetencyResponseDTO."""

    def test_should_map_from_domain_like_attributes(self) -> None:
        """Response DTOs can be built from attribute-based objects."""
        entity = SimpleNamespace(
            id=uuid4(),
            name="Python",
            description="Programming language",
            category_id=uuid4(),
            group_id=uuid4(),
            level_descriptions=LEVEL_DESCRIPTIONS,
        )

        dto = CompetencyResponseDTO.model_validate(entity)

        assert dto.id == entity.id
        assert dto.name == "Python"
        assert dto.level_descriptions == LEVEL_DESCRIPTIONS

    def test_should_be_frozen(self) -> None:
        """Response DTOs are immutable."""
        dto = CompetencyResponseDTO(
            id=uuid4(),
            name="Python",
            description="Programming language",
            category_id=uuid4(),
            group_id=uuid4(),
            level_descriptions=LEVEL_DESCRIPTIONS,
        )

        with pytest.raises(ValidationError):
            dto.name = "Patch"  # type: ignore[misc]

    def test_should_validate_uuid_format(self) -> None:
        """Identifiers keep their UUID type."""
        dto = CompetencyResponseDTO(
            id=UUID("623e4567-e89b-12d3-a456-426614174000"),
            name="Python",
            description="Programming language",
            category_id=uuid4(),
            group_id=uuid4(),
            level_descriptions=LEVEL_DESCRIPTIONS,
        )

        assert isinstance(dto.id, UUID)
