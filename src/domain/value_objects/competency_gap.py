"""CompetencyGap value object for gap analysis results."""

from dataclasses import dataclass

from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.proficiency_level import VALID_LEVELS, is_valid_level
from src.domain.value_objects.requirement_weight import RequirementWeight


@dataclass(frozen=True)
class CompetencyGap:
    """
    The gap between a collaborator's current level and a required level.

    ``current_level`` is ``0`` when the competency has not been measured in
    the baseline evaluation, meaning the whole requirement is still open.
    ``gap`` is always ``max(0, required_level - current_level)``: a negative
    difference is normalized to zero because exceeding a requirement is not a
    gap.

    The value object is immutable and is produced by ``GapAnalysisService``.
    """

    competency_id: CompetencyId
    current_level: int
    required_level: int
    gap: int
    weight: RequirementWeight

    def __post_init__(self) -> None:
        """Validate the gap invariants after construction."""
        self._validate_competency_id(self.competency_id)
        self._validate_current_level(self.current_level)
        self._validate_required_level(self.required_level)
        self._validate_gap(self.gap)
        self._validate_weight(self.weight)

        expected_gap = max(0, self.required_level - self.current_level)
        if self.gap != expected_gap:
            raise GapAnalysisError(
                "Gap must equal max(0, required_level - current_level); "
                f"expected {expected_gap}, got {self.gap}"
            )

    @staticmethod
    def _validate_competency_id(competency_id: object) -> None:
        """
        Validate that the competency reference is a CompetencyId.

        Args:
            competency_id: Proposed competency identifier.

        Raises:
            GapAnalysisError: If the value is not a CompetencyId.
        """
        if not isinstance(competency_id, CompetencyId):
            raise GapAnalysisError(
                f"Gap competency_id must be a CompetencyId, got {type(competency_id).__name__}"
            )

    @staticmethod
    def _validate_current_level(level: object) -> None:
        """
        Validate that the current level is 0 (unmeasured) or 1-5.

        Args:
            level: Proposed current proficiency level.

        Raises:
            GapAnalysisError: If the level is not an integer between 0 and 5.
        """
        if not isinstance(level, int) or isinstance(level, bool) or not 0 <= level <= 5:
            raise GapAnalysisError(
                f"Current level must be 0 or one of {sorted(VALID_LEVELS)}, got {level!r}"
            )

    @staticmethod
    def _validate_required_level(level: object) -> None:
        """
        Validate that the required level belongs to the 1-5 scale.

        Args:
            level: Proposed required proficiency level.

        Raises:
            GapAnalysisError: If the level is not an integer between 1 and 5.
        """
        if not is_valid_level(level):
            raise GapAnalysisError(
                f"Required level must be one of {sorted(VALID_LEVELS)}, got {level!r}"
            )

    @staticmethod
    def _validate_gap(gap: object) -> None:
        """
        Validate that the gap is a non-negative integer.

        Args:
            gap: Proposed gap size.

        Raises:
            GapAnalysisError: If the gap is not a non-negative integer.
        """
        if not isinstance(gap, int) or isinstance(gap, bool) or gap < 0:
            raise GapAnalysisError(f"Gap must be a non-negative integer, got {gap!r}")

    @staticmethod
    def _validate_weight(weight: object) -> None:
        """
        Validate that the weight is a RequirementWeight.

        Args:
            weight: Proposed requirement weight.

        Raises:
            GapAnalysisError: If the value is not a RequirementWeight.
        """
        if not isinstance(weight, RequirementWeight):
            raise GapAnalysisError(
                f"Weight must be a RequirementWeight, got {type(weight).__name__}"
            )

    def is_met(self) -> bool:
        """
        Return whether the requirement is met.

        Returns:
            ``True`` when the gap is zero.
        """
        return self.gap == 0

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"CompetencyGap(competency_id={self.competency_id!r}, "
            f"current_level={self.current_level}, "
            f"required_level={self.required_level}, gap={self.gap}, "
            f"weight={self.weight.value!r})"
        )
