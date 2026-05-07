-- name: GetProgramIDByName :one
SELECT id
FROM program
WHERE name = $1
LIMIT 1;

-- name: GetProgramRequirements :one
SELECT 
    p.id as program_id,
    p.name as program_name,
    (
        SELECT json_agg(json_build_object(
            'group_id', prg.id,
            'level_label', prg.level_label,
            'level_total_units', prg.level_total_units,
            'group_units', prg.group_units,
            'choose_one', prg.choose_one,
            'items', (
                SELECT json_agg(json_build_object(
                    'text', pri.requirement_text,
                    'code', pri.course_code,
                    'id', pri.course_id,
                    'is_course', pri.is_course,
                    'name', c.name,
                    'description', c.description,
                    'restrictions', c.restrictions
                ) ORDER BY pri.sort_order)
                FROM program_requirement_item pri
                LEFT JOIN course c ON pri.course_id = c.id
                WHERE pri.requirement_group_id = prg.id
            )
        ) ORDER BY prg.sort_order)
        FROM program_requirement_group prg
        WHERE prg.program_id = p.id
    ) as requirement_groups
FROM program p
WHERE p.name = $1;


