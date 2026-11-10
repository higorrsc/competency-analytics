"""Integration tests for CompetencyPathAdmin and PathLevelAdmin."""

from __future__ import annotations

import pytest
from django.contrib import admin

from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.admin.competency_path_admin import (
    CompetencyPathAdmin,
    CompetencyRequirementInline,
    PathLevelAdmin,
    PathLevelInline,
)
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.mark.django_db
class TestCompetencyPathAdmin:
    """Verify CompetencyPathAdmin and PathLevelAdmin configuration and counts."""

    def test_competency_path_admin_inlines_and_levels_count(self) -> None:
        """CompetencyPathAdmin configures PathLevelInline and computes levels_count."""
        path_admin = CompetencyPathAdmin(CompetencyPathModel, admin.site)
        assert PathLevelInline in path_admin.inlines

        path = CompetencyPathModel.objects.create(name="QA Engineering")
        assert path_admin.levels_count(path) == 0

        PathLevelModel.objects.create(path=path, name="Junior", order=1)
        PathLevelModel.objects.create(path=path, name="Senior", order=2)
        assert path_admin.levels_count(path) == 2

    def test_path_level_admin_inlines_and_requirements_count(self) -> None:
        """PathLevelAdmin configures CompetencyRequirementInline and computes count."""
        level_admin = PathLevelAdmin(PathLevelModel, admin.site)
        assert CompetencyRequirementInline in level_admin.inlines

        cat = CategoryModel.objects.create(name="Quality")
        group = CompetencyGroupModel.objects.create(category=cat, name="Testing")
        comp = CompetencyModel.objects.create(
            category=cat,
            group=group,
            name="E2E Testing",
            description="",
            level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
        )

        path = CompetencyPathModel.objects.create(name="QA Path")
        level = PathLevelModel.objects.create(path=path, name="Lead", order=1)
        assert level_admin.requirements_count(level) == 0

        CompetencyRequirementModel.objects.create(
            path_level=level,
            competency=comp,
            minimum_level=3,
            weight=RequirementWeight.CORE.value,
        )
        assert level_admin.requirements_count(level) == 1
