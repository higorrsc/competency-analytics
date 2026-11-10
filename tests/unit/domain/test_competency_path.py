"""Unit tests for the CompetencyPath aggregate root."""

import pytest

from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.path_level import PathLevel
from src.domain.exceptions.path_errors import (
    CompetencyPathValidationError,
    LevelNotFoundError,
)
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.path_id import PathId
from src.domain.value_objects.requirement_weight import RequirementWeight


def make_level(
    *,
    level_id: LevelId | None = None,
    name: str = "Junior",
    order: int = 1,
) -> PathLevel:
    """Build a valid PathLevel for use in tests."""
    return PathLevel(id=level_id or LevelId.generate(), name=name, order=order)


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


def make_path(
    *,
    path_id: PathId | None = None,
    name: str = "Software Engineer Track",
    description: str = "Engineering career progression",
    levels: list[PathLevel] | None = None,
) -> CompetencyPath:
    """Build a valid CompetencyPath for use in tests."""
    return CompetencyPath(
        id=path_id or PathId.generate(),
        name=name,
        description=description,
        levels=levels if levels is not None else [],
    )


class TestCompetencyPathCreation:
    """Test creation and validation invariants of CompetencyPath."""

    def test_should_create_path_with_sequential_levels(self) -> None:
        """A path with levels 1..N is valid."""
        levels = [
            make_level(name="Junior", order=1),
            make_level(name="Mid", order=2),
            make_level(name="Senior", order=3),
        ]

        path = make_path(levels=levels)

        assert path.name == "Software Engineer Track"
        assert path.levels == levels

    def test_should_create_path_without_levels(self) -> None:
        """A path may start empty and receive levels incrementally."""
        path = make_path(levels=[])

        assert path.levels == []

    def test_should_trim_name_and_description(self) -> None:
        """Surrounding whitespace is removed from text fields."""
        path = make_path(name="  Engineering  ", description="  Track  ")

        assert path.name == "Engineering"
        assert path.description == "Track"

    def test_should_reject_blank_name(self) -> None:
        """A blank path name violates the invariant."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="Career path name must not be empty",
        ):
            make_path(name="   ")

    def test_should_reject_non_list_levels(self) -> None:
        """Levels must be provided as a list."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="levels must be a list",
        ):
            make_path(levels="not-a-list")  # type: ignore[arg-type]

    def test_should_reject_non_level_items(self) -> None:
        """Every item must be a PathLevel."""
        with pytest.raises(
            CompetencyPathValidationError,
            match="must be PathLevel instances",
        ):
            make_path(levels=["Junior"])  # type: ignore[list-item]

    def test_should_reject_non_sequential_orders(self) -> None:
        """Orders 1, 2, 4 leave a gap and are rejected."""
        levels = [
            make_level(name="Junior", order=1),
            make_level(name="Mid", order=2),
            make_level(name="Principal", order=4),
        ]

        with pytest.raises(
            CompetencyPathValidationError,
            match="must be sequential starting at 1",
        ):
            make_path(levels=levels)

    def test_should_reject_orders_not_starting_at_one(self) -> None:
        """A path cannot start at order 2."""
        levels = [
            make_level(name="Mid", order=2),
            make_level(name="Senior", order=3),
        ]

        with pytest.raises(
            CompetencyPathValidationError,
            match="must be sequential starting at 1",
        ):
            make_path(levels=levels)

    def test_should_reject_duplicate_orders(self) -> None:
        """Two levels cannot share the same order."""
        levels = [
            make_level(name="Junior", order=1),
            make_level(name="Mid", order=1),
        ]

        with pytest.raises(
            CompetencyPathValidationError,
            match="Duplicate level order 1",
        ):
            make_path(levels=levels)

    def test_should_reject_duplicate_names_ignoring_case(self) -> None:
        """Level names are unique regardless of casing."""
        levels = [
            make_level(name="Senior", order=1),
            make_level(name="senior", order=2),
        ]

        with pytest.raises(
            CompetencyPathValidationError,
            match="Duplicate level name",
        ):
            make_path(levels=levels)

    def test_should_reject_duplicate_level_identities(self) -> None:
        """Two levels cannot share the same identity."""
        level_id = LevelId.generate()
        levels = [
            make_level(level_id=level_id, name="Junior", order=1),
            make_level(level_id=level_id, name="Mid", order=2),
        ]

        with pytest.raises(
            CompetencyPathValidationError,
            match="Duplicate level identity",
        ):
            make_path(levels=levels)


