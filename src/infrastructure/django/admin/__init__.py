"""Django Admin registrations for competency analytics models."""

from __future__ import annotations

from django.contrib import admin

from src.infrastructure.django.admin.category_admin import CategoryAdmin
from src.infrastructure.django.admin.collaborator_admin import (
    CollaboratorAdmin,
    PathEnrollmentAdmin,
)
from src.infrastructure.django.admin.competency_admin import CompetencyAdmin
from src.infrastructure.django.admin.competency_group_admin import (
    CompetencyGroupAdmin,
)
from src.infrastructure.django.admin.competency_path_admin import (
    CompetencyPathAdmin,
    PathLevelAdmin,
)
from src.infrastructure.django.admin.evaluation_admin import EvaluationAdmin
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import CompetencyGroupModel
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel

admin.site.register(CategoryModel, CategoryAdmin)
admin.site.register(CompetencyGroupModel, CompetencyGroupAdmin)
admin.site.register(CompetencyModel, CompetencyAdmin)
admin.site.register(CompetencyPathModel, CompetencyPathAdmin)
admin.site.register(PathLevelModel, PathLevelAdmin)
admin.site.register(CollaboratorModel, CollaboratorAdmin)
admin.site.register(PathEnrollmentModel, PathEnrollmentAdmin)
admin.site.register(EvaluationModel, EvaluationAdmin)

__all__ = [
    "CategoryAdmin",
    "CollaboratorAdmin",
    "CompetencyAdmin",
    "CompetencyGroupAdmin",
    "CompetencyPathAdmin",
    "EvaluationAdmin",
    "PathEnrollmentAdmin",
    "PathLevelAdmin",
]
