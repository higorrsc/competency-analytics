"""Career path query use cases."""

from __future__ import annotations

from src.application.use_cases.path.query.get_career_path import (
    GetCareerPathUseCase,
)
from src.application.use_cases.path.query.list_career_paths import (
    ListCareerPathsUseCase,
)

__all__ = [
    "GetCareerPathUseCase",
    "ListCareerPathsUseCase",
]
