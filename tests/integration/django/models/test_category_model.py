"""Integration tests for CategoryModel."""

from __future__ import annotations

import pytest
from django.db import IntegrityError

from src.infrastructure.django.models.category import CategoryModel


@pytest.mark.django_db
class TestCategoryModel:
    """Tests for CategoryModel persistence, constraints, and string representation."""

    def test_should_create_category_and_display_str(self) -> None:
        """Category model persists correctly and returns expected __str__."""
        category = CategoryModel.objects.create(
            name="Engineering", description="Tech skills"
        )
        assert str(category) == "Engineering"
        assert category.description == "Tech skills"

    def test_should_enforce_unique_category_name(self) -> None:
        """Category names must be unique."""
        CategoryModel.objects.create(name="Architecture")
        with pytest.raises(IntegrityError):
            CategoryModel.objects.create(name="Architecture")

    def test_should_respect_meta_ordering_by_name(self) -> None:
        """Categories are ordered alphabetically by name."""
        cat_b = CategoryModel.objects.create(name="Beta Category")
        cat_a = CategoryModel.objects.create(name="Alpha Category")
        assert list(CategoryModel.objects.all()) == [cat_a, cat_b]
