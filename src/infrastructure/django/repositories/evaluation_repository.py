"""Django ORM implementation of the EvaluationRepository protocol."""

from __future__ import annotations

from django.db import IntegrityError, transaction

from src.domain.entities.competency_measurement import CompetencyMeasurement
from src.domain.entities.evaluation import Evaluation
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.evaluation_id import EvaluationId
from src.domain.value_objects.evaluation_status import EvaluationStatus
from src.domain.value_objects.measurement_id import MeasurementId
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel


class DjangoEvaluationRepository:
    """
    Persistence adapter for the Evaluation aggregate root.

    Mapping strategy:
    - Root entity `Evaluation` maps to `EvaluationModel`.
    - Inner entities `CompetencyMeasurement` map to `CompetencyMeasurementModel`.
    - Preserves evaluation status transitions and response notes.
    - `find_latest_finalized_for_collaborator` filters exclusively on
      finalized states (ACCEPTED or CONTESTED) to provide the baseline for
      gap analysis and temporal tracking.
    """

    def save(self, evaluation: Evaluation) -> None:
        """
        Persist an evaluation aggregate and its measurements atomically.

        Args:
            evaluation: Aggregate root to persist.
        """
        with transaction.atomic():
            existing = EvaluationModel.objects.filter(id=evaluation.id.value).first()
            if existing is not None and existing.status in (
                EvaluationStatus.ACCEPTED.value,
                EvaluationStatus.CONTESTED.value,
            ):
                raise IntegrityError("Cannot modify finalized evaluation")

            if existing is None:
                eval_model = EvaluationModel.objects.create(
                    id=evaluation.id.value,
                    collaborator_id=evaluation.collaborator_id.value,
                    evaluator_id=evaluation.evaluator_id.value,
                    period=evaluation.period,
                    evaluation_date=evaluation.evaluation_date,
                    status=EvaluationStatus.DRAFT.value,
                    submitted_at=evaluation.submitted_at,
                    response_date=evaluation.response_date,
                    response_notes=evaluation.response_notes or "",
                )
            else:
                eval_model = existing

            # Synchronize measurements
            current_measurement_ids = [m.id.value for m in evaluation.measurements]
            CompetencyMeasurementModel.objects.filter(
                evaluation_id=evaluation.id.value
            ).exclude(id__in=current_measurement_ids).delete()

            for measurement in evaluation.measurements:
                CompetencyMeasurementModel.objects.update_or_create(
                    id=measurement.id.value,
                    defaults={
                        "evaluation_id": evaluation.id.value,
                        "competency_id": measurement.competency_id.value,
                        "current_level": measurement.current_level,
                        "notes": measurement.notes or "",
                        "evidence": measurement.evidence or "",
                    },
                )

            # Finally, transition to the aggregate's target status
            if eval_model.status != evaluation.status.value:
                eval_model.status = evaluation.status.value
                eval_model.period = evaluation.period
                eval_model.submitted_at = evaluation.submitted_at
                eval_model.response_date = evaluation.response_date
                eval_model.response_notes = evaluation.response_notes or ""
                eval_model.save()

    def get_by_id(self, evaluation_id: EvaluationId) -> Evaluation | None:
        """
        Retrieve an evaluation aggregate by identifier.

        Args:
            evaluation_id: Identifier of the evaluation.

        Returns:
            Mapped domain Evaluation aggregate if found, otherwise None.
        """
        model = (
            EvaluationModel.objects.filter(id=evaluation_id.value)
            .prefetch_related("measurements")
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def find_latest_finalized_for_collaborator(
        self, collaborator_id: CollaboratorId
    ) -> Evaluation | None:
        """
        Return the most recent finalized evaluation for a collaborator.

        Finalized evaluations are those with status ACCEPTED or CONTESTED.
        DRAFT and COMPLETED evaluations are excluded.

        Args:
            collaborator_id: Collaborator whose finalized history is queried.

        Returns:
            The latest finalized Evaluation aggregate, or None if none exists.
        """
        model = (
            EvaluationModel.objects.filter(
                collaborator_id=collaborator_id.value,
                status__in=[
                    EvaluationStatus.ACCEPTED.value,
                    EvaluationStatus.CONTESTED.value,
                ],
            )
            .prefetch_related("measurements")
            .order_by("-evaluation_date", "-created_at")
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def find_all(
        self, *, collaborator_id: CollaboratorId | None = None
    ) -> list[Evaluation]:
        """
        Return evaluations, optionally filtered by collaborator.

        Args:
            collaborator_id: Optional collaborator filter.

        Returns:
            List of domain Evaluation aggregates.
        """
        queryset = EvaluationModel.objects.all().prefetch_related("measurements")
        if collaborator_id is not None:
            queryset = queryset.filter(collaborator_id=collaborator_id.value)
        queryset = queryset.order_by("-evaluation_date", "-created_at")
        return [self._to_domain(model) for model in queryset]

    @classmethod
    def _to_domain(cls, model: EvaluationModel) -> Evaluation:
        """Map EvaluationModel and its measurements to domain Evaluation."""
        measurements: list[CompetencyMeasurement] = []
        for measurement_model in CompetencyMeasurementModel.objects.filter(
            evaluation_id=model.id
        ):
            measurements.append(
                CompetencyMeasurement(
                    id=MeasurementId(measurement_model.id),
                    competency_id=CompetencyId(measurement_model.competency_id),
                    current_level=measurement_model.current_level,
                    notes=measurement_model.notes or None,
                    evidence=measurement_model.evidence or None,
                )
            )

        return Evaluation(
            id=EvaluationId(model.id),
            collaborator_id=CollaboratorId(model.collaborator_id),
            evaluator_id=CollaboratorId(model.evaluator_id),
            period=str(model.period),
            evaluation_date=model.evaluation_date,
            status=EvaluationStatus(model.status),
            measurements=measurements,
            submitted_at=model.submitted_at,
            response_date=model.response_date,
            response_notes=model.response_notes or None,
        )
