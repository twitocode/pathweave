-- name: GetProgramIDByName :one
SELECT id
FROM program
WHERE name = $1
LIMIT 1;

-- name: GetProgramRequirements :one
WITH requirement_hierarchy AS (
  SELECT
    prl.program_id,
    jsonb_build_object(
      'levels',
      jsonb_agg(
        jsonb_build_object(
          'level_number', prl.level_number,
          'index', prl.sort_order,
          'groups', COALESCE(
            (
              SELECT jsonb_agg(
                jsonb_build_object(
                  'name', prg.group_name,
                  'units', prg.group_units,
                  'choose_one', prg.choose_one,
                  'requirements', COALESCE(
                    (
                      SELECT jsonb_agg(
                        jsonb_build_object(
                          'type', CASE WHEN pri.is_course THEN 'course' ELSE 'text' END,
                          'text', pri.requirement_text,
                          'course_code', pri.course_code
                        )
                        ORDER BY pri.sort_order, pri.id
                      )
                      FROM program_requirement_item pri
                      WHERE pri.requirement_group_id = prg.id
                    ),
                    '[]'::jsonb
                  )
                )
                ORDER BY prg.sort_order, prg.id
              )
              FROM program_requirement_group prg
              WHERE prg.requirement_level_id = prl.id
            ),
            '[]'::jsonb
          )
        )
        ORDER BY prl.sort_order, prl.id
      )
    ) AS requirements
  FROM program_requirement_level prl
  GROUP BY prl.program_id
)
SELECT
    p.id as program_id,
    p.name as program_name,
    COALESCE(rh.requirements, p.requirements_by_level, '{"levels":[]}'::jsonb) as requirement_groups
FROM program p
LEFT JOIN requirement_hierarchy rh ON rh.program_id = p.id
WHERE p.name = $1;


