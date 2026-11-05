"""CompetencyRequirement Django ORM model."""

from __future__ import annotations

import uuid

from django.db import models

from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.path_level import PathLevelModel


class CompetencyRequirementModel(models.Model):
    """Requirement linking a path level to a minimum competency proficiency."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    path_level = models.ForeignKey(
        PathLevelModel,
        on_delete=models.CASCADE,
        related_name="requirements",
    )
    competency = models.ForeignKey(
        CompetencyModel,
        on_delete=models.PROTECT,
        related_name="path_requirements",
    )
    minimum_level = models.PositiveSmallIntegerField()
    weight = models.CharField(
        max_length=20,
        choices=[(w.value, w.name) for w in RequirementWeight],
    )

    class Meta:
        """Model metadata."""

        ordering = ("path_level", "competency")
        db_table = "competency_requirements"
        verbose_name = "competency requirement"
        verbose_name_plural = "competency requirements"
        constraints = (
            models.UniqueConstraint(
                fields=["path_level", "competency"],
                name="competency_requirements_unique_per_level",
            ),
            models.CheckConstraint(
                condition=models.Q(minimum_level__gte=1, minimum_level__lte=5),
                name="competency_requirements_min_level_range",
            ),
        )

    def __str__(self) -> str:
        """Return display string for the requirement."""
        return (
            f"{self.path_level.name} requires {self.competency.name} "
            f">= {self.minimum_level} ({self.weight})"
        )
