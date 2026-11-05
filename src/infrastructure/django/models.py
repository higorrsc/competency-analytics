"""Django models for the competency analytics infrastructure layer.

Models in this module are persistence-only adapters: they never contain
business rules, which stay in the domain layer. Domain entities are mapped
to/from these models exclusively by repository implementations.
"""

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
        verbose_name_plural = "categories"

    def __str__(self) -> str:
        """Return the category name for display."""
        return str(self.name)


class CompetencyGroupModel(models.Model):
    """Second level of the hierarchy: a group inside a category."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.PROTECT,
        related_name="groups",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True, default="")

    class Meta:
        """Model metadata."""

        ordering = ("name",)
        db_table = "competency_groups"
        constraints = (
            models.UniqueConstraint(
                fields=["category", "name"],
                name="competency_groups_unique_name_per_category",
            ),
        )

    def __str__(self) -> str:
        """Return the group name for display."""
        return str(self.name)


class CompetencyModel(models.Model):
    """
    Third level of the hierarchy: a single assessable competency.

    ``level_descriptions`` stores the textual description of each proficiency
    level (1-5) as a JSON object, mirroring the domain value object.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    category = models.ForeignKey(
        CategoryModel,
        on_delete=models.PROTECT,
        related_name="competencies",
    )
    group = models.ForeignKey(
        CompetencyGroupModel,
        on_delete=models.PROTECT,
        related_name="competencies",
    )
    name = models.CharField(max_length=120)
    description = models.TextField()
    level_descriptions = models.JSONField()

    class Meta:
        """Model metadata."""

        ordering = ("name",)
        db_table = "competencies"
        constraints = (
            models.UniqueConstraint(
                fields=["group", "name"],
                name="competencies_unique_name_per_group",
            ),
        )

    def __str__(self) -> str:
        """Return the competency name for display."""
        return str(self.name)
