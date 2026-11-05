"""CompetencyGroup Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.django.models.category import CategoryModel


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
        verbose_name = "competency group"
        verbose_name_plural = "competency groups"
        constraints = (
            models.UniqueConstraint(
                fields=["category", "name"],
                name="competency_groups_unique_name_per_category",
            ),
        )

    def __str__(self) -> str:
        """Return the group name for display."""
        return str(self.name)
