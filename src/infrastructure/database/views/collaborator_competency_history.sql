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
