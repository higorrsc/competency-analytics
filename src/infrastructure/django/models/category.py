"""Category Django ORM model for competency hierarchy."""

from __future__ import annotations

import uuid

from django.db import models


class CategoryModel(models.Model):
    """Top level of the competency catalog hierarchy."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        """Model metadata."""

        ordering = ("name",)
        db_table = "categories"
        verbose_name = "category"
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        """Return the category name for display."""
        return str(self.name)
