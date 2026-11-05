"""Shared test helpers for Django model integration tests."""

from __future__ import annotations


def make_descriptions() -> dict[str, str]:
    """Return standard 1-5 level descriptions for testing."""
    return {
        "1": "Basic awareness",
        "2": "Guided application",
        "3": "Independent execution",
        "4": "Advanced leadership",
        "5": "Strategic mastery",
    }
