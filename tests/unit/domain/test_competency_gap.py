"""Unit tests for the CompetencyGap value object."""

import pytest

from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.value_objects.competency_gap import CompetencyGap
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.requirement_weight import RequirementWeight


def make_gap(
    *,
    competency_id: CompetencyId | None = None,
    current_level: int = 2,
    required_level: int = 4,
    gap: int = 2,
    weight: RequirementWeight = RequirementWeight.CORE,
) -> CompetencyGap:
    """Build a valid CompetencyGap for use in tests."""
    return CompetencyGap(
        competency_id=competency_id or CompetencyId.generate(),
        current_level=current_level,
        required_level=required_level,
        gap=gap,
        weight=weight,
    )


class TestCompetencyGapCreation:
    """Test creation and validation invariants of CompetencyGap."""

    def test_should_create_gap_when_data_is_valid(self) -> None:
        """A valid gap keeps all of its data."""
        competency_id = CompetencyId.generate()

        gap = make_gap(
            competency_id=competency_id,
            current_level=2,
            required_level=4,
            gap=2,
            weight=RequirementWeight.IMPORTANT,
        )

        assert gap.competency_id == competency_id
        assert gap.current_level == 2
        assert gap.required_level == 4
        assert gap.gap == 2
        assert gap.weight is RequirementWeight.IMPORTANT

    def test_should_report_unmet_requirement(self) -> None:
        """A positive gap means the requirement is not met."""
        gap = make_gap(current_level=2, required_level=4, gap=2)

        assert gap.is_met() is False

    def test_should_report_met_requirement(self) -> None:
        """A zero gap means the requirement is met."""
        gap = make_gap(current_level=5, required_level=4, gap=0)

        assert gap.is_met() is True

    def test_should_allow_unmeasured_current_level(self) -> None:
        """Level 0 represents a competency that was not measured."""
        gap = make_gap(current_level=0, required_level=4, gap=4)

        assert gap.current_level == 0
        assert gap.gap == 4

    def test_should_reject_non_competency_id(self) -> None:
        """The competency reference must be a CompetencyId."""
        with pytest.raises(
            GapAnalysisError,
            match="competency_id must be a CompetencyId",
        ):
            make_gap(competency_id="python")  # type: ignore[arg-type]

    @pytest.mark.parametrize("level", [-1, 6])
    def test_should_reject_current_level_outside_range(self, level: int) -> None:
        """Current levels must be 0 or between 1 and 5."""
        with pytest.raises(
            GapAnalysisError,
            match="Current level must be 0 or one of",
        ):
            make_gap(current_level=level, gap=2)

    def test_should_reject_boolean_current_level(self) -> None:
        """Booleans are not accepted as current levels."""
        with pytest.raises(
            GapAnalysisError,
            match="Current level must be 0 or one of",
        ):
            make_gap(current_level=True)  # type: ignore[arg-type]

    @pytest.mark.parametrize("level", [0, 6, -1])
    def test_should_reject_required_level_outside_scale(self, level: int) -> None:
        """Required levels must be between 1 and 5."""
        with pytest.raises(
            GapAnalysisError,
            match="Required level must be one of",
        ):
            make_gap(required_level=level, gap=2)

    def test_should_reject_boolean_required_level(self) -> None:
        """Booleans are not accepted as required levels."""
        with pytest.raises(
            GapAnalysisError,
            match="Required level must be one of",
        ):
            make_gap(required_level=True)  # type: ignore[arg-type]

    def test_should_reject_negative_gap(self) -> None:
        """Gap sizes cannot be negative."""
        with pytest.raises(
            GapAnalysisError,
            match="Gap must be a non-negative integer",
        ):
            make_gap(current_level=2, required_level=4, gap=-1)

    def test_should_reject_boolean_gap(self) -> None:
        """Booleans are not accepted as gap sizes."""
        with pytest.raises(
            GapAnalysisError,
            match="Gap must be a non-negative integer",
        ):
            make_gap(current_level=2, required_level=4, gap=True)  # type: ignore[arg-type]

    def test_should_reject_inconsistent_gap(self) -> None:
        """The gap must match the difference between levels."""
        with pytest.raises(
            GapAnalysisError,
            match="Gap must equal max",
        ):
            make_gap(current_level=2, required_level=4, gap=1)

    def test_should_reject_invalid_weight(self) -> None:
        """The weight must be a RequirementWeight."""
        with pytest.raises(
            GapAnalysisError,
            match="Weight must be a RequirementWeight",
        ):
            make_gap(weight="CORE")  # type: ignore[arg-type]

    def test_should_be_immutable(self) -> None:
        """Gaps are frozen value objects."""
        gap = make_gap()

        with pytest.raises(AttributeError):
            gap.gap = 1  # type: ignore[misc]

    def test_should_provide_repr(self) -> None:
        """The representation exposes the gap fields."""
        gap = make_gap(current_level=2, required_level=4, gap=2)

        representation = repr(gap)

        assert "CompetencyGap(" in representation
        assert "current_level=2" in representation
        assert "required_level=4" in representation
        assert "gap=2" in representation
        assert "CORE" in representation
