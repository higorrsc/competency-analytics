"""Unmanaged Django model mapping the collaborator_competency_history view."""

from __future__ import annotations

import uuid

from django.db import models


class CollaboratorCompetencyHistoryViewModel(models.Model):
    """
    Read-only ORM model backed by the collaborator_competency_history SQL view.

    Provides chronological competency measurements for collaborators with
    previous level and level change calculated via SQL window functions.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collaborator_id = models.UUIDField()
    competency_id = models.UUIDField()
    competency_name = models.CharField(max_length=120)
    evaluation_date = models.DateTimeField()
    period = models.CharField(max_length=60)
    current_level = models.IntegerField()
    previous_level = models.IntegerField(null=True)
    level_change = models.IntegerField(null=True)
    status = models.CharField(max_length=20)

    class Meta:
        """Model metadata for unmanaged database view."""

        managed = False
        db_table = "collaborator_competency_history"
        ordering = ("evaluation_date", "id")
        verbose_name = "collaborator competency history"
        verbose_name_plural = "collaborator competency histories"

    def __str__(self) -> str:
        """Return representation of historical measurement."""
        return (
            f"{self.competency_name}: L{self.current_level} "
            f"({self.period}, {self.status})"
        )
