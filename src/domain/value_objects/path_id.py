"""PathId value object for type-safe career path identification."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class PathId:
    """
    Value object representing a unique career path identifier.

    Immutable identifier using UUID for career paths in the system.
    Provides type safety and prevents mixing path IDs with other entity IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> PathId:
        """Generate a new unique PathId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> PathId:
        """
        Create PathId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid PathId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"PathId({self.value})"
