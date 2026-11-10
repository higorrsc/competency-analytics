"""Query use case for competency gap analysis and progression eligibility."""

from __future__ import annotations

from src.application.dto.gap_analysis import (
    GapAnalysisRequestDTO,
    GapAnalysisResponseDTO,
)
from src.application.use_cases.errors import ConflictError, NotFoundError
from src.application.use_cases.mappers import map_eligibility, map_gap
from src.domain.exceptions.gap_analysis_errors import GapAnalysisError
from src.domain.exceptions.path_errors import LevelNotFoundError
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.repositories.path_repository import PathRepository
from src.domain.services.gap_analysis_service import GapAnalysisService
from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.level_id import LevelId
from src.domain.value_objects.path_id import PathId


class CalculateCompetencyGapsUseCase:
    """
    Use case for analyzing competency gaps against a target path level.

    Orchestration flow:

    1. Load the collaborator's latest finalized evaluation. Draft and
       submitted evaluations are not valid baselines for analysis.
    2. Load the target career path and the requested path level.
    3. Delegate the calculation to the domain service, which prioritizes
       gaps by requirement weight, gap size, and competency.
    4. Delegate progression eligibility to the domain service, where only
       unmet ``CORE`` gaps block progression.
    5. Map both results to response DTOs.

    The domain service is injected, keeping the use case focused purely on
    coordination; no calculation logic is duplicated here.
    """

    def __init__(
        self,
        evaluation_repository: EvaluationRepository,
        path_repository: PathRepository,
        gap_analysis_service: GapAnalysisService,
    ) -> None:
        """
        Initialize the use case with its dependencies.

        Args:
            evaluation_repository: Abstraction used to resolve the latest
                finalized evaluation.
            path_repository: Abstraction used to resolve the target path and
                level.
            gap_analysis_service: Domain service performing the gap
                calculation.
        """
        self._evaluation_repository = evaluation_repository
        self._path_repository = path_repository
        self._gap_analysis_service = gap_analysis_service

    def execute(
        self,
        request: GapAnalysisRequestDTO,
    ) -> GapAnalysisResponseDTO:
        """
        Calculate prioritized gaps and progression eligibility.

        Args:
            request: Validated input referencing collaborator, path, and the
                target path level to analyze.

        Returns:
            The analysis response with prioritized gaps and eligibility.

        Raises:
            NotFoundError: If the collaborator has no finalized evaluation,
                the path does not exist, or the level does not belong to the
                path.
            ConflictError: If the domain service rejects the baseline
                evaluation.
        """
        evaluation = self._evaluation_repository.find_latest_finalized_for_collaborator(
            CollaboratorId(request.collaborator_id)
        )
        if evaluation is None:
            raise NotFoundError("Finalized evaluation", request.collaborator_id)

        path = self._path_repository.get_by_id(PathId(request.path_id))
        if path is None:
            raise NotFoundError("Path", request.path_id)

        try:
            level = path.require_level(LevelId(request.level_id))
        except LevelNotFoundError as exc:
            raise NotFoundError("Path level", request.level_id) from exc

        try:
            gaps = self._gap_analysis_service.calculate_gaps(evaluation, level)
            eligibility = self._gap_analysis_service.check_progression_eligibility(gaps)
        except GapAnalysisError as exc:
            raise ConflictError(str(exc)) from exc

        return GapAnalysisResponseDTO(
            gaps=[map_gap(g) for g in gaps],
            eligibility=map_eligibility(eligibility),
        )
