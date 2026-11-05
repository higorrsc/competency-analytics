"""Application-level errors translated from domain failures.

Application use cases orchestrate domain behavior and must not leak
infrastructure or domain exception types directly to the presentation layer.
This module defines the error vocabulary application results can express, so
HTTP/API adapters can map every failure deterministically.
"""

from __future__ import annotations


class ApplicationError(Exception):
    """
    Base class for all application-level errors.

    Presentation layers may catch this type generically when no more specific
    handling is required. Concrete subclasses group failures by the HTTP
    semantics they should eventually map to: validation, conflict, not found.
    """

    def __init__(self, message: str) -> None:
        """
        Initialize the error with a human-readable message.

        Args:
            message: Description of what failed and, when useful, why.
        """
        super().__init__(message)
        self.message = message


class ValidationError(ApplicationError):
    """
    Raised when use case input or a business operation is invalid.

    Maps to validation failures such as blank required data, values outside
    the supported scale, or business rules that reject the requested change.
    """

    def __init__(self, message: str) -> None:
        """
        Initialize the validation error.

        Args:
            message: Description of the rejected input or business rule.
        """
        super().__init__(message)


class ConflictError(ApplicationError):
    """
    Raised when the requested operation is not allowed in the current state.

    Examples include mutating a finalized evaluation or re-enrolling in a path
    the collaborator is already enrolled in.
    """

    def __init__(self, message: str) -> None:
        """
        Initialize the conflict error.

        Args:
            message: Description of the state conflict.
        """
        super().__init__(message)


class NotFoundError(ApplicationError):
    """
    Raised when a referenced entity does not exist.

    Carries the entity type and the identifier that could not be resolved, so
    API layers can produce precise messages without parsing strings.
    """

    def __init__(self, entity: str, identifier: object) -> None:
        """
        Initialize the not-found error.

        Args:
            entity: Human-readable entity name, for example ``"Collaborator"``.
            identifier: The identifier that could not be resolved.
        """
        self.entity = entity
        self.identifier = identifier
        super().__init__(f"{entity} not found: {identifier}")
