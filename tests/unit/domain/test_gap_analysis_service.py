"""Unit tests for the GapAnalysisService domain service."""

from datetime import UTC, datetime

import pytest

from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.evaluation import Evaluation
from src.domain.entities.path_level import PathLevel
from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.services.gap_analysis_service import GapAnalysisService
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_gap import CompetencyGap
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.measurement_id import MeasurementId
from src.domain.value_objects.requirement_weight import RequirementWeight

EVALUATION_DATE = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
SUBMITTED_AT = datetime(2026, 4, 2, 9, 0, tzinfo=UTC)
RESPONDED_AT = datetime(2026, 4, 3, 9, 0, tzinfo=UTC)


def make_measurement(
    competency_id: CompetencyId,
    current_level: int,
) -> CompetencyMeasurement:
    """Build a measurement for a competency at a given level."""
    return CompetencyMeasurement(
        id=MeasurementId.generate(),
        competency_id=competency_id,
        current_level=current_level,
    )


def make_evaluation(
    measurements: list[CompetencyMeasurement],
    *,
    status: EvaluationStatus = EvaluationStatus.ACCEPTED,
) -> Evaluation:
    """Build a lifecycle-consistent evaluation in the requested status."""
    common = {
        "id": EvaluationId.generate(),
        "collaborator_id": CollaboratorId.generate(),
        "evaluator_id": CollaboratorId.generate(),
        "period": "Q1 2026",
        "evaluation_date": EVALUATION_DATE,
        "status": status,
        "measurements": measurements,
    }
    if status is EvaluationStatus.DRAFT:
        return Evaluation(**common)
    if status is EvaluationStatus.COMPLETED:
        return Evaluation(**common, submitted_at=SUBMITTED_AT)
    return Evaluation(
        **common,
        submitted_at=SUBMITTED_AT,
        response_date=RESPONDED_AT,
        response_notes="Disagree" if status is EvaluationStatus.CONTESTED else None,
    )


def make_requirement(
    competency_id: CompetencyId,
    minimum_level: int,
    weight: RequirementWeight,
) -> CompetencyRequirement:
    """Build a competency requirement for a path level."""
    return CompetencyRequirement(
        competency_id=competency_id,
        minimum_level=minimum_level,
        weight=weight,
    )


def make_level(requirements: list[CompetencyRequirement]) -> PathLevel:
    """Build a path level carrying the given requirements."""
    return PathLevel(
        id=LevelId.generate(),
        name="Senior",
        order=3,
        requirements=requirements,
    )


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


