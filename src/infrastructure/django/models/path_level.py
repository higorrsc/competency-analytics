"""PathLevel Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.django.models.competency_path import CompetencyPathModel


class PathLevelModel(models.Model):
    """A progression level within a career path (e.g. Junior, Mid, Senior)."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    path = models.ForeignKey(
        CompetencyPathModel,
        on_delete=models.CASCADE,
        related_name="levels",
    )
    name = models.CharField(max_length=120)
    order = models.PositiveIntegerField()

    class Meta:
        """Model metadata."""

        ordering = ("path", "order")
        db_table = "path_levels"
        verbose_name = "path level"
        verbose_name_plural = "path levels"
        constraints = (
            models.UniqueConstraint(
                fields=["path", "name"],
                name="path_levels_unique_name_per_path",
            ),
            models.UniqueConstraint(
                fields=["path", "order"],
                name="path_levels_unique_order_per_path",
            ),
        )

    def __str__(self) -> str:
        """Return display representation of the level."""
        return f"{self.name} (L{self.order})"
