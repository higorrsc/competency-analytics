"""Integration tests for CompetencyGroupModel."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel


@pytest.mark.django_db
class TestCompetencyGroupModel:
    """
    Tests for CompetencyGroupModel persistence, constraints, and representation.
    """

    def test_should_create_group_and_display_str(self) -> None:
        """Competency group persists and returns its name on __str__."""
        category = CategoryModel.objects.create(name="Engineering")
        group = CompetencyGroupModel.objects.create(
            category=category,
            name="Backend",
            description="Backend competencies",
        )
        assert str(group) == "Backend"
        assert group.category == category

    def test_should_enforce_unique_group_name_per_category(self) -> None:
        """Competency groups must have unique names within the same category."""
        category1 = CategoryModel.objects.create(name="Management")
        category2 = CategoryModel.objects.create(name="Product")

        CompetencyGroupModel.objects.create(category=category1, name="Strategy")
        # Same name in different category is allowed
        CompetencyGroupModel.objects.create(category=category2, name="Strategy")

        # Duplicate in same category is rejected
        with pytest.raises(IntegrityError):
            CompetencyGroupModel.objects.create(category=category1, name="Strategy")
