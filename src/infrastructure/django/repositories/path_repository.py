"""Django ORM implementation of the PathRepository protocol."""

from __future__ import annotations

from django.db import transaction

from src.domain.entities.competency_path import CompetencyPath
from src.domain.entities.path_level import PathLevel
from src.domain.value_objects.competency_id import CompetencyId
from src.domain.value_objects.competency_requirement import CompetencyRequirement
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.path_id import PathId
from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.path_level import PathLevelModel


class DjangoPathRepository:
    """
    Persistence adapter for the CompetencyPath aggregate root.

    Mapping strategy:
    - Root entity `CompetencyPath` maps to `CompetencyPathModel`.
    - Inner entity `PathLevel` maps to `PathLevelModel` with foreign key to path.
    - Value object `CompetencyRequirement` maps to `CompetencyRequirementModel`.
    - All levels and requirements are saved atomically to maintain aggregate
      consistency.
    """

    def save(self, path: CompetencyPath) -> None:
        """
        Persist a career path aggregate and its nested levels and requirements.

        Args:
            path: Aggregate root to persist.
        """
        with transaction.atomic():
            CompetencyPathModel.objects.update_or_create(
                id=path.id.value,
                defaults={
                    "name": path.name,
                    "description": path.description,
                },
            )

            # Synchronize levels
            current_level_ids = [level.id.value for level in path.levels]
            PathLevelModel.objects.filter(path_id=path.id.value).exclude(
                id__in=current_level_ids
            ).delete()

            for level in path.levels:
                PathLevelModel.objects.update_or_create(
                    id=level.id.value,
                    defaults={
                        "path_id": path.id.value,
                        "name": level.name,
                        "order": level.order,
                    },
                )

                # Synchronize requirements for this level
                current_req_comp_ids = [
                    req.competency_id.value for req in level.requirements
                ]
                CompetencyRequirementModel.objects.filter(
                    path_level_id=level.id.value
                ).exclude(competency_id__in=current_req_comp_ids).delete()

                for req in level.requirements:
                    CompetencyRequirementModel.objects.update_or_create(
                        path_level_id=level.id.value,
                        competency_id=req.competency_id.value,
                        defaults={
                            "minimum_level": req.minimum_level,
                            "weight": req.weight.value,
                        },
                    )

    def get_by_id(self, path_id: PathId) -> CompetencyPath | None:
        """
        Retrieve a career path aggregate with all levels and requirements.

        Args:
            path_id: Identifier of the career path.

        Returns:
            Mapped domain CompetencyPath aggregate if found, otherwise None.
        """
        model = (
            CompetencyPathModel.objects.filter(id=path_id.value)
            .prefetch_related("levels__requirements")
            .first()
        )
        if model is None:
            return None
        return self._to_domain(model)

    def find_all(self) -> list[CompetencyPath]:
        """
        Retrieve all career paths in the catalog with their hierarchy.

        Returns:
            List of domain CompetencyPath aggregate roots.
        """
        queryset = CompetencyPathModel.objects.all().prefetch_related(
            "levels__requirements"
        )
        return [self._to_domain(model) for model in queryset.order_by("name")]

    @classmethod
    def _to_domain(cls, model: CompetencyPathModel) -> CompetencyPath:
        """Map CompetencyPathModel and its nested relations to domain aggregate."""
        levels: list[PathLevel] = []
        for level_model in PathLevelModel.objects.filter(path_id=model.id).order_by(
            "order"
        ):
            requirements: list[CompetencyRequirement] = []
            for req_model in CompetencyRequirementModel.objects.filter(
                path_level_id=level_model.id
            ):
                requirements.append(
                    CompetencyRequirement(
                        competency_id=CompetencyId(req_model.competency_id),
                        minimum_level=req_model.minimum_level,
                        weight=RequirementWeight(req_model.weight),
                    )
                )
            levels.append(
                PathLevel(
                    id=LevelId(level_model.id),
                    name=str(level_model.name),
                    order=level_model.order,
                    requirements=requirements,
                )
            )

        return CompetencyPath(
            id=PathId(model.id),
            name=str(model.name),
            description=str(model.description),
            levels=levels,
        )
