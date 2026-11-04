"""Unit tests for the Competency catalog entity."""

import pytest

from src.domain.entities.competency import VALID_LEVELS, Competency
from src.domain.exceptions.competency_errors import CompetencyValidationError
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId


def make_level_descriptions() -> dict[int, str]:
    """Build a complete, valid set of proficiency level descriptions."""
    return {
        1: "Basic awareness",
        2: "Working knowledge",
        3: "Independent practitioner",
        4: "Advanced practitioner",
        5: "Expert and reference",
    }


def make_competency(
    *,
    competency_id: CompetencyId | None = None,
    name: str = "Python",
    description: str = "Python programming language",
    category_id: CategoryId | None = None,
    group_id: GroupId | None = None,
    level_descriptions: dict[int, str] | None = None,
) -> Competency:
    """Build a valid Competency for use in tests."""
    return Competency(
        id=competency_id or CompetencyId.generate(),
        name=name,
        description=description,
        category_id=category_id or CategoryId.generate(),
        group_id=group_id or GroupId.generate(),
        level_descriptions=(
            level_descriptions if level_descriptions is not None else make_level_descriptions()
        ),
    )


class TestCompetencyCreation:
    """Test creation and validation invariants of Competency."""

    def test_should_create_competency_when_all_levels_are_described(self) -> None:
        """A complete competency is created and exposes its data."""
        category_id = CategoryId.generate()
        group_id = GroupId.generate()
        competency_id = CompetencyId.generate()

        competency = make_competency(
            competency_id=competency_id,
            category_id=category_id,
            group_id=group_id,
        )

        assert competency.id == competency_id
        assert competency.name == "Python"
        assert competency.category_id == category_id
        assert competency.group_id == group_id
        assert competency.level_descriptions == make_level_descriptions()

    def test_should_reject_competency_when_name_is_empty(self) -> None:
        """An empty name violates the catalog invariant."""
        with pytest.raises(CompetencyValidationError, match="name must not be empty"):
            make_competency(name="")

    def test_should_reject_competency_when_name_is_whitespace(self) -> None:
        """A whitespace-only name is not meaningful."""
        with pytest.raises(CompetencyValidationError, match="name must not be empty"):
            make_competency(name="   ")

    def test_should_reject_competency_when_level_descriptions_are_missing(self) -> None:
        """All five proficiency levels are mandatory."""
        incomplete = make_level_descriptions()
        del incomplete[5]

        with pytest.raises(
            CompetencyValidationError,
            match="Missing descriptions for proficiency levels: 5",
        ):
            make_competency(level_descriptions=incomplete)

    def test_should_reject_competency_when_multiple_levels_are_missing(self) -> None:
        """The error reports every missing level."""
        incomplete = make_level_descriptions()
        del incomplete[4]
        del incomplete[5]

        with pytest.raises(
            CompetencyValidationError,
            match="Missing descriptions for proficiency levels: 4, 5",
        ):
            make_competency(level_descriptions=incomplete)

    def test_should_reject_competency_when_unexpected_level_is_present(self) -> None:
        """Levels outside the 1-5 scale are rejected."""
        invalid = make_level_descriptions()
        invalid[6] = "Beyond expert"

        with pytest.raises(
            CompetencyValidationError,
            match="Unexpected proficiency levels: 6",
        ):
            make_competency(level_descriptions=invalid)

    def test_should_reject_competency_when_level_description_is_blank(self) -> None:
        """Every level must have a non-blank description."""
        invalid = make_level_descriptions()
        invalid[3] = "   "

        with pytest.raises(
            CompetencyValidationError,
            match="Description for proficiency level 3 must not be empty",
        ):
            make_competency(level_descriptions=invalid)

    def test_should_reject_competency_when_levels_are_not_a_mapping(self) -> None:
        """Level descriptions must be a mapping of level to text."""
        with pytest.raises(
            CompetencyValidationError,
            match="must be a mapping",
        ):
            make_competency(level_descriptions=["not", "a", "mapping"])  # type: ignore[arg-type]

    def test_valid_levels_constant_matches_scale(self) -> None:
        """The catalog scale is fixed at levels 1 through 5."""
        assert VALID_LEVELS == frozenset({1, 2, 3, 4, 5})


