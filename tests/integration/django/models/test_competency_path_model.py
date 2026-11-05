"""Integration tests for CompetencyPathModel."""

from __future__ import annotations

import pytest

from src.infrastructure.django.models.competency_path import CompetencyPathModel


@pytest.mark.django_db
class TestCompetencyPathModel:
    """Tests for CompetencyPathModel persistence and string representation."""

    def test_should_create_path_and_display_str(self) -> None:
        """Path persists and returns its name on __str__."""
        path = CompetencyPathModel.objects.create(
            name="Product Design", description="Design track"
        )
        assert str(path) == "Product Design"
        assert path.description == "Design track"
