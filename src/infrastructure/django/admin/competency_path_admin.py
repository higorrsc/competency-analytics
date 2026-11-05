"""CompetencyPath and PathLevel Django Admin configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin

from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.path_level import PathLevelModel

if TYPE_CHECKING:
    _ReqInlineBase = admin.TabularInline[CompetencyRequirementModel, PathLevelModel]
    _LevelInlineBase = admin.TabularInline[PathLevelModel, CompetencyPathModel]
    _PathAdminBase = admin.ModelAdmin[CompetencyPathModel]
    _LevelAdminBase = admin.ModelAdmin[PathLevelModel]
else:
    _ReqInlineBase = admin.TabularInline
    _LevelInlineBase = admin.TabularInline
    _PathAdminBase = admin.ModelAdmin
    _LevelAdminBase = admin.ModelAdmin


class CompetencyRequirementInline(_ReqInlineBase):
    """Inline editing for competency requirements under a career level."""

    model = CompetencyRequirementModel
    extra = 1
    fields = ("competency", "minimum_level", "weight")
    ordering = ("competency__name",)


class PathLevelInline(_LevelInlineBase):
    """Inline editing for career path levels directly within CompetencyPath."""

    model = PathLevelModel
    extra = 1
    fields = ("name", "order")
    ordering = ("order",)


class CompetencyPathAdmin(_PathAdminBase):
    """Admin configuration for CompetencyPathModel with inline level editing."""

    inlines = (PathLevelInline,)
    list_display = ("name", "description", "levels_count")
    search_fields = ("name", "description")
    ordering = ("name",)

    @admin.display(description="Levels Count")
    def levels_count(self, obj: CompetencyPathModel) -> int:
        """Return the number of configured levels for the career path."""
        return PathLevelModel.objects.filter(path_id=obj.id).count()


class PathLevelAdmin(_LevelAdminBase):
    """Admin configuration for PathLevelModel with inline requirements."""

    inlines = (CompetencyRequirementInline,)
    list_display = ("name", "path", "order", "requirements_count")
    list_filter = ("path",)
    search_fields = ("name", "path__name")
    ordering = ("path__name", "order")

    @admin.display(description="Requirements Count")
    def requirements_count(self, obj: PathLevelModel) -> int:
        """Return the number of competency requirements configured for the level."""
        return CompetencyRequirementModel.objects.filter(path_level_id=obj.id).count()
