"""Backward-compatible re-exports for read model use cases.

This module preserves existing import paths while delegating to the
modular use case structure in `src.application.use_cases.read_model`.
"""

from src.application.use_cases.read_model.query.get_competency_history import (
    GetCompetencyHistoryUseCase,
)
from src.application.use_cases.read_model.query.get_path_progression import (
    GetPathProgressionUseCase,
)

__all__ = [
    "GetCompetencyHistoryUseCase",
    "GetPathProgressionUseCase",
]