class TestCompetencyPathLevelManagement:
    """Test adding and locating levels in a path."""

    def test_should_add_level_preserving_sequence(self) -> None:
        """A level with the next order is accepted."""
        path = make_path(levels=[make_level(name="Junior", order=1)])

        path.add_level(make_level(name="Mid", order=2))

        assert [level.name for level in path.levels_in_order()] == ["Junior", "Mid"]

    def test_should_reject_level_that_breaks_sequence(self) -> None:
        """Adding a level with a gap is rejected without mutating the path."""
        path = make_path(levels=[make_level(name="Junior", order=1)])
        original = list(path.levels)

        with pytest.raises(
            CompetencyPathValidationError,
            match="must be sequential starting at 1",
        ):
            path.add_level(make_level(name="Principal", order=5))

        assert path.levels == original

    def test_should_reject_duplicate_level_name_on_add(self) -> None:
        """A duplicate name is rejected on add."""
        path = make_path(levels=[make_level(name="Junior", order=1)])

        with pytest.raises(
            CompetencyPathValidationError,
            match="Duplicate level name",
        ):
            path.add_level(make_level(name="junior", order=2))

    def test_should_find_level_by_id(self) -> None:
        """A level can be found by identifier."""
        level = make_level()
        path = make_path(levels=[level])

        assert path.find_level(level.id) == level

    def test_should_return_none_for_missing_level(self) -> None:
        """An unknown identifier yields no level."""
        path = make_path()

        assert path.find_level(LevelId.generate()) is None

    def test_should_require_existing_level(self) -> None:
        """require_level returns the level when present."""
        level = make_level()
        path = make_path(levels=[level])

        assert path.require_level(level.id) == level

    def test_should_raise_when_required_level_is_missing(self) -> None:
        """require_level raises LevelNotFoundError for unknown identifiers."""
        level_id = LevelId.generate()
        path = make_path()

        with pytest.raises(LevelNotFoundError) as error:
            path.require_level(level_id)

        assert error.value.level_id == level_id

    def test_should_find_level_by_name_ignoring_case(self) -> None:
        """Level lookup by name is case-insensitive."""
        level = make_level(name="Senior", order=1)
        path = make_path(levels=[level])

        assert path.find_level_by_name("  senior ") == level
        assert path.find_level_by_name("Principal") is None

    def test_should_return_levels_in_order(self) -> None:
        """levels_in_order sorts by the level order."""
        senior = make_level(name="Senior", order=3)
        junior = make_level(name="Junior", order=1)
        mid = make_level(name="Mid", order=2)
        path = make_path(levels=[senior, junior, mid])

        assert path.levels_in_order() == [junior, mid, senior]


class TestCompetencyPathDetails:
    """Test descriptive updates on a path."""

    def test_should_update_name_and_description(self) -> None:
        """Text fields can be revised without touching levels."""
        level = make_level()
        path = make_path(levels=[level])

        path.update_details(
            name="Software Engineering Track",
            description="Updated description",
        )

        assert path.name == "Software Engineering Track"
        assert path.description == "Updated description"
        assert path.levels == [level]

    def test_should_reject_blank_name_on_update(self) -> None:
        """An invalid rename leaves the path unchanged."""
        path = make_path(name="Engineering")

        with pytest.raises(
            CompetencyPathValidationError,
            match="Career path name must not be empty",
        ):
            path.update_details(name="  ", description="Track")

        assert path.name == "Engineering"


class TestCompetencyPathIdentity:
    """Test identity semantics of CompetencyPath."""

    def test_should_be_equal_when_ids_match(self) -> None:
        """Identity is based on the path identifier."""
        path_id = PathId.generate()
        first = make_path(path_id=path_id, name="Engineering")
        second = make_path(path_id=path_id, name="Engineering II")

        assert first == second
        assert hash(first) == hash(second)

    def test_should_differ_when_ids_differ(self) -> None:
        """Different identifiers mean different paths."""
        assert make_path() != make_path()

    def test_should_not_equal_other_types(self) -> None:
        """Comparison against unrelated types is not supported."""
        assert make_path() != "Engineering"

    def test_should_provide_repr(self) -> None:
        """The representation identifies the path."""
        path = make_path(name="Engineering")

        representation = repr(path)

        assert "CompetencyPath(" in representation
        assert "Engineering" in representation
