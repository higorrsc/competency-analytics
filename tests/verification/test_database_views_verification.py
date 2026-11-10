"""System verification tests for database views against manual queries.

Task 18.5:
- Verify database views return correct data matching manual raw SQL queries.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest
from django.db import connection

from src.infrastructure.django.models.category import CategoryModel
from src.infrastructure.django.models.collaborator import CollaboratorModel
from src.infrastructure.django.models.collaborator_competency_history_view import (
    CollaboratorCompetencyHistoryViewModel,
)
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
from src.infrastructure.django.models.path_enrollment import PathEnrollmentModel
from src.infrastructure.django.models.path_level import PathLevelModel
from src.infrastructure.django.models.path_progression_summary_view import (
    PathProgressionSummaryViewModel,
)


@pytest.mark.django_db
def test_collaborator_competency_history_view_matches_manual_sql() -> None:
    """Verify history view returns identical results to a manual SQL query."""
    collab = CollaboratorModel.objects.create(
        name="Diana Prince", email="diana@amazon.corp", department="Security"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Hippolyta", email="queen@amazon.corp", department="Security"
    )

    category = CategoryModel.objects.create(name="Defense")
    group = CompetencyGroupModel.objects.create(name="Strategy", category=category)
    comp = CompetencyModel.objects.create(
        name="Tactics",
        description="Combat strategy",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    # Evaluation 1: Level 2
    t1 = datetime(2024, 6, 1, 12, 0, tzinfo=UTC)
    e1 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2024.H1",
        evaluation_date=t1,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=e1, competency=comp, current_level=2
    )
    e1.status = "ACCEPTED"
    e1.submitted_at = t1
    e1.response_date = t1
    e1.response_notes = "Approved H1"
    e1.save()

    # Evaluation 2: Level 4
    t2 = datetime(2025, 1, 15, 12, 0, tzinfo=UTC)
    e2 = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2024.H2",
        evaluation_date=t2,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=e2, competency=comp, current_level=4
    )
    e2.status = "ACCEPTED"
    e2.submitted_at = t2
    e2.response_date = t2
    e2.response_notes = "Approved H2"
    e2.save()

    # Manual query directly on underlying tables:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                e.period,
                m.current_level,
                LAG(m.current_level) OVER (
                    PARTITION BY m.competency_id
                    ORDER BY e.evaluation_date
                ) AS previous_level
            FROM evaluations e
            JOIN competency_measurements m ON m.evaluation_id = e.id
            WHERE e.collaborator_id = %s
              AND e.status IN ('COMPLETED', 'ACCEPTED', 'CONTESTED')
            ORDER BY e.evaluation_date ASC
            """,
            [collab.id.hex],
        )
        manual_rows = cursor.fetchall()

    assert len(manual_rows) == 2
    assert manual_rows[0] == ("2024.H1", 2, None)
    assert manual_rows[1] == ("2024.H2", 4, 2)

    # Database view query:
    view_rows = list(
        CollaboratorCompetencyHistoryViewModel.objects.filter(
            collaborator_id=collab.id
        ).order_by("evaluation_date")
    )

    assert len(view_rows) == len(manual_rows)
    for i, row in enumerate(view_rows):
        assert row.period == manual_rows[i][0]
        assert row.current_level == manual_rows[i][1]
        assert row.previous_level == manual_rows[i][2]
        if row.previous_level is not None:
            assert row.level_change == row.current_level - row.previous_level
        else:
            assert row.level_change is None


@pytest.mark.django_db
def test_path_progression_summary_view_matches_manual_sql() -> None:
    """Verify progression summary view matches manual SQL calculation."""
    collab = CollaboratorModel.objects.create(
        name="Arthur Curry", email="arthur@atlantis.corp", department="Naval"
    )
    evaluator = CollaboratorModel.objects.create(
        name="Mera", email="mera@atlantis.corp", department="Naval"
    )

    path = CompetencyPathModel.objects.create(
        name="Naval Commander", description="Ocean track"
    )
    level = PathLevelModel.objects.create(path=path, name="Lieutenant", order=1)

    category = CategoryModel.objects.create(name="Maritime")
    group = CompetencyGroupModel.objects.create(name="Navigation", category=category)
    comp1 = CompetencyModel.objects.create(
        name="Sonar Ops",
        description="Sonar",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )
    comp2 = CompetencyModel.objects.create(
        name="Hydrography",
        description="Mapping",
        category=category,
        group=group,
        level_descriptions={str(i): f"L{i}" for i in range(1, 6)},
    )

    # 1 mandatory requirement, 1 optional
    CompetencyRequirementModel.objects.create(
        path_level=level, competency=comp1, minimum_level=3, weight="CORE"
    )
    CompetencyRequirementModel.objects.create(
        path_level=level, competency=comp2, minimum_level=2, weight="IMPORTANT"
    )

    # Active path enrollment
    now = datetime.now(UTC)
    PathEnrollmentModel.objects.create(
        collaborator=collab,
        path=path,
        target_level="Lieutenant",
        is_active=True,
        enrolled_at=now,
    )

    # Finalized evaluation (comp1 at level 3 -> met, comp2 at level 1 -> not met)
    ev = EvaluationModel.objects.create(
        collaborator=collab,
        evaluator=evaluator,
        period="2025.H1",
        evaluation_date=now,
        status="DRAFT",
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev, competency=comp1, current_level=3
    )
    CompetencyMeasurementModel.objects.create(
        evaluation=ev, competency=comp2, current_level=1
    )
    ev.status = "ACCEPTED"
    ev.submitted_at = now
    ev.response_date = now
    ev.save()

    # View query:
    summary_view = PathProgressionSummaryViewModel.objects.filter(
        collaborator_id=collab.id, path_id=path.id
    ).first()

    # Manual aggregation query:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(DISTINCT cr.id) AS total_reqs,
                COUNT(DISTINCT CASE
                    WHEN cm.current_level >= cr.minimum_level THEN cr.id
                END) AS reqs_met
            FROM path_enrollments pe
            JOIN path_levels pl ON pl.path_id = pe.path_id
                               AND pl.name = pe.target_level
            JOIN competency_requirements cr ON cr.path_level_id = pl.id
            LEFT JOIN evaluations e ON e.collaborator_id = pe.collaborator_id
                                   AND e.status IN ('ACCEPTED', 'CONTESTED')
            LEFT JOIN competency_measurements cm ON cm.evaluation_id = e.id
                                                AND cm.competency_id = cr.competency_id
            WHERE pe.collaborator_id = %s
              AND pe.is_active = 1
            """,
            [collab.id.hex],
        )
        total_reqs, reqs_met = cursor.fetchone()

    assert summary_view is not None
    assert summary_view.total_requirements == total_reqs
    assert summary_view.requirements_met == reqs_met
    assert summary_view.total_requirements == 2
    assert summary_view.requirements_met == 1
    assert summary_view.completion_percentage == 50.0
