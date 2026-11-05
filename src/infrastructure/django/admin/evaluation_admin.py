"""Evaluation and CompetencyMeasurement Django Admin configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING

from django.contrib import admin
from django.http import HttpRequest

from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel

if TYPE_CHECKING:
    _MeasurementInlineBase = admin.TabularInline[
        CompetencyMeasurementModel, EvaluationModel
    ]
    _EvalAdminBase = admin.ModelAdmin[EvaluationModel]
else:
    _MeasurementInlineBase = admin.TabularInline
    _EvalAdminBase = admin.ModelAdmin


class CompetencyMeasurementInline(_MeasurementInlineBase):
    """Inline editing for competency measurements within an Evaluation."""

    model = CompetencyMeasurementModel
    extra = 1
    fields = ("competency", "current_level", "notes", "evidence")
    ordering = ("competency__name",)

    def has_add_permission(
        self, request: HttpRequest, obj: EvaluationModel | None = None
    ) -> bool:
        """Prevent adding measurements to finalized evaluations."""
        if obj is not None and obj.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(
        self, request: HttpRequest, obj: EvaluationModel | None = None
    ) -> bool:
        """Prevent modifying measurements in finalized evaluations."""
        if obj is not None and obj.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: EvaluationModel | None = None
    ) -> bool:
        """Prevent deleting measurements from finalized evaluations."""
        if obj is not None and obj.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            return False
        return super().has_delete_permission(request, obj)


class EvaluationAdmin(_EvalAdminBase):
    """
    Admin configuration for EvaluationModel.

    Enforces immutability for finalized evaluations (ACCEPTED and CONTESTED)
    by disabling edits and deletions and marking all fields read-only.
    """

    inlines = (CompetencyMeasurementInline,)
    list_display = (
        "collaborator",
        "evaluator",
        "period",
        "evaluation_date",
        "status",
        "is_finalized_display",
    )
    list_filter = ("status", "collaborator__department", "evaluation_date")
    search_fields = (
        "collaborator__name",
        "collaborator__email",
        "evaluator__name",
        "period",
    )
    ordering = ("-evaluation_date",)

    @admin.display(boolean=True, description="Finalized")
    def is_finalized_display(self, obj: EvaluationModel) -> bool:
        """Indicate whether the evaluation is permanently finalized."""
        return obj.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        )

    def get_readonly_fields(
        self, request: HttpRequest, obj: EvaluationModel | None = None
    ) -> list[str] | tuple[str, ...]:
        """Make all fields read-only once the evaluation is finalized."""
        if obj is not None and obj.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            return [field.name for field in self.model._meta.fields]
        return super().get_readonly_fields(request, obj)

    def has_delete_permission(
        self, request: HttpRequest, obj: EvaluationModel | None = None
    ) -> bool:
        """Prevent deleting finalized evaluations in the admin interface."""
        if obj is not None and obj.status in (
            EvaluationStatus.ACCEPTED.value,
            EvaluationStatus.CONTESTED.value,
        ):
            return False
        return super().has_delete_permission(request, obj)
