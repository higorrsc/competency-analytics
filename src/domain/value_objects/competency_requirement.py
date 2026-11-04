"""CompetencyRequirement value object for career path level requirements."""

from dataclasses import dataclass

from src.domain.exceptions.path_errors import CompetencyPathValidationError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.proficiency_level import VALID_LEVELS, is_valid_level
from src.domain.value_objects.requirement_weight import RequirementWeight


@dataclass(frozen=True)
class CompetencyRequirement:
    """
    A competency requirement attached to a career path level.

    A requirement states that, to reach a given career level, a collaborator
    must reach at least ``minimum_level`` in a competency, and how important
    that competency is for the level (``weight``).

    Requirements are immutable value objects: they are identified by their
    full content, not by a surrogate identifier. Duplicate requirements for
    the same competency are rejected by the owning ``PathLevel``.
    """

    competency_id: CompetencyId
    minimum_level: int
    weight: RequirementWeight

    def __post_init__(self) -> None:
        """Validate the requirement invariants after construction."""
        self._validate_minimum_level(self.minimum_level)
        self._validate_weight(self.weight)

    @staticmethod
    def _validate_minimum_level(level: object) -> None:
        """
        Validate that the minimum level belongs to the 1-5 scale.

        Args:
            level: Proposed minimum proficiency level.

        Raises:
            CompetencyPathValidationError: If the level is not an integer
                between 1 and 5.
        """
        if not is_valid_level(level):
            raise CompetencyPathValidationError(
                f"Minimum level must be one of {sorted(VALID_LEVELS)}, got {level!r}"
            )

    @staticmethod
    def _validate_weight(weight: object) -> None:
        """
        Validate that the weight is a supported requirement weight.

        Args:
            weight: Proposed requirement weight.

        Raises:
            CompetencyPathValidationError: If the weight is not a
                RequirementWeight value.
        """
        if not isinstance(weight, RequirementWeight):
            raise CompetencyPathValidationError(
                f"Weight must be a RequirementWeight, got {type(weight).__name__}"
            )

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"CompetencyRequirement(competency_id={self.competency_id!r}, "
            f"minimum_level={self.minimum_level}, weight={self.weight.value!r})"
        )
