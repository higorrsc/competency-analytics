"""Evaluation Django ORM model with immutability guarantees."""

from __future__ import annotations

import uuid

from django.db import IntegrityError, models

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.collaborator import CollaboratorModel


class EvaluationModel(models.Model):
    """
    Formal competency evaluation with immutable finalized states.

    Finalized evaluations (ACCEPTED or CONTESTED) cannot be updated or deleted.
    """

    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    collaborator = models.ForeignKey(
        CollaboratorModel,
        on_delete=models.PROTECT,
        related_name="evaluations",
    )
    evaluator = models.ForeignKey(
        CollaboratorModel,
        on_delete=models.PROTECT,
        related_name="conducted_evaluations",
    )
    period = models.CharField(max_length=60)
    evaluation_date = models.DateTimeField()
    status = models.CharField(
        max_length=20,
        choices=[(s.value, s.name) for s in EvaluationStatus],
        default=EvaluationStatus.DRAFT.value,
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    response_date = models.DateTimeField(null=True, blank=True)
    response_notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """Model metadata."""

        ordering = ("-evaluation_date",)
        db_table = "evaluations"
        verbose_name = "evaluation"
        verbose_name_plural = "evaluations"
        constraints = (
            models.CheckConstraint(
                condition=models.Q(
                    status__in=[
                        EvaluationStatus.DRAFT.value,
                        EvaluationStatus.COMPLETED.value,
                        EvaluationStatus.ACCEPTED.value,
                        EvaluationStatus.CONTESTED.value,
                    ]
                ),
                name="evaluations_status_valid",
            ),
        )

    def save(self, *args: object, **kwargs: object) -> None:
        """
        Enforce model-level immutability for finalized evaluations.

        Raises:
            IntegrityError: If attempting to modify a finalized evaluation.
        """
        if self.pk:
            old = EvaluationModel.objects.filter(pk=self.pk).only("status").first()
            if old is not None and old.status in (
                EvaluationStatus.ACCEPTED.value,
                EvaluationStatus.CONTESTED.value,
            ):
                raise IntegrityError("Cannot modify finalized evaluation")
        super().save(*args, **kwargs)  # type: ignore[arg-type]

    def delete(self, *args: object, **kwargs: object) -> tuple[int, dict[str, int]]:
        """
        Prevent deletion of finalized evaluations.

        Raises:
            IntegrityError: If attempting to delete a finalized evaluation.
        """
        if self.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            raise IntegrityError("Cannot delete finalized evaluation")
        return super().delete(*args, **kwargs)  # type: ignore[arg-type]

    def __str__(self) -> str:
        """Return display string for evaluation."""
        return f"{self.collaborator.name} - {self.period} ({self.status})"
