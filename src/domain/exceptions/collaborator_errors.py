"""Domain exceptions for the collaborator aggregate."""

from src.domain.exceptions.domain_error import DomainError
from src.domain.value_objects.path_id import PathId


class CollaboratorValidationError(DomainError):
    """
    Raised when a collaborator or enrollment violates an invariant.

    Examples include blank identity fields, malformed emails, duplicate path
    enrollments, and more than one active enrollment.
    """


class EnrollmentNotFoundError(DomainError):
    """
    Raised when an enrollment cannot be found inside a collaborator.

    Attributes:
        path_id: Identifier of the path whose enrollment is missing.
    """

    def __init__(self, path_id: PathId) -> None:
        """
        Create an EnrollmentNotFoundError.

        Args:
            path_id: Identifier of the path whose enrollment is missing.
        """
        self.path_id = path_id
        super().__init__(f"Collaborator is not enrolled in path {path_id}")
