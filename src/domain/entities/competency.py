"""Competency entity belonging to the hierarchical competency catalog."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from src.domain.exceptions.competency_errors import CompetencyValidationError
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId
from src.domain.value_objects.proficiency_level import VALID_LEVELS, is_valid_level


@dataclass(eq=False)
class Competency:
    """
    A single competency in the hierarchical competency catalog.

    The catalog is organized in three fixed levels:
    Category -> CompetencyGroup -> Competency. A competency stores references
    to its category and group by identifier, keeping aggregate boundaries
    loose while preserving the hierarchy.

    Every competency MUST define a textual description for each of the five
    proficiency levels (1-5). Those descriptions make the numeric scale
    meaningful during evaluations and gap analysis.

    Identity is based on ``id`` only: two competency instances represent the
    same competency when their identifiers match, regardless of other fields.
    """

    id: CompetencyId
    name: str
    description: str
    category_id: CategoryId
    group_id: GroupId
    level_descriptions: dict[int, str]

    def __post_init__(self) -> None:
        """Validate catalog invariants immediately after construction."""
        self._validate_name(self.name)
        self._validate_level_descriptions(self.level_descriptions)
        self.name = self.name.strip()
        self.description = self.description.strip()

    @staticmethod
    def _validate_name(name: object) -> None:
        """
        Validate that a competency name is present and meaningful.

        The parameter is typed as ``object`` because this guard also protects
        the aggregate from data coming from persistence or transport layers,
        where static types cannot be trusted at runtime.

        Args:
            name: Proposed competency name.

        Raises:
            CompetencyValidationError: If the name is empty or whitespace only.
        """
        if not isinstance(name, str) or not name.strip():
            raise CompetencyValidationError("Competency name must not be empty")

    @staticmethod
    def _validate_level_descriptions(level_descriptions: object) -> None:
        """
        Validate that all five proficiency levels are described.

        The parameter is typed as ``object`` because this guard also protects
        the aggregate from data coming from persistence or transport layers,
        where static types cannot be trusted at runtime.

        Args:
            level_descriptions: Mapping from level number (1-5) to description.

        Raises:
            CompetencyValidationError: If levels are missing, unexpected, or
                contain blank descriptions.
        """
        if not isinstance(level_descriptions, dict):
            raise CompetencyValidationError(
                "Level descriptions must be a mapping of level to description"
            )

        mapping = cast(dict[object, object], level_descriptions)
        provided_levels: set[int] = set()

        for level, description in mapping.items():
            if not isinstance(level, int) or isinstance(level, bool):
                raise CompetencyValidationError(
                    f"Proficiency level must be an integer, got {type(level).__name__}"
                )
            provided_levels.add(level)
            if not isinstance(description, str) or not description.strip():
                raise CompetencyValidationError(
                    f"Description for proficiency level {level} must not be empty"
                )

        missing_levels = VALID_LEVELS - provided_levels
        unexpected_levels = provided_levels - VALID_LEVELS

        if missing_levels:
            missing = ", ".join(str(level) for level in sorted(missing_levels))
            raise CompetencyValidationError(
                f"Missing descriptions for proficiency levels: {missing}"
            )

        if unexpected_levels:
            unexpected = ", ".join(str(level) for level in sorted(unexpected_levels))
            raise CompetencyValidationError(
                f"Unexpected proficiency levels: {unexpected}"
            )

    def description_for_level(self, level: int) -> str:
        """
        Return the proficiency level description.

        Args:
            level: Proficiency level between 1 and 5.

        Returns:
            The textual description associated with the level.

        Raises:
            CompetencyValidationError: If the level is outside 1-5.
        """
        if not is_valid_level(level):
            raise CompetencyValidationError(
                f"Invalid proficiency level {level}; expected one of "
                f"{sorted(VALID_LEVELS)}"
            )
        return self.level_descriptions[level]

    def update_details(self, name: str, description: str) -> None:
        """
        Update the competency name and description.

        Existing level descriptions, category, and group references are
        preserved so that career paths and evaluations keep working.

        Args:
            name: New competency name.
            description: New competency description.

        Raises:
            CompetencyValidationError: If the new name is empty.
        """
        self._validate_name(name)
        self.name = name.strip()
        self.description = description.strip()

    def update_level_descriptions(self, level_descriptions: dict[int, str]) -> None:
        """
        Replace the proficiency level descriptions.

        Historical evaluation measurements store numeric levels, not the
        descriptions, so changing descriptions does not alter history.

        Args:
            level_descriptions: New mapping from level number (1-5) to text.

        Raises:
            CompetencyValidationError: If the mapping is incomplete or invalid.
        """
        self._validate_level_descriptions(level_descriptions)
        self.level_descriptions = dict(level_descriptions)

    def belongs_to_category(self, category_id: CategoryId) -> bool:
        """Return whether the competency belongs to the given category."""
        return self.category_id == category_id

    def belongs_to_group(self, group_id: GroupId) -> bool:
        """Return whether the competency belongs to the given group."""
        return self.group_id == group_id

    def __eq__(self, other: object) -> bool:
        """Compare competencies by identity."""
        if not isinstance(other, Competency):
            return NotImplemented
        return self.id == other.id

    def __hash__(self) -> int:
        """Hash competencies by identity so they can be used in sets."""
        return hash(self.id)

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        return (
            f"Competency(id={self.id!r}, name={self.name!r}, "
            f"category_id={self.category_id!r}, group_id={self.group_id!r})"
        )
