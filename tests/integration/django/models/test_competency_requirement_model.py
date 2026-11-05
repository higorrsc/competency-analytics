"""Integration tests for CompetencyRequirementModel."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.path_level import PathLevelModel
from tests.integration.django.models.helpers import make_descriptions


@pytest.mark.django_db
class TestCompetencyRequirementModel:
    """
    Tests for CompetencyRequirementModel persistence and constraints.
    """

    def test_should_create_requirement_and_display_str(self) -> None:
        """Requirement persists with level and weight."""
        category = CategoryModel.objects.create(name="Design")
        group = CompetencyGroupModel.objects.create(category=category, name="UX")
        competency = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="User Research",
            description="Interviews",
            level_descriptions=make_descriptions(),
        )
        path = CompetencyPathModel.objects.create(name="Product Design")
        level = PathLevelModel.objects.create(path=path, name="Junior", order=1)

        req = CompetencyRequirementModel.objects.create(
            path_level=level,
            competency=competency,
            minimum_level=2,
            weight=RequirementWeight.CORE.value,
        )
        assert "Junior" in str(req)
        assert "User Research" in str(req)
        assert req.minimum_level == 2

    def test_should_enforce_unique_requirement_per_level(self) -> None:
        """A level cannot require the same competency multiple times."""
        category = CategoryModel.objects.create(name="Tech")
        group = CompetencyGroupModel.objects.create(category=category, name="Core")
        comp = CompetencyModel.objects.create(
            category=category,
            group=group,
            name="Git",
            description="VCS",
            level_descriptions=make_descriptions(),
        )
        path = CompetencyPathModel.objects.create(name="Developer")
        level = PathLevelModel.objects.create(path=path, name="Junior", order=1)

        CompetencyRequirementModel.objects.create(
            path_level=level,
            competency=comp,
            minimum_level=1,
            weight=RequirementWeight.CORE.value,
        )

        with pytest.raises(IntegrityError):
            CompetencyRequirementModel.objects.create(
                path_level=level,
                competency=comp,
                minimum_level=3,
                weight=RequirementWeight.IMPORTANT.value,
            )
