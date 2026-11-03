"""CollaboratorId value object for type-safe collaborator identification."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CollaboratorId:
    """
    Value object representing a unique collaborator identifier.

    Immutable identifier using UUID for collaborators in the system.
    Provides type safety and prevents mixing collaborator IDs with other entity IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> "CollaboratorId":
        """Generate a new unique CollaboratorId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "CollaboratorId":
        """
        Create CollaboratorId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid CollaboratorId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"CollaboratorId({self.value})"
