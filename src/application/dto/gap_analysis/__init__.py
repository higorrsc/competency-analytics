"""Gap analysis application DTOs."""

from src.application.dto.gap_analysis.requests import GapAnalysisRequestDTO
from src.application.dto.gap_analysis.responses import (
    CompetencyGapDTO,
    GapAnalysisResponseDTO,
    ProgressionEligibilityDTO,
)

__all__ = [
    "CompetencyGapDTO",
    "GapAnalysisRequestDTO",
    "GapAnalysisResponseDTO",
    "ProgressionEligibilityDTO",
]
