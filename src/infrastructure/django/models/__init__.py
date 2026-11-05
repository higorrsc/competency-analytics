"""Django ORM models package for competency analytics infrastructure.

All models in this package are persistence-only adapters and do not contain
business rules. Domain entities are mapped to/from these models by repositories.
"""

from __future__ import annotations

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel

__all__ = [
    "CategoryModel",
    "CollaboratorModel",
    "CompetencyGroupModel",
    "CompetencyMeasurementModel",
    "CompetencyModel",
    "CompetencyPathModel",
    "CompetencyRequirementModel",
    "EvaluationModel",
    "PathEnrollmentModel",
    "PathLevelModel",
]
