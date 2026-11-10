"""Requirement weight enumeration for career path competency requirements."""

from __future__ import annotations

from enum import StrEnum


class RequirementWeight(StrEnum):
    """
    Weight categorization for competency requirements in career paths.

    Defines the importance level of a competency for a specific career level:
    - CORE: Essential competency, must be met for progression
    - IMPORTANT: Strongly recommended competency
    - DESIRABLE: Nice-to-have competency
    """

    CORE = "CORE"
    IMPORTANT = "IMPORTANT"
    DESIRABLE = "DESIRABLE"

    def priority_order(self) -> int:
        """
        Return numeric priority for sorting (lower is higher priority).

        Used for ordering gaps: CORE gaps should be addressed first,
        then IMPORTANT, then DESIRABLE.
        """
        priority_map = {
            RequirementWeight.CORE: 1,
            RequirementWeight.IMPORTANT: 2,
            RequirementWeight.DESIRABLE: 3,
        }
        return priority_map[self]

    def __lt__(self, other: object) -> bool:
        """Compare weights by priority (CORE < IMPORTANT < DESIRABLE)."""
        if not isinstance(other, RequirementWeight):
            return NotImplemented
        return self.priority_order() < other.priority_order()

    def __le__(self, other: object) -> bool:
        """Compare weights by priority or equality."""
        if not isinstance(other, RequirementWeight):
            return NotImplemented
        return self.priority_order() <= other.priority_order()

    def __gt__(self, other: object) -> bool:
        """Compare weights by priority (DESIRABLE > IMPORTANT > CORE)."""
        if not isinstance(other, RequirementWeight):
            return NotImplemented
        return self.priority_order() > other.priority_order()

    def __ge__(self, other: object) -> bool:
        """Compare weights by priority or equality."""
        if not isinstance(other, RequirementWeight):
            return NotImplemented
        return self.priority_order() >= other.priority_order()
