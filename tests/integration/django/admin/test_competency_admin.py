"""Integration tests for CompetencyAdmin."""

from __future__ import annotations

import pytest
from django.contrib import admin

from src.infrastructure.django.admin.competency_admin import CompetencyAdmin
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel


@pytest.mark.django_db
class TestCompetencyAdmin:
    """Verify configuration options and methods of CompetencyAdmin."""

    def test_competency_admin_options(self) -> None:
        """CompetencyAdmin defines expected filters, display, and search fields."""
        comp_admin = CompetencyAdmin(CompetencyModel, admin.site)
        assert comp_admin.list_display == (
            "name",
            "group",
            "category_display",
            "description",
        )
        assert comp_admin.list_filter == ("group__category", "group")
        assert "name" in comp_admin.search_fields

    def test_category_display_method(self) -> None:
        """category_display method resolves the category name through group relation."""
        category = CategoryModel.objects.create(name="Tech Architecture")
        group = CompetencyGroupModel.objects.create(
            category=category, name="Distributed Systems"
        )
        competency = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Microservices",
            description="",
            level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
        )

        comp_admin = CompetencyAdmin(CompetencyModel, admin.site)
        assert comp_admin.category_display(competency) == "Tech Architecture"
