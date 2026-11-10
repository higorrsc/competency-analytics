"""Migration to create collaborator_competency_history database view."""

from typing import ClassVar

from django.db import migrations

CREATE_VIEW_SQL = """
-- View: collaborator_competency_history
-- Purpose: Optimized CQRS read model providing chronological competency evolution
--          for each collaborator, including previous level and level changes using
--          SQL window functions (LAG).
-- Dependencies: collaborators, evaluations, competency_measurements, competencies
-- Status filtering: Finalized evaluations only ('ACEITA', 'CONTESTADA').
CREATE VIEW collaborator_competency_history AS
SELECT
    cm.id as id,
    c.id as collaborator_id,
    comp.id as competency_id,
    comp.name as competency_name,
    e.evaluation_date,
    e.period,
    cm.current_level,
    LAG(cm.current_level) OVER (
        PARTITION BY c.id, comp.id
        ORDER BY e.evaluation_date, e.id
    ) as previous_level,
    cm.current_level - LAG(cm.current_level) OVER (
        PARTITION BY c.id, comp.id
        ORDER BY e.evaluation_date, e.id
    ) as level_change,
    e.status
FROM collaborators c
JOIN evaluations e ON e.collaborator_id = c.id
JOIN competency_measurements cm ON cm.evaluation_id = e.id
JOIN competencies comp ON comp.id = cm.competency_id
WHERE e.status IN ('ACCEPTED', 'CONTESTED', 'ACEITA', 'CONTESTADA');
"""

DROP_VIEW_SQL = "DROP VIEW IF EXISTS collaborator_competency_history;"


class Migration(migrations.Migration):
    """Create collaborator_competency_history view with window functions."""

    dependencies: ClassVar[list[tuple[str, str]]] = [
        ("competency", "0001_initial"),
    ]

    operations: ClassVar[list[migrations.RunSQL]] = [
        migrations.RunSQL(
            sql=CREATE_VIEW_SQL,
            reverse_sql=DROP_VIEW_SQL,
        ),
    ]
