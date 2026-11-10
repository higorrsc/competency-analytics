"""CompetencyPath aggregate root for career progression structures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import cast

from src.domain.entities.path_level import PathLevel
from src.domain.exceptions.path_errors import (
    CompetencyPathValidationError,
    LevelNotFoundError,
)
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.path_id import PathId


@dataclass(eq=False)
class CompetencyPath:
    """
    Aggregate root describing a career progression structure.

    A path is an ordered sequence of levels (for example Junior -> Mid ->
    Senior). Each level carries the competency requirements a collaborator
    must satisfy to reach it.

    Invariants enforced by this aggregate:

    - level names are unique within the path (case-insensitive);
    - level orders are unique and form the sequence 1..N without gaps;
    - level identities are unique.

    The aggregate intentionally does not know about collaborators or
    enrollments: those are a separate aggregate. Deleting a level that is
    targeted by an enrollment is an application-level policy, because it
    requires loading enrollment data.
    """

    id: PathId
    name: str
    description: str
    levels: list[PathLevel] = field(default_factory=list[PathLevel])

    def __post_init__(self) -> None:
        """Validate path invariants immediately after construction."""
        self._validate_name(self.name)
        self._validate_levels(self.levels)
        self.name = self.name.strip()
        self.description = self.description.strip()

    @staticmethod
    def _validate_name(name: object) -> None:
        """
        Validate that the path name is present and meaningful.

        Args:
            name: Proposed path name.

        Raises:
            CompetencyPathValidationError: If the name is blank.
        """
        if not isinstance(name, str) or not name.strip():
            raise CompetencyPathValidationError("Career path name must not be empty")

    @staticmethod
    def _validate_levels(levels: object) -> None:
        """
        Validate level identity, naming, ordering, and sequential continuity.

        Args:
            levels: Proposed list of levels.

        Raises:
            CompetencyPathValidationError: If the value is not a list, contains
                non-level items, repeats a level identity, name, or order, or
                the orders are not the sequence 1..N.
        """
        if not isinstance(levels, list):
            raise CompetencyPathValidationError(
                "Career path levels must be a list of PathLevel"
            )

        seen_ids: set[LevelId] = set()
        seen_names: set[str] = set()
        seen_orders: set[int] = set()

        for level in cast(list[object], levels):
            if not isinstance(level, PathLevel):
                raise CompetencyPathValidationError(
                    "Career path levels must be PathLevel instances"
                )
            if level.id in seen_ids:
                raise CompetencyPathValidationError(
                    f"Duplicate level identity {level.id}"
                )
            normalized_name = level.name.casefold()
            if normalized_name in seen_names:
                raise CompetencyPathValidationError(
                    f"Duplicate level name {level.name!r}"
                )
            if level.order in seen_orders:
                raise CompetencyPathValidationError(
                    f"Duplicate level order {level.order}"
                )
            seen_ids.add(level.id)
            seen_names.add(normalized_name)
            seen_orders.add(level.order)

        expected_orders = list(range(1, len(seen_orders) + 1))
        actual_orders = sorted(seen_orders)
        if actual_orders != expected_orders:
            raise CompetencyPathValidationError(
                f"Level orders must be sequential starting at 1; got {actual_orders}"
            )

    def add_level(self, level: PathLevel) -> None:
        """
        Add a level to the path, preserving all ordering invariants.

        The candidate list is validated before mutation, so a rejected level
        leaves the aggregate unchanged.

        Args:
            level: Level to add.

        Raises:
            CompetencyPathValidationError: If the level repeats an identity,
                name, or order, or breaks sequential ordering.
        """
        candidate_levels = [*self.levels, level]
        self._validate_levels(candidate_levels)
        self.levels.append(level)

    def find_level(self, level_id: LevelId) -> PathLevel | None:
        """
        Return a level by identifier.

        Args:
            level_id: Identifier of the level.

        Returns:
            The matching level, or ``None`` when absent.
        """
        for level in self.levels:
            if level.id == level_id:
                return level
        return None

    def require_level(self, level_id: LevelId) -> PathLevel:
        """
        Return a level by identifier or raise when it does not exist.

        Args:
            level_id: Identifier of the level.

        Returns:
            The matching level.

        Raises:
            LevelNotFoundError: If no level has the given identifier.
        """
        level = self.find_level(level_id)
        if level is None:
            raise LevelNotFoundError(level_id)
        return level

    def find_level_by_name(self, name: str) -> PathLevel | None:
        """
        Return a level by name, ignoring case.

        Args:
            name: Level name to look up.

        Returns:
            The matching level, or ``None`` when absent.
        """
        normalized = name.strip().casefold()
        for level in self.levels:
            if level.name.casefold() == normalized:
                return level
        return None

    def levels_in_order(self) -> list[PathLevel]:
        """
        Return the levels sorted by their order.

        Returns:
            A new list ordered from the lowest to the highest level.
        """
        return sorted(self.levels, key=lambda level: level.order)

    def update_details(self, name: str, description: str) -> None:
        """
        Update the path name and description.

        Levels and their requirements are preserved so existing enrollments
        and gap calculations keep working.

        Args:
            name: New path name.
            description: New path description.

        Raises:
            CompetencyPathValidationError: If the new name is blank.
        """
        self._validate_name(name)
        self.name = name.strip()
        self.description = description.strip()

    def __eq__(self, other: object) -> bool:
        """Compare paths by identity."""
        if not isinstance(other, CompetencyPath):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash paths by identity."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"CompetencyPath(id={self.id!r}, name={self.name!r}, "
            f"levels={len(self.levels)})"
        )
