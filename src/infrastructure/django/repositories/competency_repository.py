"""Django ORM implementation of the CompetencyRepository protocol."""

from __future__ import annotations

from django.db import transaction

from src.domain.entities.competency import Competency
from src.domain.exceptions.competency_errors import CompetencyReferencedError
from src.domain.value_objects.category_id import CategoryId
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.group_id import GroupId
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)


class DjangoCompetencyRepository:
    """
    Persistence adapter for the Competency catalog aggregate.

    Mapping strategy:
    - Domain entity `Competency` maps to `CompetencyModel`.
    - Proficiency level descriptions (`dict[int, str]`) in domain map to/from
      Django's `JSONField` (keys serialized as string in JSON, parsed back to int).
    - Foreign keys to Category and Group are validated and persisted.
    - References in career path requirements and evaluation measurements are checked
      before deletion to enforce catalog integrity rules.
    """

    def save(self, competency: Competency) -> None:
        """
        Persist a competency aggregate, creating or updating its record.

        Args:
            competency: Domain entity to persist.
        """
        with transaction.atomic():
            # Ensure referenced category and group exist
            category, _ = CategoryModel.objects.get_or_create(
                id=competency.category_id.value,
                defaults={"name": f"Category {competency.category_id.value}"},
            )
            CompetencyGroupModel.objects.get_or_create(
                id=competency.group_id.value,
                defaults={
                    "category": category,
                    "name": f"Group {competency.group_id.value}",
                },
            )

            serialized_levels = {
                str(k): v for k, v in competency.level_descriptions.items()
            }
            CompetencyModel.objects.update_or_create(
                id=competency.id.value,
                defaults={
                    "name": competency.name,
                    "description": competency.description,
                    "category_id": competency.category_id.value,
                    "group_id": competency.group_id.value,
                    "level_descriptions": serialized_levels,
                },
            )

    def get_by_id(self, competency_id: CompetencyId) -> Competency | None:
        """
        Retrieve a competency aggregate by identifier.

        Args:
            competency_id: Identifier of the competency to load.

        Returns:
            Mapped domain Competency entity if found, otherwise None.
        """
        model = CompetencyModel.objects.filter(id=competency_id.value).first()
        if model is None:
            return None
        return self._to_domain(model)

    def find_by_hierarchy(
        self,
        *,
        category_id: CategoryId | None = None,
        group_id: GroupId | None = None,
    ) -> list[Competency]:
        """
        List competencies filtered by category and/or group.

        Args:
            category_id: Optional category filter.
            group_id: Optional group filter.

        Returns:
            List of matching domain Competency entities.
        """
        queryset = CompetencyModel.objects.all()
        if category_id is not None:
            queryset = queryset.filter(category_id=category_id.value)
        if group_id is not None:
            queryset = queryset.filter(group_id=group_id.value)

        return [self._to_domain(model) for model in queryset.order_by("name")]

    def delete(self, competency_id: CompetencyId) -> None:
        """
        Delete a competency from the catalog if unreferenced.

        Args:
            competency_id: Identifier of the competency to remove.

        Raises:
            CompetencyReferencedError: If the competency is referenced by a career path
                or an evaluation measurement.
        """
        if CompetencyRequirementModel.objects.filter(
            competency_id=competency_id.value
        ).exists():
            raise CompetencyReferencedError(
                competency_id,
                [f"Competency {competency_id} is referenced in career paths"],
            )

        if CompetencyMeasurementModel.objects.filter(
            competency_id=competency_id.value
        ).exists():
            raise CompetencyReferencedError(
                competency_id,
                [f"Competency {competency_id} is referenced in evaluations"],
            )

        CompetencyModel.objects.filter(id=competency_id.value).delete()

    @staticmethod
    def _to_domain(model: CompetencyModel) -> Competency:
        """Map a CompetencyModel ORM record to a domain Competency entity."""
        level_descriptions = {
            int(k): str(v) for k, v in model.level_descriptions.items()
        }
        return Competency(
            id=CompetencyId(model.id),
            name=str(model.name),
            description=str(model.description),
            category_id=CategoryId(model.category_id),
            group_id=GroupId(model.group_id),
            level_descriptions=level_descriptions,
        )
