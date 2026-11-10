"""Collaborator Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models


class CollaboratorModel(models.Model):
    """Employee record in the competency analytics system."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=120)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        """Model metadata."""

        ordering = ("name",)
        db_table = "collaborators"
        verbose_name = "collaborator"
        verbose_name_plural = "collaborators"

    def __str__(self) -> str:
        """Return collaborator name and department."""
        return f"{self.name} ({self.department})"
