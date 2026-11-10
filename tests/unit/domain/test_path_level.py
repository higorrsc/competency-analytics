"""Unit tests for the PathLevel entity."""

import pytest

from src.domain.entities.path_level import PathLevel
from src.domain.exceptions.path_errors import CompetencyPathValidationError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.level_id import LevelId
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


def make_level(
    *,
    level_id: LevelId | None = None,
    name: str = "Senior",
    order: int = 3,
    requirements: list[CompetencyRequirement] | None = None,
) -> PathLevel:
    """Build a valid PathLevel for use in tests."""
    return PathLevel(
        id=level_id or LevelId.generate(),
        name=name,
        order=order,
        requirements=requirements if requirements is not None else [],
    )


class TestPathLevelCreation:
    """Test creation and validation invariants of PathLevel."""

    def test_should_create_level_when_data_is_valid(self) -> None:
        """A valid level keeps its data and requirements."""
        requirement = make_requirement()
        level = make_level(name="Senior", order=3, requirements=[requirement])

        assert level.name == "Senior"
        assert level.order == 3
        assert level.requirements == [requirement]

    def test_should_create_level_without_requirements(self) -> None:
        """A level may start without requirements."""
        level = make_level(requirements=[])

        assert level.requirements == []

    def test_should_trim_level_name(self) -> None:
        """Surrounding whitespace is removed from the name."""
        level = make_level(name="  Senior  ")

        assert level.name == "Senior"

    def test_should_reject_blank_name(self) -> None:
        """A blank level name violates the invariant."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Level name must not be empty",
        ):
            make_level(name="   ")

    @pytest.mark.parametrize("order", [0, -1])
    def test_should_reject_non_positive_order(self, order: int) -> None:
        """Level order starts at 1."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Level order must be a positive integer",
        ):
            make_level(order=order)

    def test_should_reject_boolean_order(self) -> None:
        """Booleans are rejected as orders."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Level order must be a positive integer",
        ):
            make_level(order=True)  # type: ignore[arg-type]

    def test_should_reject_non_list_requirements(self) -> None:
        """Requirements must be provided as a list."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="requirements must be a list",
        ):
            make_level(requirements="not-a-list")  # type: ignore[arg-type]

    def test_should_reject_non_requirement_items(self) -> None:
        """Every item must be a CompetencyRequirement."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="must be CompetencyRequirement instances",
        ):
            make_level(requirements=["Python"])  # type: ignore[list-item]

    def test_should_reject_duplicate_competencies_at_construction(self) -> None:
        """A competency may appear at most once per level."""
        competency_id = CompetencyId.generate()
        first = make_requirement(competency_id=competency_id)
        second = make_requirement(competency_id=competency_id, minimum_level=5)

        with pytest.raises(
            CompetencyPathValidationError,
            match="Duplicate requirement for competency",
        ):
            make_level(requirements=[first, second])


class TestPathLevelRequirements:
    """Test requirement management on a level."""

    def test_should_add_requirement_when_competency_is_new(self) -> None:
        """A new competency requirement is appended."""
        level = make_level()
        requirement = make_requirement()

        level.add_requirement(requirement)

        assert level.requirements == [requirement]

    def test_should_reject_duplicate_requirement_on_add(self) -> None:
        """Adding the same competency twice is rejected."""
        competency_id = CompetencyId.generate()
        level = make_level(requirements=[make_requirement(competency_id=competency_id)])

        with pytest.raises(
            CompetencyPathValidationError,
            match="is already required",
        ):
            level.add_requirement(make_requirement(competency_id=competency_id))

    def test_should_remove_existing_requirement(self) -> None:
        """An existing requirement can be removed."""
        competency_id = CompetencyId.generate()
        level = make_level(requirements=[make_requirement(competency_id=competency_id)])

        level.remove_requirement(competency_id)

        assert level.requirements == []

    def test_should_reject_removing_missing_requirement(self) -> None:
        """Removing a competency that is not required fails."""
        level = make_level()

        with pytest.raises(
            CompetencyPathValidationError,
            match="is not required",
        ):
            level.remove_requirement(CompetencyId.generate())

    def test_should_find_existing_requirement(self) -> None:
        """A requirement can be looked up by competency."""
        competency_id = CompetencyId.generate()
        requirement = make_requirement(competency_id=competency_id)
        level = make_level(requirements=[requirement])

        assert level.find_requirement(competency_id) == requirement

    def test_should_return_none_for_missing_requirement(self) -> None:
        """An unknown competency yields no requirement."""
        level = make_level()

        assert level.find_requirement(CompetencyId.generate()) is None

    def test_should_filter_requirements_by_weight(self) -> None:
        """Requirements can be filtered by importance."""
        core = make_requirement(weight=RequirementWeight.CORE)
        desirable = make_requirement(weight=RequirementWeight.DESIRABLE)
        level = make_level(requirements=[core, desirable])

        assert level.requirements_for_weight(RequirementWeight.CORE) == [core]
        assert level.requirements_for_weight(RequirementWeight.DESIRABLE) == [desirable]
        assert level.requirements_for_weight(RequirementWeight.IMPORTANT) == []


class TestPathLevelIdentity:
    """Test identity semantics of PathLevel."""

    def test_should_be_equal_when_ids_match(self) -> None:
        """Identity is based on the level identifier."""
        level_id = LevelId.generate()
        first = make_level(level_id=level_id, name="Senior")
        second = make_level(level_id=level_id, name="Senior II")

        assert first == second
        assert hash(first) == hash(second)

    def test_should_differ_when_ids_differ(self) -> None:
        """Different identifiers mean different levels."""
        assert make_level() != make_level()

    def test_should_not_equal_other_types(self) -> None:
        """Comparison against unrelated types is not supported."""
        assert make_level() != "Senior"

    def test_should_provide_repr(self) -> None:
        """The representation identifies the level."""
        level = make_level(name="Senior", order=3)

        representation = repr(level)

        assert "PathLevel(" in representation
        assert "Senior" in representation
        assert "order=3" in representation
