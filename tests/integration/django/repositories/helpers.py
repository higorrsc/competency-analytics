"""Shared test helpers for Django repository integration tests."""

from __future__ import annotations

from src.domain.entities.competency import Competency
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId


def make_descriptions() -> dict[int, str]:
    """Return standard 1-5 level descriptions for testing."""
    return {
        1: "Basic awareness",
        2: "Guided application",
        3: "Independent execution",
        4: "Advanced leadership",
        5: "Strategic mastery",
    }


def make_competency(
    *,
    competency_id: CompetencyId | None = None,
    category_id: CategoryId | None = None,
    group_id: GroupId | None = None,
    name: str = "Python Programming",
) -> Competency:
    """Helper to create a valid domain Competency entity."""
    return Competency(
        id=competency_id or CompetencyId.generate(),
        name=name,
        description="Core language skills",
        category_id=category_id or CategoryId.generate(),
        group_id=group_id or GroupId.generate(),
        level_descriptions=make_descriptions(),
    )
