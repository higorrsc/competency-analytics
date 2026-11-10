"""Category Django Admin configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin

from src.infrastructure.django.models.category import CategoryModel

if TYPE_CHECKING:
    _CategoryAdminBase = admin.ModelAdmin[CategoryModel]
else:
    _CategoryAdminBase = admin.ModelAdmin


class CategoryAdmin(_CategoryAdminBase):
    """Admin configuration for CategoryModel."""

    list_display = ("name", "description")
    search_fields = ("name", "description")
    ordering = ("name",)