class TestCalculateGaps:
    """Test gap calculation from in-memory domain entities."""

    def test_should_calculate_zero_gap_when_requirement_is_met(self) -> None:
        """A level above the requirement produces no gap."""
        competency_id = CompetencyId.generate()
        evaluation = make_evaluation([make_measurement(competency_id, 5)])
        level = make_level([make_requirement(competency_id, 4, RequirementWeight.CORE)])

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert len(gaps) == 1
        assert gaps[0].competency_id == competency_id
        assert gaps[0].current_level == 5
        assert gaps[0].required_level == 4
        assert gaps[0].gap == 0
        assert gaps[0].is_met() is True

    def test_should_calculate_gap_when_requirement_is_unmet(self) -> None:
        """A level below the requirement produces the difference."""
        competency_id = CompetencyId.generate()
        evaluation = make_evaluation([make_measurement(competency_id, 2)])
        level = make_level([make_requirement(competency_id, 4, RequirementWeight.CORE)])

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert gaps[0].current_level == 2
        assert gaps[0].required_level == 4
        assert gaps[0].gap == 2

    def test_should_treat_unmeasured_competency_as_level_zero(self) -> None:
        """A missing measurement produces the full required level as gap."""
        measured = CompetencyId.generate()
        unmeasured = CompetencyId.generate()
        evaluation = make_evaluation([make_measurement(measured, 3)])
        level = make_level([make_requirement(unmeasured, 4, RequirementWeight.IMPORTANT)])

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert gaps[0].competency_id == unmeasured
        assert gaps[0].current_level == 0
        assert gaps[0].required_level == 4
        assert gaps[0].gap == 4

    def test_should_return_one_gap_per_requirement(self) -> None:
        """Every requirement is evaluated, including met ones."""
        first = CompetencyId.generate()
        second = CompetencyId.generate()
        evaluation = make_evaluation([make_measurement(first, 5), make_measurement(second, 1)])
        level = make_level(
            [
                make_requirement(first, 4, RequirementWeight.CORE),
                make_requirement(second, 3, RequirementWeight.DESIRABLE),
            ]
        )

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert len(gaps) == 2

    def test_should_sort_by_weight_then_gap_size(self) -> None:
        """CORE gaps come before IMPORTANT and DESIRABLE gaps."""
        core = CompetencyId.generate()
        important = CompetencyId.generate()
        desirable = CompetencyId.generate()
        evaluation = make_evaluation(
            [
                make_measurement(core, 4),
                make_measurement(important, 1),
                make_measurement(desirable, 1),
            ]
        )
        level = make_level(
            [
                make_requirement(desirable, 3, RequirementWeight.DESIRABLE),
                make_requirement(important, 4, RequirementWeight.IMPORTANT),
                make_requirement(core, 5, RequirementWeight.CORE),
            ]
        )

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert [gap.competency_id for gap in gaps] == [
            core,
            important,
            desirable,
        ]

    def test_should_sort_same_weight_by_descending_gap_size(self) -> None:
        """Within the same weight, larger gaps come first."""
        larger = CompetencyId.generate()
        smaller = CompetencyId.generate()
        evaluation = make_evaluation([make_measurement(larger, 1), make_measurement(smaller, 4)])
        level = make_level(
            [
                make_requirement(smaller, 5, RequirementWeight.CORE),
                make_requirement(larger, 4, RequirementWeight.CORE),
            ]
        )

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert [gap.competency_id for gap in gaps] == [larger, smaller]
        assert [gap.gap for gap in gaps] == [3, 1]

    def test_should_break_ties_deterministically_by_competency_id(self) -> None:
        """Equal weight and gap size are ordered by competency id."""
        first = CompetencyId.generate()
        second = CompetencyId.generate()
        evaluation = make_evaluation([make_measurement(first, 2), make_measurement(second, 2)])
        level = make_level(
            [
                make_requirement(second, 4, RequirementWeight.CORE),
                make_requirement(first, 4, RequirementWeight.CORE),
            ]
        )

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        expected = sorted([first, second], key=str)
        assert [gap.competency_id for gap in gaps] == expected

    def test_should_reject_draft_evaluation(self) -> None:
        """Draft evaluations are not valid gap analysis baselines."""
        evaluation = make_evaluation(
            [make_measurement(CompetencyId.generate(), 3)],
            status=EvaluationStatus.DRAFT,
        )
        level = make_level([])

        with pytest.raises(
            GapAnalysisError,
            match="requires a finalized evaluation",
        ):
            GapAnalysisService().calculate_gaps(evaluation, level)

    def test_should_reject_completed_evaluation(self) -> None:
        """Completed evaluations are still awaiting the employee response."""
        evaluation = make_evaluation(
            [make_measurement(CompetencyId.generate(), 3)],
            status=EvaluationStatus.COMPLETED,
        )
        level = make_level([])

        with pytest.raises(
            GapAnalysisError,
            match="requires a finalized evaluation",
        ):
            GapAnalysisService().calculate_gaps(evaluation, level)

    def test_should_accept_contested_evaluation(self) -> None:
        """Contested evaluations are finalized and can be used."""
        competency_id = CompetencyId.generate()
        evaluation = make_evaluation(
            [make_measurement(competency_id, 3)],
            status=EvaluationStatus.CONTESTED,
        )
        level = make_level([make_requirement(competency_id, 4, RequirementWeight.CORE)])

        gaps = GapAnalysisService().calculate_gaps(evaluation, level)

        assert gaps[0].gap == 1

    def test_should_return_empty_list_when_level_has_no_requirements(self) -> None:
        """A level without requirements produces no gaps."""
        evaluation = make_evaluation([make_measurement(CompetencyId.generate(), 3)])

        gaps = GapAnalysisService().calculate_gaps(evaluation, make_level([]))

        assert gaps == []

    def test_should_not_mutate_inputs(self) -> None:
        """Gap calculation only reads the provided entities."""
        competency_id = CompetencyId.generate()
        measurement = make_measurement(competency_id, 2)
        evaluation = make_evaluation([measurement])
        requirement = make_requirement(competency_id, 4, RequirementWeight.CORE)
        level = make_level([requirement])

        GapAnalysisService().calculate_gaps(evaluation, level)

        assert evaluation.measurements == [measurement]
        assert level.requirements == [requirement]


