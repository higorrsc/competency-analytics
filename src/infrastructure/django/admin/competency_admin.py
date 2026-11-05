"""Competency Django Admin configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin

from src.infrastructure.django.models.competency import CompetencyModel

if TYPE_CHECKING:
    _CompetencyAdminBase = admin.ModelAdmin[CompetencyModel]
else:
    _CompetencyAdminBase = admin.ModelAdmin


class CompetencyAdmin(_CompetencyAdminBase):
    """Admin configuration for CompetencyModel with hierarchical catalog display."""

    list_display = ("name", "group", "category_display", "description")
    list_filter = ("group__category", "group")
    search_fields = (
        "name",
        "description",
        "group__name",
        "group__category__name",
    )
    ordering = ("group__category__name", "group__name", "name")

    @admin.display(description="Category", ordering="group__category__name")
    def category_display(self, obj: CompetencyModel) -> str:
        """Display the category to which the competency belongs."""
        return str(obj.group.category.name)
