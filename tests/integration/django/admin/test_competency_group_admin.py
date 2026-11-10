"""Integration tests for CompetencyGroupAdmin."""

from __future__ import annotations

import pytest
from django.contrib import admin

from src.infrastructure.django.admin.competency_group_admin import (
    CompetencyGroupAdmin,
)
from src.infrastructure.django.models.competency_group import CompetencyGroupModel


@pytest.mark.django_db
class TestCompetencyGroupAdmin:
    """Verify configuration options of CompetencyGroupAdmin."""

    def test_competency_group_admin_options(self) -> None:
        """CompetencyGroupAdmin defines expected filters, fields, and ordering."""
        group_admin = CompetencyGroupAdmin(CompetencyGroupModel, admin.site)
        assert group_admin.list_display == ("name", "category", "description")
        assert group_admin.list_filter == ("category",)
        assert group_admin.search_fields == (
            "name",
            "category__name",
            "description",
        )
        assert group_admin.ordering == ("category__name", "name")
