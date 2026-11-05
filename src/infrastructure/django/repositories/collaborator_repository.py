"""Django ORM implementation of the CollaboratorRepository protocol."""

from __future__ import annotations

from django.db import transaction

from src.domain.entities.collaborator import Collaborator
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.path_enrollment import PathEnrollment
from src.domain.value_objects.path_id import PathId
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel


class DjangoCollaboratorRepository:
    """
    Persistence adapter for the Collaborator aggregate root.

    Mapping strategy:
    - Root entity `Collaborator` maps to `CollaboratorModel`.
    - Inner value objects `PathEnrollment` map to `PathEnrollmentModel` records.
    - Preserves historical inactive enrollments as required by domain rules.
    - Translates between domain Collaborator aggregate and persistence models.
    """

    def save(self, collaborator: Collaborator) -> None:
        """
        Persist a collaborator aggregate and its career path enrollments.

        Args:
            collaborator: Domain aggregate to persist.
        """
        with transaction.atomic():
            CollaboratorModel.objects.update_or_create(
                id=collaborator.id.value,
                defaults={
                    "name": collaborator.name,
                    "email": collaborator.email,
                    "department": collaborator.department,
                },
            )

            # Synchronize enrollments
            current_path_ids = [e.path_id.value for e in collaborator.enrollments]
            PathEnrollmentModel.objects.filter(
                collaborator_id=collaborator.id.value
            ).exclude(path_id__in=current_path_ids).delete()

            for enrollment in collaborator.enrollments:
                PathEnrollmentModel.objects.update_or_create(
                    collaborator_id=collaborator.id.value,
                    path_id=enrollment.path_id.value,
                    defaults={
                        "target_level": enrollment.target_level,
                        "is_active": enrollment.is_active,
                        "enrolled_at": enrollment.enrolled_at,
                    },
                )

    def get_by_id(self, collaborator_id: CollaboratorId) -> Collaborator | None:
        """
        Retrieve a collaborator aggregate by identifier.

        Args:
            collaborator_id: Identifier of the collaborator.

        Returns:
            Mapped domain Collaborator aggregate if found, otherwise None.
        """
        model = (
            CollaboratorModel.objects.filter(id=collaborator_id.value)
            .prefetch_related("enrollments")
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def find_by_path(
        self, path_id: PathId, *, active_only: bool = False
    ) -> list[Collaborator]:
        """
        Return collaborators enrolled in a career path.

        Args:
            path_id: Career path identifier.
            active_only: When True, returns only collaborators with an
                active enrollment.

        Returns:
            List of domain Collaborator aggregates.
        """
        queryset = CollaboratorModel.objects.filter(enrollments__path_id=path_id.value)
        if active_only:
            queryset = queryset.filter(enrollments__is_active=True)

        queryset = queryset.distinct().prefetch_related("enrollments").order_by("name")
        return [self._to_domain(model) for model in queryset]

    @classmethod
    def _to_domain(cls, model: CollaboratorModel) -> Collaborator:
        """Map CollaboratorModel and its enrollments to domain Collaborator."""
        enrollments: list[PathEnrollment] = []
        for enrollment_model in PathEnrollmentModel.objects.filter(
            collaborator_id=model.id
        ):
            enrollments.append(
                PathEnrollment(
                    path_id=PathId(enrollment_model.path_id),
                    target_level=str(enrollment_model.target_level),
                    enrolled_at=enrollment_model.enrolled_at,
                    is_active=bool(enrollment_model.is_active),
                )
            )

        return Collaborator(
            id=CollaboratorId(model.id),
            name=str(model.name),
            email=str(model.email),
            department=str(model.department),
            enrollments=enrollments,
        )
