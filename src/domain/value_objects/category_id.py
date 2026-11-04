"""CategoryId value object for type-safe competency category identification."""

from dataclasses import dataclass
from uuid import UUID, uuid4


@dataclass(frozen=True)
class CategoryId:
    """
    Value object representing a unique competency category identifier.

    Immutable identifier using UUID for the top level of the competency
    hierarchy. Provides type safety and prevents mixing category IDs with
    other entity IDs.
    """

    value: UUID

    @classmethod
    def generate(cls) -> "CategoryId":
        """Generate a new unique CategoryId."""
        return cls(value=uuid4())

    @classmethod
    def from_string(cls, id_string: str) -> "CategoryId":
        """
        Create CategoryId from string representation.

        Args:
            id_string: String representation of UUID

        Raises:
            ValueError: If string is not a valid UUID format
        """
        try:
            return cls(value=UUID(id_string))
        except (ValueError, AttributeError) as e:
            raise ValueError(f"Invalid CategoryId format: {id_string}") from e

    def __str__(self) -> str:
        """Return string representation of the ID."""
        return str(self.value)

    def __repr__(self) -> str:
        """Return developer-friendly representation."""
        return f"CategoryId({self.value})"
