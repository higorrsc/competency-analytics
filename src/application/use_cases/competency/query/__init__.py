"""Competency query use cases."""

from __future__ import annotations

from src.application.use_cases.competency.query.get_competency import (
    GetCompetencyUseCase,
)
from src.application.use_cases.competency.query.list_competencies import (
    ListCompetenciesUseCase,
)

__all__ = [
    "GetCompetencyUseCase",
    "ListCompetenciesUseCase",
]
