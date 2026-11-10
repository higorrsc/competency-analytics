"""GroupId value object for type-safe competency group identification."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class GroupId:
    """
    Value object representing a unique competency group identifier.

    Immutable identifier using UUID for the middle level of the competency
    hierarchy. Provides type safety and prevents mixing group IDs with other
    entity IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> GroupId:
        """Generate a new unique GroupId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> GroupId:
        """
        Create GroupId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid GroupId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"GroupId({self.value})"