class TestProgressionEligibilityCheck:
    """Test progression eligibility based on CORE requirements."""

    def test_should_be_eligible_when_all_core_requirements_are_met(self) -> None:
        """IMPORTANT gaps do not block progression."""
        important = CompetencyId.generate()
        gaps = [
            make_gap(current_level=5, required_level=4, gap=0),
            make_gap(
                competency_id=important,
                current_level=1,
                required_level=3,
                gap=2,
                weight=RequirementWeight.IMPORTANT,
            ),
        ]

        eligibility = GapAnalysisService().check_progression_eligibility(gaps)

        assert eligibility.is_eligible is True
        assert eligibility.blocking_competency_ids == ()

    def test_should_not_be_eligible_with_a_core_gap(self) -> None:
        """Any open CORE gap blocks progression and is listed."""
        blocker = CompetencyId.generate()
        gaps = [
            make_gap(
                competency_id=blocker,
                current_level=3,
                required_level=4,
                gap=1,
            )
        ]

        eligibility = GapAnalysisService().check_progression_eligibility(gaps)

        assert eligibility.is_eligible is False
        assert eligibility.blocking_competency_ids == (blocker,)

    def test_should_list_every_blocking_core_competency(self) -> None:
        """All open CORE competencies are reported in gap order."""
        first = CompetencyId.generate()
        second = CompetencyId.generate()
        gaps = [
            make_gap(
                competency_id=first,
                current_level=1,
                required_level=4,
                gap=3,
            ),
            make_gap(
                competency_id=second,
                current_level=3,
                required_level=4,
                gap=1,
            ),
        ]

        eligibility = GapAnalysisService().check_progression_eligibility(gaps)

        assert eligibility.blocking_competency_ids == (first, second)

    def test_should_ignore_important_and_desirable_gaps(self) -> None:
        """Only CORE requirements affect eligibility."""
        gaps = [
            make_gap(current_level=5, required_level=4, gap=0),
            make_gap(
                current_level=1,
                required_level=4,
                gap=3,
                weight=RequirementWeight.IMPORTANT,
            ),
            make_gap(
                current_level=1,
                required_level=4,
                gap=3,
                weight=RequirementWeight.DESIRABLE,
            ),
        ]

        eligibility = GapAnalysisService().check_progression_eligibility(gaps)

        assert eligibility.is_eligible is True

    def test_should_be_eligible_without_gaps(self) -> None:
        """No requirements means nothing blocks progression."""
        eligibility = GapAnalysisService().check_progression_eligibility([])

        assert eligibility.is_eligible is True


class TestGenerateRecommendation:
    """Test textual recommendations for different gaps."""

    def test_should_recommend_immediate_action_for_large_core_gap(self) -> None:
        """A CORE gap of three or more levels is urgent."""
        gap = make_gap(current_level=2, required_level=5, gap=3)

        recommendation = GapAnalysisService().generate_recommendation(gap)

        assert "Immediate high-priority development" in recommendation
        assert "CORE" in recommendation
        assert str(gap.competency_id) in recommendation
        assert "from level 2 to level 5" in recommendation

    def test_should_recommend_high_priority_for_small_core_gap(self) -> None:
        """A small CORE gap is still high priority."""
        gap = make_gap(current_level=3, required_level=4, gap=1)

        recommendation = GapAnalysisService().generate_recommendation(gap)

        assert "High-priority development" in recommendation
        assert "Immediate" not in recommendation

    def test_should_recommend_planned_development_for_important_gap(self) -> None:
        """IMPORTANT gaps are planned development."""
        gap = make_gap(
            current_level=2,
            required_level=4,
            gap=2,
            weight=RequirementWeight.IMPORTANT,
        )

        recommendation = GapAnalysisService().generate_recommendation(gap)

        assert "Planned development" in recommendation
        assert "IMPORTANT" in recommendation

    def test_should_recommend_optional_development_for_desirable_gap(self) -> None:
        """DESIRABLE gaps are optional development."""
        gap = make_gap(
            current_level=2,
            required_level=3,
            gap=1,
            weight=RequirementWeight.DESIRABLE,
        )

        recommendation = GapAnalysisService().generate_recommendation(gap)

        assert "Optional development" in recommendation
        assert "DESIRABLE" in recommendation

    def test_should_recommend_maintenance_for_met_requirement(self) -> None:
        """A met requirement only needs maintenance."""
        gap = make_gap(current_level=5, required_level=4, gap=0)

        recommendation = GapAnalysisService().generate_recommendation(gap)

        assert "Maintain current proficiency" in recommendation
        assert "is met" in recommendation

    def test_should_mention_unmeasured_competency(self) -> None:
        """An unmeasured competency is called out as needing assessment."""
        gap = make_gap(current_level=0, required_level=4, gap=4)

        recommendation = GapAnalysisService().generate_recommendation(gap)

        assert "assess and develop" in recommendation
        assert "from level 0 to level 4" in recommendation
        assert "gap of 4" in recommendation
