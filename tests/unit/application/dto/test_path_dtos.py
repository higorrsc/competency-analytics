"""Unit tests for career path DTOs."""

from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from pydantic import ValidationError

from src.application.dto.path_dtos import (
    LevelCreateDTO,
    LevelResponseDTO,
    PathCreateDTO,
    PathResponseDTO,
    RequirementCreateDTO,
    RequirementResponseDTO,
)


class TestRequirementDTOs:
    """Test validation of requirement DTOs."""

    def test_should_accept_valid_requirement(self) -> None:
        """A requirement within the level scale is accepted."""
        competency_id = uuid4()

        dto = RequirementCreateDTO(competency_id=competency_id, minimum_level=4, weight="CORE")

        assert dto.competency_id == competency_id
        assert dto.minimum_level == 4
        assert dto.weight.value == "CORE"

    @pytest.mark.parametrize("level", [0, 6, -1])
    def test_should_reject_minimum_level_outside_scale(self, level: int) -> None:
        """Minimum levels must be between 1 and 5."""
        with pytest.raises(ValidationError, match="minimum_level"):
            RequirementCreateDTO(competency_id=uuid4(), minimum_level=level, weight="CORE")

    def test_should_reject_unknown_weight(self) -> None:
        """Weights must be one of the supported values."""
        with pytest.raises(ValidationError, match="weight"):
            RequirementCreateDTO(competency_id=uuid4(), minimum_level=4, weight="ESSENTIAL")

    def test_should_map_requirement_response(self) -> None:
        """Response DTOs can be built from attribute-based objects."""
        entity = SimpleNamespace(competency_id=uuid4(), minimum_level=3, weight="IMPORTANT")

        dto = RequirementResponseDTO.model_validate(entity)

        assert dto.competency_id == entity.competency_id
        assert dto.weight.value == "IMPORTANT"


class TestLevelDTOs:
    """Test validation of level DTOs."""

    def test_should_accept_valid_level(self) -> None:
        """A level with requirements is accepted."""
        requirement = RequirementCreateDTO(competency_id=uuid4(), minimum_level=4, weight="CORE")

        dto = LevelCreateDTO(name="Senior", order=3, requirements=[requirement])

        assert dto.name == "Senior"
        assert dto.order == 3
        assert dto.requirements == [requirement]

    def test_should_default_requirements_to_empty(self) -> None:
        """Levels may be created without requirements."""
        dto = LevelCreateDTO(name="Junior", order=1)

        assert dto.requirements == []

    def test_should_reject_blank_name(self) -> None:
        """Blank level names are rejected."""
        with pytest.raises(ValidationError, match="name"):
            LevelCreateDTO(name="   ", order=1)

    def test_should_reject_non_positive_order(self) -> None:
        """Level orders start at 1."""
        with pytest.raises(ValidationError, match="order"):
            LevelCreateDTO(name="Senior", order=0)

    def test_should_map_level_response(self) -> None:
        """Response DTOs nest requirement DTOs from attributes."""
        requirement = SimpleNamespace(competency_id=uuid4(), minimum_level=4, weight="CORE")
        entity = SimpleNamespace(id=uuid4(), name="Senior", order=3, requirements=[requirement])

        dto = LevelResponseDTO.model_validate(entity)

        assert dto.id == entity.id
        assert dto.requirements[0].minimum_level == 4


class TestPathDTOs:
    """Test validation of path DTOs."""

    def test_should_accept_valid_path(self) -> None:
        """A path with ordered levels is accepted."""
        dto = PathCreateDTO(
            name="Software Engineer Track",
            description="Engineering progression",
            levels=[
                LevelCreateDTO(name="Junior", order=1),
                LevelCreateDTO(name="Senior", order=2),
            ],
        )

        assert dto.name == "Software Engineer Track"
        assert len(dto.levels) == 2
        assert dto.levels[0].order == 1

    def test_should_default_levels_to_empty(self) -> None:
        """Paths may be created without levels."""
        dto = PathCreateDTO(name="Track", description="Description")

        assert dto.levels == []

    @pytest.mark.parametrize("field", ["name", "description"])
    def test_should_reject_blank_text_fields(self, field: str) -> None:
        """Blank names and descriptions are rejected."""
        data = {"name": "Track", "description": "Description"}
        data[field] = "   "

        with pytest.raises(ValidationError, match=field):
            PathCreateDTO(**data)  # type: ignore[arg-type]

    def test_should_map_path_response(self) -> None:
        """Response DTOs nest level and requirement DTOs from attributes."""
        requirement = SimpleNamespace(competency_id=uuid4(), minimum_level=4, weight="DESIRABLE")
        level = SimpleNamespace(id=uuid4(), name="Senior", order=3, requirements=[requirement])
        entity = SimpleNamespace(
            id=uuid4(),
            name="Software Engineer Track",
            description="Description",
            levels=[level],
        )

        dto = PathResponseDTO.model_validate(entity)

        assert dto.levels[0].requirements[0].weight.value == "DESIRABLE"

    def test_should_preserve_types_after_mapping(self) -> None:
        """Mapped identifiers stay UUIDs."""
        path_id = uuid4()
        dto = PathResponseDTO(
            id=path_id,
            name="Track",
            description="Description",
            levels=[LevelResponseDTO(id=uuid4(), name="Junior", order=1, requirements=[])],
        )

        assert dto.id == path_id
        assert isinstance(dto.levels[0].id, UUID)