class TestCompetencyLevelDescriptions:
    """Test proficiency level description access and updates."""

    def test_should_return_description_for_valid_level(self) -> None:
        """A valid level returns its description."""
        competency = make_competency()

        assert competency.description_for_level(1) == "Basic awareness"
        assert competency.description_for_level(5) == "Expert and reference"

    @pytest.mark.parametrize("level", [0, 6, -1])
    def test_should_reject_invalid_level_lookup(self, level: int) -> None:
        """Levels outside 1-5 are rejected when looked up."""
        competency = make_competency()

        with pytest.raises(CompetencyValidationError, match="Invalid proficiency level"):
            competency.description_for_level(level)

    def test_should_update_level_descriptions_when_valid(self) -> None:
        """Level descriptions can be revised without touching identity."""
        competency = make_competency()
        revised = {
            1: "Knows the syntax",
            2: "Writes simple scripts",
            3: "Builds applications",
            4: "Designs systems",
            5: "Shapes the ecosystem",
        }

        competency.update_level_descriptions(revised)

        assert competency.level_descriptions == revised
        assert competency.description_for_level(1) == "Knows the syntax"

    def test_should_keep_previous_levels_when_update_is_invalid(self) -> None:
        """A rejected update must not corrupt the current descriptions."""
        competency = make_competency()
        original = dict(competency.level_descriptions)

        with pytest.raises(CompetencyValidationError):
            competency.update_level_descriptions({1: "Only one level"})

        assert competency.level_descriptions == original


class TestCompetencyDetails:
    """Test updating descriptive fields of a competency."""

    def test_should_update_name_and_description(self) -> None:
        """Name and description can be revised while references persist."""
        competency = make_competency()

        competency.update_details(
            name="Python Programming",
            description="Backend and data engineering with Python",
        )

        assert competency.name == "Python Programming"
        assert competency.description == "Backend and data engineering with Python"
        assert competency.level_descriptions == make_level_descriptions()

    def test_should_reject_update_when_name_is_empty(self) -> None:
        """An invalid rename leaves the competency unchanged."""
        competency = make_competency()

        with pytest.raises(CompetencyValidationError, match="name must not be empty"):
            competency.update_details(name="  ", description="Still Python")

        assert competency.name == "Python"

    def test_should_report_category_membership(self) -> None:
        """Category membership is determined by identifier."""
        category_id = CategoryId.generate()
        competency = make_competency(category_id=category_id)

        assert competency.belongs_to_category(category_id) is True
        assert competency.belongs_to_category(CategoryId.generate()) is False

    def test_should_report_group_membership(self) -> None:
        """Group membership is determined by identifier."""
        group_id = GroupId.generate()
        competency = make_competency(group_id=group_id)

        assert competency.belongs_to_group(group_id) is True
        assert competency.belongs_to_group(GroupId.generate()) is False


class TestCompetencyIdentity:
    """Test identity semantics of the Competency entity."""

    def test_should_consider_competencies_equal_when_ids_match(self) -> None:
        """Identity is based on the identifier, not on mutable fields."""
        competency_id = CompetencyId.generate()
        first = make_competency(competency_id=competency_id, name="Python")
        second = make_competency(competency_id=competency_id, name="Python 3")

        assert first == second
        assert hash(first) == hash(second)

    def test_should_consider_competencies_different_when_ids_differ(self) -> None:
        """Different identifiers mean different competencies."""
        first = make_competency()
        second = make_competency()

        assert first != second

    def test_should_not_equal_other_types(self) -> None:
        """Comparison against unrelated types is not supported."""
        competency = make_competency()

        assert competency != "Python"

    def test_should_provide_repr(self) -> None:
        """The representation identifies the competency."""
        competency = make_competency(name="Python")

        assert "Competency(" in repr(competency)
        assert "Python" in repr(competency)
