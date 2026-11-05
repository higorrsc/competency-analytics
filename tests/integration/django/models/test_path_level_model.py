"""Integration tests for PathLevelModel."""

from __future__ import annotations

import pytest
from django.db import IntegrityError, transaction

from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.path_level import PathLevelModel


@pytest.mark.django_db
class TestPathLevelModel:
    """Tests for PathLevelModel persistence, unique constraints, and ordering."""

    def test_should_create_level_and_display_str(self) -> None:
        """Path level persists and returns formatted level name on __str__."""
        path = CompetencyPathModel.objects.create(name="Engineering")
        level = PathLevelModel.objects.create(path=path, name="Junior", order=1)
        assert str(level) == "Junior (L1)"
        assert level.order == 1

    def test_should_enforce_unique_level_order_and_name_per_path(self) -> None:
        """Path levels must have unique names and orders within the same path."""
        path = CompetencyPathModel.objects.create(name="Engineering")
        PathLevelModel.objects.create(path=path, name="Junior", order=1)

        # Duplicate name
        with transaction.atomic(), pytest.raises(IntegrityError):
            PathLevelModel.objects.create(path=path, name="Junior", order=2)

        # Duplicate order
        with transaction.atomic(), pytest.raises(IntegrityError):
            PathLevelModel.objects.create(path=path, name="Pleno", order=1)
