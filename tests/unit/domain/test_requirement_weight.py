"""Unit tests for RequirementWeight enum."""

from src.domain.value_objects.requirement_weight import RequirementWeight


class TestRequirementWeight:
    """Test RequirementWeight enum and comparison methods."""

    def test_all_weights_defined(self) -> None:
        """Verify all three weights are defined."""
        assert RequirementWeight.CORE.value == "CORE"
        assert RequirementWeight.IMPORTANT.value == "IMPORTANT"
        assert RequirementWeight.DESIRABLE.value == "DESIRABLE"

    def test_priority_order(self) -> None:
        """Verify priority_order returns correct numeric values."""
        assert RequirementWeight.CORE.priority_order() == 1
        assert RequirementWeight.IMPORTANT.priority_order() == 2
        assert RequirementWeight.DESIRABLE.priority_order() == 3

    def test_less_than_comparison(self) -> None:
        """Verify less than comparison (CORE < IMPORTANT < DESIRABLE)."""
        assert RequirementWeight.CORE < RequirementWeight.IMPORTANT
        assert RequirementWeight.CORE < RequirementWeight.DESIRABLE
        assert RequirementWeight.IMPORTANT < RequirementWeight.DESIRABLE
        assert not (RequirementWeight.IMPORTANT < RequirementWeight.CORE)

    def test_less_than_or_equal_comparison(self) -> None:
        """Verify less than or equal comparison."""
        assert RequirementWeight.CORE <= RequirementWeight.CORE
        assert RequirementWeight.CORE <= RequirementWeight.IMPORTANT
        assert RequirementWeight.IMPORTANT <= RequirementWeight.DESIRABLE

    def test_greater_than_comparison(self) -> None:
        """Verify greater than comparison (DESIRABLE > IMPORTANT > CORE)."""
        assert RequirementWeight.DESIRABLE > RequirementWeight.IMPORTANT
        assert RequirementWeight.DESIRABLE > RequirementWeight.CORE
        assert RequirementWeight.IMPORTANT > RequirementWeight.CORE
        assert not (RequirementWeight.CORE > RequirementWeight.IMPORTANT)

    def test_greater_than_or_equal_comparison(self) -> None:
        """Verify greater than or equal comparison."""
        assert RequirementWeight.DESIRABLE >= RequirementWeight.DESIRABLE
        assert RequirementWeight.DESIRABLE >= RequirementWeight.IMPORTANT
        assert RequirementWeight.IMPORTANT >= RequirementWeight.CORE

    def test_sorting(self) -> None:
        """Verify weights can be sorted correctly."""
        weights = [
            RequirementWeight.DESIRABLE,
            RequirementWeight.CORE,
            RequirementWeight.IMPORTANT,
        ]
        sorted_weights = sorted(weights)
        assert sorted_weights == [
            RequirementWeight.CORE,
            RequirementWeight.IMPORTANT,
            RequirementWeight.DESIRABLE,
        ]
