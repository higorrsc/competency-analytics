"""Unit tests for the CompetencyRequirement value object."""

import pytest

from src.domain.exceptions.path_errors import CompetencyPathValidationError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.requirement_weight import RequirementWeight


def make_requirement(
    *,
    competency_id: CompetencyId | None = None,
    minimum_level: int = 3,
    weight: RequirementWeight = RequirementWeight.CORE,
) -> CompetencyRequirement:
    """Build a valid CompetencyRequirement for use in tests."""
    return CompetencyRequirement(
        competency_id=competency_id or CompetencyId.generate(),
        minimum_level=minimum_level,
        weight=weight,
    )


class TestCompetencyRequirementCreation:
    """Test creation and validation of CompetencyRequirement."""

    def test_should_create_requirement_when_data_is_valid(self) -> None:
        """A valid requirement keeps its data."""
        competency_id = CompetencyId.generate()

        requirement = make_requirement(
            competency_id=competency_id,
            minimum_level=4,
            weight=RequirementWeight.IMPORTANT,
        )

        assert requirement.competency_id == competency_id
        assert requirement.minimum_level == 4
        assert requirement.weight is RequirementWeight.IMPORTANT

    @pytest.mark.parametrize("level", [0, 6, -1])
    def test_should_reject_minimum_level_outside_scale(self, level: int) -> None:
        """Levels outside 1-5 are rejected."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Minimum level must be one of",
        ):
            make_requirement(minimum_level=level)

    def test_should_reject_boolean_minimum_level(self) -> None:
        """Booleans are not accepted as levels despite subclassing int."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Minimum level must be one of",
        ):
            make_requirement(minimum_level=True)  # type: ignore[arg-type]

    def test_should_reject_invalid_weight(self) -> None:
        """A plain string is not a valid requirement weight."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Weight must be a RequirementWeight",
        ):
            make_requirement(weight="CORE")  # type: ignore[arg-type]

    def test_should_be_immutable(self) -> None:
        """Requirements are frozen value objects."""
        requirement = make_requirement()

        with pytest.raises(AttributeError):
            requirement.minimum_level = 5  # type: ignore[misc]


class TestCompetencyRequirementValueSemantics:
    """Test equality, hashing, and representation of requirements."""

    def test_should_be_equal_when_all_fields_match(self) -> None:
        """Requirements are identified by their content."""
        competency_id = CompetencyId.generate()
        first = make_requirement(competency_id=competency_id, minimum_level=3)
        second = make_requirement(competency_id=competency_id, minimum_level=3)

        assert first == second
        assert hash(first) == hash(second)

    def test_should_differ_when_level_differs(self) -> None:
        """A different minimum level produces a different requirement."""
        competency_id = CompetencyId.generate()
        first = make_requirement(competency_id=competency_id, minimum_level=3)
        second = make_requirement(competency_id=competency_id, minimum_level=4)

        assert first != second

    def test_should_differ_when_weight_differs(self) -> None:
        """A different weight produces a different requirement."""
        competency_id = CompetencyId.generate()
        first = make_requirement(
            competency_id=competency_id,
            weight=RequirementWeight.CORE,
        )
        second = make_requirement(
            competency_id=competency_id,
            weight=RequirementWeight.DESIRABLE,
        )

        assert first != second

    def test_should_provide_repr(self) -> None:
        """The representation exposes the requirement fields."""
        requirement = make_requirement(minimum_level=4)

        representation = repr(requirement)

        assert "CompetencyRequirement(" in representation
        assert "minimum_level=4" in representation
        assert "CORE" in representation
