"""Domain exceptions for competency gap analysis."""

from src.domain.exceptions.domain_error import DomainError


class GapAnalysisError(DomainError):
    """
    Raised when gap analysis cannot be performed.

    Examples include using a non-finalized evaluation as the baseline or
    creating an inconsistent gap value object.
    """
