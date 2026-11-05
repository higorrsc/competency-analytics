"""CompetencyMeasurement Django ORM model."""

from __future__ import annotations

import uuid

from django.db import IntegrityError, models

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.evaluation import EvaluationModel


class CompetencyMeasurementModel(models.Model):
    """A single competency proficiency rating within an evaluation."""

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    evaluation = models.ForeignKey(
        EvaluationModel,
        on_delete=models.CASCADE,
        related_name="measurements",
    )
    competency = models.ForeignKey(
        CompetencyModel,
        on_delete=models.PROTECT,
        related_name="measurements",
    )
    current_level = models.PositiveSmallIntegerField()
    notes = models.TextField(blank=True, default="")
    evidence = models.TextField(blank=True, default="")

    class Meta:
        """Model metadata."""

        ordering = ("evaluation", "competency")
        db_table = "competency_measurements"
        verbose_name = "competency measurement"
        verbose_name_plural = "competency measurements"
        constraints = (
            models.UniqueConstraint(
                fields=["evaluation", "competency"],
                name="competency_measurements_unique_per_evaluation",
            ),
            models.CheckConstraint(
                condition=models.Q(current_level__gte=1, current_level__lte=5),
                name="competency_measurements_level_range",
            ),
        )

    def save(self, *args: object, **kwargs: object) -> None:
        """
        Block adding or updating measurements for finalized evaluations.

        Raises:
            IntegrityError: If the parent evaluation is finalized.
        """
        evaluation = (
            self.evaluation
            if hasattr(self, "evaluation") and self.evaluation is not None
            else EvaluationModel.objects.filter(pk=self.evaluation_id).first()
        )
        if evaluation is not None and evaluation.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            raise IntegrityError("Cannot modify measurements of a finalized evaluation")
        super().save(*args, **kwargs)  # type: ignore[arg-type]

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        """
        Block deleting measurements from finalized evaluations.

        Raises:
            IntegrityError: If the parent evaluation is finalized.
        """
        if self.evaluation.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            raise IntegrityError("Cannot delete measurements of a finalized evaluation")
        return super().delete(*args, **kwargs)  # type: ignore[arg-type]

    def __str__(self) -> str:
        """Return display representation of measurement."""
        return f"{self.competency.name}: L{self.current_level}"
