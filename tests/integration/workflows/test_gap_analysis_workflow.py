"""Integration test for competency gap analysis with missing measurements.

Task 16.5:
- Evaluation with partial measurements → verify unmeasured treated as level 0.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from src.application.dto.gap_analysis import GapAnalysisRequestDTO
from src.domain.value_objects.requirement_weight import RequirementWeight
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.competency_path import CompetencyPathModel
from src.infrastructure.django.models.competency_requirement import (
    CompetencyRequirementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.infrastructure.django.models.path_level import PathLevelModel
from src.presentation.dependencies.container import get_container


@pytest.fixture
def gap_analysis_setup(
    db: None,
) -> tuple[
    CollaboratorModel,
    CompetencyPathModel,
    PathLevelModel,
    tuple[CompetencyModel, CompetencyModel, CompetencyModel],
]:
    collab = CollaboratorModel.objects.create(
        name="Developer One", email="dev1@company.com", department="Backend"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Tech Lead One", email="lead1@company.com", department="Backend"
    )

    category = CategoryModel.objects.create(name="Tech Skills")
    group = CompetencyGroupModel.objects.create(name="Engineering", category=category)

    comp_python = CompetencyModel.objects.create(
        name="Python",
        description="Backend language",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )
    comp_sql = CompetencyModel.objects.create(
        name="SQL & Relational Databases",
        description="Database design and querying",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )
    comp_docker = CompetencyModel.objects.create(
        name="Docker & Containerization",
        description="Containers and deployment",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    path = CompetencyPathModel.objects.create(
        name="Backend Track", description="Career Track"
    )
    level = PathLevelModel.objects.create(path=path, name="Senior Engineer", order=1)

    # 1. Python: min 4, CORE
    CompetencyRequirementModel.objects.create(
        path_level=level,
        competency=comp_python,
        minimum_level=4,
        weight=RequirementWeight.CORE.value,
    )
    # 2. SQL: min 3, IMPORTANT
    CompetencyRequirementModel.objects.create(
        path_level=level,
        competency=comp_sql,
        minimum_level=3,
        weight=RequirementWeight.IMPORTANT.value,
    )
    # 3. Docker: min 2, DESIRABLE
    CompetencyRequirementModel.objects.create(
        path_level=level,
        competency=comp_docker,
        minimum_level=2,
        weight=RequirementWeight.DESIRABLE.value,
    )

    # Finalized evaluation with ONLY Python measured (SQL and Docker unmeasured)
    now = datetime.now(UTC)
    evaluation = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2026.Q1",
        evaluation_date=now,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=evaluation,
        competency=comp_python,
        current_level=3,
    )
    evaluation.status = "ACCEPTED"
    evaluation.submitted_at = now
    evaluation.response_date = now
    evaluation.response_notes = "Approved"
    evaluation.save()

    return collab, path, level, (comp_python, comp_sql, comp_docker)


@pytest.mark.django_db
def test_gap_analysis_treats_unmeasured_competencies_as_level_zero(
    gap_analysis_setup: tuple[
        CollaboratorModel,
        CompetencyPathModel,
        PathLevelModel,
        tuple[CompetencyModel, CompetencyModel, CompetencyModel],
    ],
) -> None:
    """Validate unmeasured competencies get current_level=0 and full gap."""
    collab, path, level, (comp_python, comp_sql, comp_docker) = gap_analysis_setup
    container = get_container()

    request_dto = GapAnalysisRequestDTO(
        collaborator_id=collab.id,
        path_id=path.id,
        level_id=level.id,
    )
    response = container.calculate_competency_gaps_use_case.execute(request_dto)

    assert len(response.gaps) == 3

    # Priority 1: CORE (Python) - current 3, required 4 -> gap 1
    python_gap = next(g for g in response.gaps if g.competency_id == comp_python.id)
    assert python_gap.weight == RequirementWeight.CORE
    assert python_gap.current_level == 3
    assert python_gap.required_level == 4
    assert python_gap.gap == 1

    # Priority 2: IMPORTANT (SQL) - unmeasured -> current 0, required 3 -> gap 3
    sql_gap = next(g for g in response.gaps if g.competency_id == comp_sql.id)
    assert sql_gap.weight == RequirementWeight.IMPORTANT
    assert sql_gap.current_level == 0
    assert sql_gap.required_level == 3
    assert sql_gap.gap == 3

    # Priority 3: DESIRABLE (Docker) - unmeasured -> current 0, required 2 -> gap 2
    docker_gap = next(g for g in response.gaps if g.competency_id == comp_docker.id)
    assert docker_gap.weight == RequirementWeight.DESIRABLE
    assert docker_gap.current_level == 0
    assert docker_gap.required_level == 2
    assert docker_gap.gap == 2

    # Verification of ordering: CORE first, then IMPORTANT, then DESIRABLE
    assert response.gaps[0].competency_id == comp_python.id
    assert response.gaps[1].competency_id == comp_sql.id
    assert response.gaps[2].competency_id == comp_docker.id

    # Progression blocked due to unmet CORE
    assert response.eligibility.is_eligible is False
    assert comp_python.id in response.eligibility.blocking_competency_ids
