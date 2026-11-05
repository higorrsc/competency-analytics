"""Integration tests for CompetencyModel."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from tests.integration.django.models.helpers import make_descriptions


@pytest.mark.django_db
class TestCompetencyModel:
    """Tests for CompetencyModel persistence, constraints, and string representation."""

    def test_should_create_competency_and_display_str(self) -> None:
        """Competency persists with level descriptions and displays name on __str__."""
        category = CategoryModel.objects.create(name="Engineering")
        group = CompetencyGroupModel.objects.create(category=category, name="Backend")
        competency = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Python",
            description="Core language",
            level_descriptions=make_descriptions(),
        )
        assert str(competency) == "Python"
        assert competency.level_descriptions["1"] == "Basic awareness"

    def test_should_enforce_unique_competency_name_per_group(self) -> None:
        """Competencies must have unique names within the same group."""
        cat = CategoryModel.objects.create(name="Data")
        group1 = CompetencyGroupModel.objects.create(category=cat, name="Analytics")
        group2 = CompetencyGroupModel.objects.create(category=cat, name="Engineering")

        CompetencyModel.objects.create(
            category=cat,
            group=group1,
            name="SQL",
            description="Queries",
            level_descriptions=make_descriptions(),
        )
        # Same name in different group is allowed
        CompetencyModel.objects.create(
            category=cat,
            group=group2,
            name="SQL",
            description="DB dev",
            level_descriptions=make_descriptions(),
        )

        # Duplicate in same group is rejected
        with pytest.raises(IntegrityError):
            CompetencyModel.objects.create(
                category=cat,
                group=group1,
                name="SQL",
                description="Duplicate",
                level_descriptions=make_descriptions(),
            )
