"""Backward-compatible re-exports for competency use cases."""

from __future__ import annotations

from src.application.use_cases.competency.command.create_competency import (
    CreateCompetencyUseCase,
)
from src.application.use_cases.competency.command.delete_competency import (
    DeleteCompetencyUseCase,
)
from src.application.use_cases.competency.query.get_competency import (
    GetCompetencyUseCase,
)
from src.application.use_cases.competency.query.list_competencies import (
    ListCompetenciesUseCase,
)

__all__ = [
    "CreateCompetencyUseCase",
    "DeleteCompetencyUseCase",
    "GetCompetencyUseCase",
    "ListCompetenciesUseCase",
]
