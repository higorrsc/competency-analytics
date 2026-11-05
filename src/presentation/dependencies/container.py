"""Dependency injection container and composition root."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.application.ports.read_models import (
    CompetencyHistoryReadModel,
    PathProgressionReadModel,
)
from src.application.use_cases.collaborator_use_cases import (
    ActivateCollaboratorPathUseCase,
    CreateCollaboratorUseCase,
    EnrollCollaboratorInPathUseCase,
    GetCollaboratorUseCase,
    ListCollaboratorsUseCase,
)
from src.application.use_cases.competency_use_cases import (
    CreateCompetencyUseCase,
    DeleteCompetencyUseCase,
    GetCompetencyUseCase,
    ListCompetenciesUseCase,
)
from src.application.use_cases.evaluation_use_cases import (
    AcceptEvaluationUseCase,
    AddMeasurementToEvaluationUseCase,
    ContestEvaluationUseCase,
    CreateEvaluationUseCase,
    GetEvaluationUseCase,
    ListEvaluationsUseCase,
    SubmitEvaluationUseCase,
)
from src.application.use_cases.gap_analysis_use_cases import (
    CalculateCompetencyGapsUseCase,
)
from src.application.use_cases.path_use_cases import (
    CreateCareerPathUseCase,
    GetCareerPathUseCase,
    ListCareerPathsUseCase,
)
from src.application.use_cases.read_model_use_cases import (
    GetCompetencyHistoryUseCase,
    GetPathProgressionUseCase,
)
from src.domain.repositories.collaborator_repository import CollaboratorRepository
from src.domain.repositories.competency_repository import CompetencyRepository
from src.domain.repositories.evaluation_repository import EvaluationRepository
from src.domain.repositories.path_repository import PathRepository
from src.domain.services.gap_analysis_service import GapAnalysisService

if TYPE_CHECKING:
    pass


class Container:
    """
    Composition root wiring application use cases to infrastructure repositories.

    This container encapsulates the composition of all application dependencies.
    Domain services like `GapAnalysisService` are singletons wired across use cases,
    and all repositories and read models default to Django ORM implementations
    while remaining fully substitutable for testing.
    """

    def __init__(
        self,
        *,
        competency_repository: CompetencyRepository | None = None,
        path_repository: PathRepository | None = None,
        collaborator_repository: CollaboratorRepository | None = None,
        evaluation_repository: EvaluationRepository | None = None,
        competency_history_read_model: CompetencyHistoryReadModel | None = None,
        path_progression_read_model: PathProgressionReadModel | None = None,
        gap_analysis_service: GapAnalysisService | None = None,
    ) -> None:
        """
        Initialize the container, creating default adapters if not provided.

        Args:
            competency_repository: Persistence port for competencies.
            path_repository: Persistence port for career paths.
            collaborator_repository: Persistence port for collaborators.
            evaluation_repository: Persistence port for evaluations.
            competency_history_read_model: Read model port for temporal history.
            path_progression_read_model: Read model port for path progression.
            gap_analysis_service: Domain service for competency gap calculations.
        """
        # Lazy import concrete infrastructure adapters to maintain loose coupling
        from src.infrastructure.django.read_models import (
            DjangoCompetencyHistoryReadModel,
            DjangoPathProgressionReadModel,
        )
        from src.infrastructure.django.repositories import (
            DjangoCollaboratorRepository,
            DjangoCompetencyRepository,
            DjangoEvaluationRepository,
            DjangoPathRepository,
        )

        self.competency_repository: CompetencyRepository = (
            competency_repository or DjangoCompetencyRepository()
        )
        self.path_repository: PathRepository = path_repository or DjangoPathRepository()
        self.collaborator_repository: CollaboratorRepository = (
            collaborator_repository or DjangoCollaboratorRepository()
        )
        self.evaluation_repository: EvaluationRepository = (
            evaluation_repository or DjangoEvaluationRepository()
        )
        self.competency_history_read_model: CompetencyHistoryReadModel = (
            competency_history_read_model or DjangoCompetencyHistoryReadModel()
        )
        self.path_progression_read_model: PathProgressionReadModel = (
            path_progression_read_model or DjangoPathProgressionReadModel()
        )

        # Singleton domain service
        self.gap_analysis_service: GapAnalysisService = (
            gap_analysis_service or GapAnalysisService()
        )

        # Wire Competency Use Cases
        self.create_competency_use_case = CreateCompetencyUseCase(
            self.competency_repository
        )
        self.get_competency_use_case = GetCompetencyUseCase(self.competency_repository)
        self.list_competencies_use_case = ListCompetenciesUseCase(
            self.competency_repository
        )
        self.delete_competency_use_case = DeleteCompetencyUseCase(
            self.competency_repository
        )

        # Wire Career Path Use Cases
        self.create_career_path_use_case = CreateCareerPathUseCase(
            self.path_repository,
            self.competency_repository,
        )
        self.get_career_path_use_case = GetCareerPathUseCase(self.path_repository)
        self.list_career_paths_use_case = ListCareerPathsUseCase(self.path_repository)

        # Wire Collaborator Use Cases
        self.create_collaborator_use_case = CreateCollaboratorUseCase(
            self.collaborator_repository
        )
        self.get_collaborator_use_case = GetCollaboratorUseCase(
            self.collaborator_repository
        )
        self.list_collaborators_use_case = ListCollaboratorsUseCase(
            self.collaborator_repository
        )
        self.enroll_collaborator_in_path_use_case = EnrollCollaboratorInPathUseCase(
            self.collaborator_repository,
            self.path_repository,
        )
        self.activate_collaborator_path_use_case = ActivateCollaboratorPathUseCase(
            self.collaborator_repository
        )

        # Wire Evaluation Use Cases
        self.create_evaluation_use_case = CreateEvaluationUseCase(
            self.evaluation_repository,
            self.collaborator_repository,
        )
        self.get_evaluation_use_case = GetEvaluationUseCase(self.evaluation_repository)
        self.list_evaluations_use_case = ListEvaluationsUseCase(
            self.evaluation_repository
        )
        self.add_measurement_to_evaluation_use_case = AddMeasurementToEvaluationUseCase(
            self.evaluation_repository,
            self.competency_repository,
        )
        self.submit_evaluation_use_case = SubmitEvaluationUseCase(
            self.evaluation_repository
        )
        self.accept_evaluation_use_case = AcceptEvaluationUseCase(
            self.evaluation_repository
        )
        self.contest_evaluation_use_case = ContestEvaluationUseCase(
            self.evaluation_repository
        )

        # Wire Gap Analysis Use Case
        self.calculate_competency_gaps_use_case = CalculateCompetencyGapsUseCase(
            self.evaluation_repository,
            self.path_repository,
            self.gap_analysis_service,
        )

        # Wire CQRS Read Model Use Cases
        self.get_competency_history_use_case = GetCompetencyHistoryUseCase(
            self.competency_history_read_model
        )
        self.get_path_progression_use_case = GetPathProgressionUseCase(
            self.path_progression_read_model
        )


_default_container: Container | None = None


def get_container() -> Container:
    """
    Retrieve or initialize the application-wide dependency container.

    Returns:
        The singleton application container instance.
    """
    global _default_container
    if _default_container is None:
        _default_container = Container()
    return _default_container


def set_container(container: Container | None) -> None:
    """
    Override the application dependency container (typically for testing).

    Args:
        container: The container instance to set, or None to reset to default.
    """
    global _default_container
    _default_container = container
