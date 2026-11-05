"""Integration tests for CategoryAdmin."""

from __future__ import annotations

import pytest
from django.contrib import admin

from src.infrastructure.django.admin.category_admin import CategoryAdmin
from src.infrastructure.django.models.category import CategoryModel


@pytest.mark.django_db
class TestCategoryAdmin:
    """Verify configuration options of CategoryAdmin."""

    def test_category_admin_options(self) -> None:
        """CategoryAdmin defines expected list display, search fields, and ordering."""
        category_admin = CategoryAdmin(CategoryModel, admin.site)
        assert category_admin.list_display == ("name", "description")
        assert category_admin.search_fields == ("name", "description")
        assert category_admin.ordering == ("name",)
