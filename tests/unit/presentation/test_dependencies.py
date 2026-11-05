"""Unit tests for the dependency injection container and composition root."""

from __future__ import annotations

from collections.abc import Generator

import pytest

from src.domain.services.gap_analysis_service import GapAnalysisService
from src.infrastructure.django.read_models.competency_history_read_model import (
    DjangoCompetencyHistoryReadModel,
)
from src.infrastructure.django.read_models.path_progression_read_model import (
    DjangoPathProgressionReadModel,
)
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
from src.presentation.dependencies.container import (
    Container,
    get_container,
    set_container,
)
from tests.unit.application.use_cases.fakes import (
    FakeCollaboratorRepository,
    FakeCompetencyRepository,
    FakeEvaluationRepository,
    FakePathRepository,
)


@pytest.fixture(autouse=True)
def reset_container() -> Generator[None]:
    """Ensure clean container state before and after each test."""
    set_container(None)
    yield
    set_container(None)


def test_container_default_initialization() -> None:
    """Verify default container creates standard adapters and wires use cases."""
    container = Container()

    assert isinstance(container.competency_repository, DjangoCompetencyRepository)
    assert isinstance(container.path_repository, DjangoPathRepository)
    assert isinstance(container.collaborator_repository, DjangoCollaboratorRepository)
    assert isinstance(container.evaluation_repository, DjangoEvaluationRepository)
    assert isinstance(
        container.competency_history_read_model,
        DjangoCompetencyHistoryReadModel,
    )
    assert isinstance(
        container.path_progression_read_model,
        DjangoPathProgressionReadModel,
    )
    assert isinstance(container.gap_analysis_service, GapAnalysisService)

    # Verify use case wiring
    assert container.create_competency_use_case is not None
    assert container.get_competency_use_case is not None
    assert container.list_competencies_use_case is not None
    assert container.delete_competency_use_case is not None
    assert container.create_career_path_use_case is not None
    assert container.get_career_path_use_case is not None
    assert container.list_career_paths_use_case is not None
    assert container.create_collaborator_use_case is not None
    assert container.get_collaborator_use_case is not None
    assert container.list_collaborators_use_case is not None
    assert container.enroll_collaborator_in_path_use_case is not None
    assert container.activate_collaborator_path_use_case is not None
    assert container.create_evaluation_use_case is not None
    assert container.get_evaluation_use_case is not None
    assert container.list_evaluations_use_case is not None
    assert container.add_measurement_to_evaluation_use_case is not None
    assert container.submit_evaluation_use_case is not None
    assert container.accept_evaluation_use_case is not None
    assert container.contest_evaluation_use_case is not None
    assert container.calculate_competency_gaps_use_case is not None
    assert container.get_competency_history_use_case is not None
    assert container.get_path_progression_use_case is not None


def test_container_custom_dependency_injection() -> None:
    """Verify custom fakes can be injected into container."""
    fake_comp = FakeCompetencyRepository()
    fake_path = FakePathRepository()
    fake_collab = FakeCollaboratorRepository()
    fake_eval = FakeEvaluationRepository()
    custom_gap_service = GapAnalysisService()

    container = Container(
        competency_repository=fake_comp,
        path_repository=fake_path,
        collaborator_repository=fake_collab,
        evaluation_repository=fake_eval,
        gap_analysis_service=custom_gap_service,
    )

    assert container.competency_repository is fake_comp
    assert container.path_repository is fake_path
    assert container.collaborator_repository is fake_collab
    assert container.evaluation_repository is fake_eval
    assert container.gap_analysis_service is custom_gap_service

    # Verify use cases received the injected fake dependencies
    assert container.create_competency_use_case._repository is fake_comp
    assert container.get_competency_use_case._repository is fake_comp
    assert container.delete_competency_use_case._repository is fake_comp
    assert container.create_career_path_use_case._path_repository is fake_path
    assert container.get_career_path_use_case._repository is fake_path
    assert (
        container.create_collaborator_use_case._collaborator_repository is fake_collab
    )
    assert container.get_collaborator_use_case._collaborator_repository is fake_collab
    assert (
        container.activate_collaborator_path_use_case._collaborator_repository
        is fake_collab
    )
    assert container.create_evaluation_use_case._evaluation_repository is fake_eval
    assert (
        container.calculate_competency_gaps_use_case._gap_analysis_service
        is custom_gap_service
    )


def test_gap_analysis_service_is_singleton() -> None:
    """Verify GapAnalysisService is a singleton instance within container."""
    container = Container()
    service1 = container.gap_analysis_service
    service2 = container.gap_analysis_service

    assert service1 is service2
    assert (
        container.calculate_competency_gaps_use_case._gap_analysis_service is service1
    )


def test_get_and_set_container() -> None:
    """Verify singleton get_container and set_container override behavior."""
    c1 = get_container()
    c2 = get_container()
    assert c1 is c2

    custom_container = Container()
    set_container(custom_container)
    assert get_container() is custom_container

    set_container(None)
    fresh = get_container()
    assert fresh is not custom_container
