"""CompetencyPath Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models


class CompetencyPathModel(models.Model):
    """Career progression path definition."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=120, unique=True)
    description = models.TextField(blank=True, default="")

    class Meta:
        """Model metadata."""

        ordering = ("name",)
        db_table = "competency_paths"
        verbose_name = "competency path"
        verbose_name_plural = "competency paths"

    def __str__(self) -> str:
        """Return the path name for display."""
        return str(self.name)
