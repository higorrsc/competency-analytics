"""Integration test for temporal queries over multiple evaluations.

Task 16.6:
- Multiple evaluations over time → query history, verify chronological
  order and level changes.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import pytest

from src.domain.value_objects.collaborator_id import CollaboratorId
from src.domain.value_objects.competency_id import CompetencyId
from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.competency import CompetencyModel
from src.infrastructure.django.models.competency_group import (
    CompetencyGroupModel,
)
from src.infrastructure.django.models.competency_measurement import (
    CompetencyMeasurementModel,
)
from src.infrastructure.django.models.evaluation import EvaluationModel
from src.presentation.dependencies.container import get_container


@pytest.fixture
def temporal_setup(
    db: None,
) -> tuple[CollaboratorModel, CompetencyModel, CompetencyModel]:
    collab = CollaboratorModel.objects.create(
        name="Roberta Lima", email="roberta@company.com", department="Data"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Lead Data", email="lead.data@company.com", department="Data"
    )

    category = CategoryModel.objects.create(name="Data Engineering")
    group = CompetencyGroupModel.objects.create(name="Pipelines", category=category)

    comp_python = CompetencyModel.objects.create(
        name="Python Data",
        description="ETL pipelines",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )
    comp_sql = CompetencyModel.objects.create(
        name="SQL Analytics",
        description="Complex queries",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    # 1. First evaluation: 2024-06-01 (ACCEPTED)
    t1 = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)
    ev1 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2024.H1",
        evaluation_date=t1,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev1, competency=comp_python, current_level=2
    )
    ev1.status = "ACCEPTED"
    ev1.submitted_at = t1
    ev1.response_date = t1
    ev1.response_notes = "H1 done"
    ev1.save()

    # 2. Second evaluation: 2025-01-15 (CONTESTADA)
    t2 = datetime(2025, 1, 15, 12, 0, 0, tzinfo=UTC)
    ev2 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2024.H2",
        evaluation_date=t2,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev2, competency=comp_python, current_level=3
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev2, competency=comp_sql, current_level=2
    )
    ev2.status = "CONTESTED"
    ev2.submitted_at = t2
    ev2.response_date = t2
    ev2.response_notes = "Disputed score"
    ev2.save()

    # 3. Third evaluation: 2025-07-20 (ACEITA)
    t3 = datetime(2025, 7, 20, 12, 0, 0, tzinfo=UTC)
    ev3 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.H1",
        evaluation_date=t3,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev3, competency=comp_python, current_level=4
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev3, competency=comp_sql, current_level=3
    )
    ev3.status = "ACCEPTED"
    ev3.submitted_at = t3
    ev3.response_date = t3
    ev3.response_notes = "Approved"
    ev3.save()

    # 4. Draft evaluation: 2026-01-10 (MUST NOT BE INCLUDED IN HISTORY)
    t4 = datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC)
    ev_draft = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.H2",
        evaluation_date=t4,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev_draft, competency=comp_python, current_level=5
    )

    return collab, comp_python, comp_sql


@pytest.mark.django_db
def test_temporal_queries_chronological_ordering_and_level_changes(
    temporal_setup: tuple[CollaboratorModel, CompetencyModel, CompetencyModel],
) -> None:
    """Validate chronological ordering, previous_level, and level_change."""
    collab, comp_python, comp_sql = temporal_setup
    container = get_container()

    history = container.get_competency_history_use_case.execute(
        CollaboratorId(collab.id)
    )

    # 5 finalized measurements across 3 evaluations (draft excluded)
    assert len(history) == 5

    # Filter Python history
    python_entries = [e for e in history if e.competency_id == comp_python.id]
    assert len(python_entries) == 3

    # Verification of chronological order and lag window calculation:
    # Entry 1 (2024.H1): level 2, initial
    assert python_entries[0].period == "2024.H1"
    assert python_entries[0].current_level == 2
    assert python_entries[0].previous_level is None
    assert python_entries[0].level_change is None

    # Entry 2 (2024.H2): level 3, previous 2, change +1
    assert python_entries[1].period == "2024.H2"
    assert python_entries[1].current_level == 3
    assert python_entries[1].previous_level == 2
    assert python_entries[1].level_change == 1

    # Entry 3 (2025.H1): level 4, previous 3, change +1
    assert python_entries[2].period == "2025.H1"
    assert python_entries[2].current_level == 4
    assert python_entries[2].previous_level == 3
    assert python_entries[2].level_change == 1

    # Filter SQL history
    sql_entries = [e for e in history if e.competency_id == comp_sql.id]
    assert len(sql_entries) == 2

    # Entry 1 (2024.H2): level 2, initial for SQL
    assert sql_entries[0].period == "2024.H2"
    assert sql_entries[0].current_level == 2
    assert sql_entries[0].previous_level is None

    # Entry 2 (2025.H1): level 3, previous 2, change +1
    assert sql_entries[1].period == "2025.H1"
    assert sql_entries[1].current_level == 3
    assert sql_entries[1].previous_level == 2
    assert sql_entries[1].level_change == 1


@pytest.mark.django_db
def test_temporal_queries_date_filtering(
    temporal_setup: tuple[CollaboratorModel, CompetencyModel, CompetencyModel],
) -> None:
    """Validate start_date and end_date filtering excludes out-of-range evaluations."""
    collab, comp_python, _ = temporal_setup
    container = get_container()

    # Query only 2025 evaluations
    filtered_history = container.get_competency_history_use_case.execute(
        CollaboratorId(collab.id),
        competency_id=CompetencyId(comp_python.id),
        start_date=date(2025, 1, 1),
        end_date=date(2025, 12, 31),
    )

    # Must contain 2024.H2 (evaluated in Jan 2025) and 2025.H1 (evaluated in Jul 2025)
    # Must exclude 2024.H1 (evaluated in Jun 2024)
    assert len(filtered_history) == 2
    periods = [e.period for e in filtered_history]
    assert "2024.H1" not in periods
    assert "2024.H2" in periods
    assert "2025.H1" in periods
