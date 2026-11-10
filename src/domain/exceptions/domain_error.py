"""Base domain exception hierarchy."""


class DomainError(Exception):
    """
    Base class for all domain-level errors.

    Domain errors represent violations of business rules or invariants.
    They are framework independent and must never leak infrastructure
    details such as database or HTTP errors.
    """
