"""Unit tests for the ProgressionEligibility value object."""

import pytest

from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.progression_eligibility import ProgressionEligibility


class TestProgressionEligibilityCreation:
    """Test creation and validation invariants of ProgressionEligibility."""

    def test_should_create_eligible_result_without_blockers(self) -> None:
        """An eligible collaborator has no blocking competencies."""
        eligibility = ProgressionEligibility(is_eligible=True)

        assert eligibility.is_eligible is True
        assert eligibility.blocking_competency_ids == ()
        assert eligibility.has_blockers() is False

    def test_should_create_ineligible_result_with_blockers(self) -> None:
        """An ineligible collaborator lists the blocking competencies."""
        blocker = CompetencyId.generate()

        eligibility = ProgressionEligibility(
            is_eligible=False,
            blocking_competency_ids=(blocker,),
        )

        assert eligibility.is_eligible is False
        assert eligibility.blocking_competency_ids == (blocker,)
        assert eligibility.has_blockers() is True

    def test_should_reject_eligible_result_with_blockers(self) -> None:
        """Eligibility and blockers cannot contradict each other."""
        with pytest.raises(
            GapAnalysisError,
            match="eligible collaborator cannot have blocking competencies",
        ):
            ProgressionEligibility(
                is_eligible=True,
                blocking_competency_ids=(CompetencyId.generate(),),
            )

    def test_should_reject_ineligible_result_without_blockers(self) -> None:
        """Ineligibility requires at least one blocker."""
        with pytest.raises(
            GapAnalysisError,
            match="ineligible collaborator must have at least one blocker",
        ):
            ProgressionEligibility(is_eligible=False)

    def test_should_reject_non_boolean_eligibility(self) -> None:
        """The eligibility flag must be a real boolean."""
        with pytest.raises(
            GapAnalysisError,
            match="is_eligible must be a bool",
        ):
            ProgressionEligibility(is_eligible=1)  # type: ignore[arg-type]

    def test_should_reject_non_tuple_blockers(self) -> None:
        """Blockers must be an immutable tuple."""
        with pytest.raises(
            GapAnalysisError,
            match="must be a tuple",
        ):
            ProgressionEligibility(
                is_eligible=False,
                blocking_competency_ids=[CompetencyId.generate()],  # type: ignore[arg-type]
            )

    def test_should_reject_non_competency_blockers(self) -> None:
        """Every blocker must be a CompetencyId."""
        with pytest.raises(
            GapAnalysisError,
            match="must be CompetencyId instances",
        ):
            ProgressionEligibility(
                is_eligible=False,
                blocking_competency_ids=("python",),  # type: ignore[arg-type]
            )

    def test_should_reject_duplicate_blockers(self) -> None:
        """The same competency cannot block progression twice."""
        blocker = CompetencyId.generate()

        with pytest.raises(
            GapAnalysisError,
            match="Duplicate blocking competency",
        ):
            ProgressionEligibility(
                is_eligible=False,
                blocking_competency_ids=(blocker, blocker),
            )

    def test_should_be_immutable(self) -> None:
        """Eligibility results are frozen value objects."""
        eligibility = ProgressionEligibility(is_eligible=True)

        with pytest.raises(AttributeError):
            eligibility.is_eligible = False  # type: ignore[misc]

    def test_should_provide_repr(self) -> None:
        """The representation exposes the eligibility fields."""
        eligibility = ProgressionEligibility(is_eligible=True)

        representation = repr(eligibility)

        assert "ProgressionEligibility(" in representation
        assert "is_eligible=True" in representation
