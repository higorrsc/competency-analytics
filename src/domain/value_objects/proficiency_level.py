"""Shared proficiency scale used by the competency catalog and career paths."""

from __future__ import annotations

#: Valid proficiency levels supported by the system (1 = lowest, 5 = highest).
VALID_LEVELS: frozenset[int] = frozenset({1, 2, 3, 4, 5})


def is_valid_level(level: object) -> bool:
    """
    Return whether a value is a valid proficiency level.

    The check is defensive because levels may come from persistence or
    transport layers where static types cannot be trusted at runtime.
    ``bool`` is rejected explicitly even though it subclasses ``int``.

    Args:
        level: Candidate proficiency level.

    Returns:
        ``True`` when the value is an integer between 1 and 5.
    """
    return (
        isinstance(level, int) and not isinstance(level, bool) and level in VALID_LEVELS
    )
