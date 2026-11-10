"""Django ORM repository implementations for domain repository protocols."""

from __future__ import annotations

from src.infrastructure.django.repositories.collaborator_repository import (
    DjangoCollaboratorRepository,
)
from src.infrastructure.django.repositories.competency_repository import (
    DjangoCompetencyRepository,
)
from src.infrastructure.django.repositories.evaluation_repository import (
    DjangoEvaluationRepository,
)
from src.infrastructure.django.repositories.path_repository import (
    DjangoPathRepository,
)

__all__ = [
    "DjangoCollaboratorRepository",
    "DjangoCompetencyRepository",
    "DjangoEvaluationRepository",
    "DjangoPathRepository",
]
