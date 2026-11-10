"""Pure domain service for competency gap analysis."""

from src.domain.entities.evaluation import Evaluation
from src.domain.entities.path_level import PathLevel
from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.value_objects.competency_gap import CompetencyGap
from src.domain.value_objects.progression_eligibility import ProgressionEligibility
from src.domain.value_objects.requirement_weight import RequirementWeight


class GapAnalysisService:
    """
    Pure domain service that compares an evaluation with a career path level.

    The service has no infrastructure dependencies: it receives in-memory
    domain entities, performs only calculations, and returns domain value
    objects. It performs no database queries, HTTP calls, or filesystem
    access, which makes it fully unit-testable and reusable by any adapter.

    Gap rules:

    - only finalized evaluations (``ACCEPTED`` or ``CONTESTED``) are valid
      baselines;
    - an unmeasured competency is treated as level ``0``, producing the full
      required level as its gap;
    - a current level above the requirement produces a gap of ``0``;
    - gaps are ordered by weight (CORE, IMPORTANT, DESIRABLE) and then by
      descending gap size.
    """

    def calculate_gaps(
        self,
        evaluation: Evaluation,
        target_level: PathLevel,
    ) -> list[CompetencyGap]:
        """
        Calculate the gaps between an evaluation and a target path level.

        Args:
            evaluation: Finalized baseline evaluation.
            target_level: Career path level whose requirements are targeted.

        Returns:
            Prioritized gaps, one per requirement, ordered by weight and then
            by descending gap size.

        Raises:
            GapAnalysisError: If the evaluation is not finalized.
        """
        if not evaluation.status.is_finalized():
            raise GapAnalysisError(
                "Gap analysis requires a finalized evaluation "
                "(ACCEPTED or CONTESTED), got "
                f"{evaluation.status.value}"
            )

        gaps: list[CompetencyGap] = []
        for requirement in target_level.requirements:
            measurement = evaluation.find_measurement(requirement.competency_id)
            current_level = 0 if measurement is None else measurement.current_level
            gap_size = max(0, requirement.minimum_level - current_level)
            gaps.append(
                CompetencyGap(
                    competency_id=requirement.competency_id,
                    current_level=current_level,
                    required_level=requirement.minimum_level,
                    gap=gap_size,
                    weight=requirement.weight,
                )
            )

        return self._sort_by_priority(gaps)

    def check_progression_eligibility(
        self,
        gaps: list[CompetencyGap],
    ) -> ProgressionEligibility:
        """
        Determine whether the collaborator can progress to the target level.

        Only CORE requirements block progression. IMPORTANT and DESIRABLE
        gaps are development opportunities but do not prevent eligibility.

        Args:
            gaps: Gaps produced by ``calculate_gaps``.

        Returns:
            Eligibility with the ordered list of blocking CORE competencies.
        """
        blocking = tuple(
            gap.competency_id
            for gap in gaps
            if gap.weight is RequirementWeight.CORE and not gap.is_met()
        )
        return ProgressionEligibility(
            is_eligible=not blocking,
            blocking_competency_ids=blocking,
        )

    def generate_recommendation(self, gap: CompetencyGap) -> str:
        """
        Generate textual development guidance for a single gap.

        The recommendation reflects both the requirement weight and the gap
        size: large CORE gaps call for immediate action, while met requirements
        only need maintenance.

        Args:
            gap: Gap to generate guidance for.

        Returns:
            Human-readable development recommendation.
        """
        if gap.is_met():
            return (
                f"Maintain current proficiency ({gap.weight.value}); "
                f"the requirement for competency {gap.competency_id} is met."
            )

        if gap.weight is RequirementWeight.CORE:
            if gap.gap >= 3:
                priority = "Immediate high-priority development"
            else:
                priority = "High-priority development"
        elif gap.weight is RequirementWeight.IMPORTANT:
            priority = "Planned development"
        else:
            priority = "Optional development"

        if gap.current_level == 0:
            detail = (
                f"assess and develop competency {gap.competency_id} "
                f"from level 0 to level {gap.required_level} "
                f"(gap of {gap.gap})"
            )
        else:
            detail = (
                f"develop competency {gap.competency_id} "
                f"from level {gap.current_level} to level {gap.required_level} "
                f"(gap of {gap.gap})"
            )

        return f"{priority} ({gap.weight.value}): {detail}."

    @staticmethod
    def _sort_by_priority(gaps: list[CompetencyGap]) -> list[CompetencyGap]:
        """
        Sort gaps by weight, then by descending gap size.

        The competency identifier is used as a final tie-breaker so the
        ordering is deterministic for equal weight and gap size.

        Args:
            gaps: Gaps to sort.

        Returns:
            A new list in priority order.
        """
        return sorted(
            gaps,
            key=lambda gap: (
                gap.weight.priority_order(),
                -gap.gap,
                str(gap.competency_id),
            ),
        )
