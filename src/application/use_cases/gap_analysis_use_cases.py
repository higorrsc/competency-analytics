"""Backward-compatible re-exports for gap analysis use cases.

This module preserves existing import paths while delegating to the
modular use case structure in `src.application.use_cases.gap_analysis`.
"""

from src.application.use_cases.gap_analysis.query.calculate_competency_gaps import (
    CalculateCompetencyGapsUseCase,
)

__all__ = ["CalculateCompetencyGapsUseCase"]
