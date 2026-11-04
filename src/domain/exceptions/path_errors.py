"""Domain exceptions for the career path aggregate."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.value_objects.level_id import LevelId


class CompetencyPathValidationError(DomainError):
    """
    Raised when a career path or one of its levels violates an invariant.

    Examples include blank names, non-positive level ordering, duplicate
    level names or orders, and duplicate competency requirements.
    """


class LevelNotFoundError(DomainError):
    """
    Raised when a level or requirement cannot be found inside a path.

    Attributes:
        level_id: Identifier of the level that could not be found.
    """

    def __init__(self, level_id: LevelId) -> None:
        """
        Create a LevelNotFoundError.

        Args:
            level_id: Identifier of the missing level.
        """
        self.level_id = level_id
        super().__init__(f"Career path level {level_id} was not found")
