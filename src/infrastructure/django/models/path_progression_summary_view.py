"""Unmanaged Django model mapping the path_progression_summary view."""

from __future__ import annotations

import uuid

from django.db import models


class PathProgressionSummaryViewModel(models.Model):
    """
    Read-only ORM model backed by the path_progression_summary SQL view.

    Provides aggregated progress towards target path level by comparing
    requirements against the latest finalized evaluation measurements.
    """

    collaborator_id = models.UUIDField(
        primary_key=True, default=uuid.uuid4, editable=False
    )
    path_id = models.UUIDField()
    target_level = models.CharField(max_length=60)
    total_requirements = models.IntegerField()
    requirements_met = models.IntegerField()
    completion_percentage = models.FloatField()

    class Meta:
        """Model metadata for unmanaged database view."""

        managed = False
        db_table = "path_progression_summary"
        verbose_name = "path progression summary"
        verbose_name_plural = "path progression summaries"

    def __str__(self) -> str:
        """Return representation of path progression."""
        return (
            f"Collaborator {self.collaborator_id} -> {self.target_level}: "
            f"{self.completion_percentage}%"
        )
