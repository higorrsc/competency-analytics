"""Competency Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel


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
        verbose_name = "competency"
        verbose_name_plural = "competencies"
        constraints = (
            models.UniqueConstraint(
                fields=["group", "name"],
                name="competencies_unique_name_per_group",
            ),
        )

    def __str__(self) -> str:
        """Return the competency name for display."""
        return str(self.name)
