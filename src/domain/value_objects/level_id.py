"""LevelId value object for type-safe career path level identification."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class LevelId:
    """
    Value object representing a unique career path level identifier.

    Immutable identifier using UUID for levels inside a career path.
    Provides type safety and prevents mixing level IDs with other entity IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> LevelId:
        """Generate a new unique LevelId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> LevelId:
        """
        Create LevelId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid LevelId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"LevelId({self.value})"
