"""PathEnrollment Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models

from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel


class PathEnrollmentModel(models.Model):
    """Enrollment record of a collaborator in a career path."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    collaborator = models.ForeignKey(
        CollaboratorModel,
        on_delete=models.CASCADE,
        related_name="enrollments",
    )
    path = models.ForeignKey(
        CompetencyPathModel,
        on_delete=models.PROTECT,
        related_name="enrollments",
    )
    target_level = models.CharField(max_length=120)
    is_active = models.BooleanField(default=True)
    enrolled_at = models.DateTimeField()

    class Meta:
        """Model metadata."""

        ordering = ("-enrolled_at",)
        db_table = "path_enrollments"
        verbose_name = "path enrollment"
        verbose_name_plural = "path enrollments"
        unique_together = (("collaborator", "path"),)

    def __str__(self) -> str:
        """Return display representation of enrollment."""
        state = "Active" if self.is_active else "Inactive"
        return (
            f"{self.collaborator.name} - {self.path.name} "
            f"({self.target_level}) [{state}]"
        )
