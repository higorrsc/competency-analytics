"""Performance verification test for competency gap analysis.

Task 18.6:
- Run performance test on gap analysis with large path (30+ requirements)
  and verify acceptable response time.
"""

from __future__ import annotations

import time
from datetime import UTC, datetime

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from src.application.dto.gap_analysis_dtos import GapAnalysisRequestDTO
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


@pytest.mark.django_db
def test_performance_gap_analysis_large_path_30_plus_requirements() -> None:
    """Gap analysis with 40 requirements must complete in acceptable time (<100ms)."""
    category = CategoryModel.objects.create(name="Scale Tech")
    group = CompetencyGroupModel.objects.create(name="Scale", category=category)

    # 1. Create 40 competencies in catalog
    competencies = [
        CompetencyModel.objects.create(
            name=f"Scale Competency {i:02d}",
            description=f"Skill {i}",
            category=category,
            group=group,
            level_descriptions={str(lvl): f"L{lvl}" for lvl in range(1, 6)},
        )
        for i in range(1, 41)
    ]
    assert len(competencies) == 40

    # 2. Create Career Path with a level having 40 requirements
    path = CompetencyPathModel.objects.create(
        name="Principal Architect", description="Staff+ Track"
    )
    level = PathLevelModel.objects.create(path=path, name="Level Principal", order=1)

    weights = [
        RequirementWeight.CORE.value,
        RequirementWeight.IMPORTANT.value,
        RequirementWeight.DESIRABLE.value,
    ]
    for i, comp in enumerate(competencies):
        CompetencyRequirementModel.objects.create(
            path_level=level,
            competency=comp,
            minimum_level=(i % 4) + 2,  # range 2 to 5
            weight=weights[i % 3],
        )

    # 3. Create Collaborator and Evaluation with 40 measurements
    collab = CollaboratorModel.objects.create(
        name="Performance Tester",
        email="perf@corp.com",
        department="Engineering",
    )
    evaluator = CollaboratorModel.objects.create(
        name="Engineering Director",
        email="director@corp.com",
        department="Engineering",
    )

    now = datetime.now(UTC)
    evaluation = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.H1",
        evaluation_date=now,
        status="DRAFT",
    )
    for i, comp in enumerate(competencies):
        CompetencyMeasurementModel.objects.create(
            evaluation=evaluation,
            competency=comp,
            current_level=(i % 5) + 1,  # range 1 to 5
        )
    evaluation.status = "ACCEPTED"
    evaluation.submitted_at = now
    evaluation.response_date = now
    evaluation.save()

    # 4. Measure Use Case execution time
    container = get_container()
    dto = GapAnalysisRequestDTO(
        collaborator_id=collab.id,
        path_id=path.id,
        level_id=level.id,
    )

    start_time = time.perf_counter()
    result = container.calculate_competency_gaps_use_case.execute(dto)
    duration_seconds = time.perf_counter() - start_time

    assert len(result.gaps) == 40
    # Core domain calculation should easily execute in < 100ms
    assert duration_seconds < 0.100, (
        f"Gap analysis took {duration_seconds * 1000:.2f}ms, expected < 100ms"
    )

    # 5. Measure REST API HTTP endpoint execution time
    client = APIClient()
    gap_url = (
        f"/api/v1/gap-analysis/?collaborator_id={collab.id}"
        f"&path_id={path.id}&level_id={level.id}"
    )

    api_start = time.perf_counter()
    response = client.get(gap_url)
    api_duration = time.perf_counter() - api_start

    assert response.status_code == status.HTTP_200_OK
    assert len(response.data["gaps"]) == 40
    # Complete HTTP serialization + query should execute in < 250ms
    assert api_duration < 0.250, (
        f"API Gap analysis took {api_duration * 1000:.2f}ms, expected < 250ms"
    )
