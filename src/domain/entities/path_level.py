"""PathLevel entity belonging to a career path aggregate."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from src.domain.exceptions.path_errors import CompetencyPathValidationError
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.requirement_weight import RequirementWeight


@dataclass(eq=False)
class PathLevel:
    """
    A single level inside a career path (for example Junior, Mid, Senior).

    A level owns the competency requirements that a collaborator must satisfy
    to reach it. Requirements are value objects and cannot repeat the same
    competency: each competency appears at most once per level.

    Identity is based on ``id`` only. ``order`` expresses the position of the
    level inside the path (1-based) and is validated by the owning
    ``CompetencyPath`` for sequential continuity.
    """

    id: LevelId
    name: str
    order: int
    requirements: list[CompetencyRequirement] = field(
        default_factory=list[CompetencyRequirement]
    )

    def __post_init__(self) -> None:
        """Validate level invariants immediately after construction."""
        self._validate_name(self.name)
        self._validate_order(self.order)
        self._validate_requirements(self.requirements)
        self.name = self.name.strip()

    @staticmethod
    def _validate_name(name: object) -> None:
        """
        Validate that the level name is present and meaningful.

        Args:
            name: Proposed level name.

        Raises:
            CompetencyPathValidationError: If the name is blank.
        """
        if not isinstance(name, str) or not name.strip():
            raise CompetencyPathValidationError("Level name must not be empty")

    @staticmethod
    def _validate_order(order: object) -> None:
        """
        Validate that the level order is a positive integer.

        Args:
            order: Proposed 1-based position of the level.

        Raises:
            CompetencyPathValidationError: If the order is not a positive int.
        """
        if not isinstance(order, int) or isinstance(order, bool) or order < 1:
            raise CompetencyPathValidationError(
                f"Level order must be a positive integer, got {order!r}"
            )

    @staticmethod
    def _validate_requirements(requirements: object) -> None:
        """
        Validate the requirement collection and its uniqueness rule.

        Args:
            requirements: Proposed requirement list.

        Raises:
            CompetencyPathValidationError: If the value is not a list, contains
                non-requirement items, or repeats a competency.
        """
        if not isinstance(requirements, list):
            raise CompetencyPathValidationError(
                "Level requirements must be a list of CompetencyRequirement"
            )

        seen: set[CompetencyId] = set()
        for requirement in cast(list[object], requirements):
            if not isinstance(requirement, CompetencyRequirement):
                raise CompetencyPathValidationError(
                    "Level requirements must be CompetencyRequirement instances"
                )
            if requirement.competency_id in seen:
                raise CompetencyPathValidationError(
                    f"Duplicate requirement for competency {requirement.competency_id}"
                )
            seen.add(requirement.competency_id)

    def add_requirement(self, requirement: CompetencyRequirement) -> None:
        """
        Add a competency requirement to the level.

        Args:
            requirement: Requirement to add.

        Raises:
            CompetencyPathValidationError: If the competency is already
                required by this level.
        """
        if self.find_requirement(requirement.competency_id) is not None:
            raise CompetencyPathValidationError(
                f"Competency {requirement.competency_id} is already required "
                f"by level {self.name}"
            )
        self.requirements.append(requirement)

    def remove_requirement(self, competency_id: CompetencyId) -> None:
        """
        Remove a competency requirement from the level.

        Args:
            competency_id: Competency whose requirement should be removed.

        Raises:
            CompetencyPathValidationError: If the competency is not required
                by this level.
        """
        requirement = self.find_requirement(competency_id)
        if requirement is None:
            raise CompetencyPathValidationError(
                f"Competency {competency_id} is not required by level {self.name}"
            )
        self.requirements.remove(requirement)

    def find_requirement(
        self, competency_id: CompetencyId
    ) -> CompetencyRequirement | None:
        """
        Return the requirement for a competency, if present.

        Args:
            competency_id: Competency to look up.

        Returns:
            The matching requirement, or ``None`` when absent.
        """
        for requirement in self.requirements:
            if requirement.competency_id == competency_id:
                return requirement
        return None

    def requirements_for_weight(
        self, weight: RequirementWeight
    ) -> list[CompetencyRequirement]:
        """
        Return the requirements with a given weight.

        Args:
            weight: Weight to filter by.

        Returns:
            Requirements matching the weight, preserving insertion order.
        """
        return [
            requirement
            for requirement in self.requirements
            if requirement.weight == weight
        ]

    def __eq__(self, other: object) -> bool:
        """Compare levels by identity."""
        if not isinstance(other, PathLevel):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash levels by identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"PathLevel(id={self.id!r}, name={self.name!r}, "
            f"order={self.order}, requirements={len(self.requirements)})"
        )
