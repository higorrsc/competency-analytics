"""CompetencyGroup Django Admin configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin

from src.infrastructure.django.models.competency_group import CompetencyGroupModel

if TYPE_CHECKING:
    _CompetencyGroupAdminBase = admin.ModelAdmin[CompetencyGroupModel]
else:
    _CompetencyGroupAdminBase = admin.ModelAdmin


class CompetencyGroupAdmin(_CompetencyGroupAdminBase):
    """Admin configuration for CompetencyGroupModel."""

    list_display = ("name", "category", "description")
    list_filter = ("category",)
    search_fields = ("name", "category__name", "description")
    ordering = ("category__name", "name")
