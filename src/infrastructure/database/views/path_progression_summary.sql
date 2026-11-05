-- View: path_progression_summary
-- Purpose: Optimized CQRS read model summarizing progress toward target path levels
--          by counting requirements met from the latest finalized evaluation.
-- Dependencies: collaborators, path_enrollments, path_levels, competency_requirements,
--               evaluations, competency_measurements
-- Status filtering: Finalized evaluations only ('ACEITA', 'CONTESTADA').
CREATE VIEW path_progression_summary AS
SELECT
    c.id as collaborator_id,
    pe.path_id as path_id,
    pe.target_level as target_level,
    COUNT(DISTINCT cr.id) as total_requirements,
    COUNT(DISTINCT CASE 
        WHEN latest_cm.current_level >= cr.minimum_level 
        THEN cr.id 
    END) as requirements_met,
    ROUND(
        100.0 * COUNT(DISTINCT CASE 
            WHEN latest_cm.current_level >= cr.minimum_level 
            THEN cr.id 
        END) / COUNT(DISTINCT cr.id),
        2
    ) as completion_percentage
FROM collaborators c
JOIN path_enrollments pe ON pe.collaborator_id = c.id AND pe.is_active = TRUE
JOIN path_levels pl ON pl.path_id = pe.path_id AND pl.name = pe.target_level
JOIN competency_requirements cr ON cr.path_level_id = pl.id
LEFT JOIN (
    SELECT
        e.collaborator_id,
        cm.competency_id,
        cm.current_level,
        ROW_NUMBER() OVER (
            PARTITION BY e.collaborator_id, cm.competency_id
            ORDER BY e.evaluation_date DESC, e.id DESC
        ) as rn
    FROM evaluations e
    JOIN competency_measurements cm ON cm.evaluation_id = e.id
    WHERE e.status IN ('ACCEPTED', 'CONTESTED', 'ACEITA', 'CONTESTADA')
) latest_cm ON latest_cm.collaborator_id = c.id 
            AND latest_cm.competency_id = cr.competency_id
            AND latest_cm.rn = 1
WHERE EXISTS (
    SELECT 1 FROM evaluations e_check
    WHERE e_check.collaborator_id = c.id
      AND e_check.status IN ('ACCEPTED', 'CONTESTED', 'ACEITA', 'CONTESTADA')
)
GROUP BY c.id, pe.path_id, pe.target_level;
