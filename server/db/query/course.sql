-- name: AddUserCompletedCourse :exec
INSERT INTO user_detail_completed_courses (user_id, course_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: AddUserAvoidedCourse :exec
INSERT INTO user_detail_avoided_courses (user_id, course_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: GetCourseIDByCode :one
SELECT id
FROM course
WHERE code = $1
LIMIT 1;

-- name: GetCourseByCode :one
SELECT id, code, name, description, restrictions, prerequisites, units, term, level_number
FROM course
WHERE code = $1
LIMIT 1;

-- name: GetSchedulesForCourse :many
SELECT sc.*, t.avg_difficulty, t.avg_rating
FROM schedule_combo AS sc
JOIN teacher t
  ON t.name = sc.instructor_name
WHERE sc.course_id = $1
ORDER BY sc.section;

-- name: CreateEmbedding :exec
UPDATE course
SET embedding = $2
WHERE code = $1;

-- name: GetAllCourseCodes :one
SELECT array_agg(code)::varchar[]
FROM course;


-- name: GetCoursesByVectorSearch :many
SELECT 
    c.id, c.code, c.name, c.description, c.restrictions, c.prerequisites, c.units, c.term, c.level_number,
    c.embedding <=> sqlc.narg('embedding')::vector AS distance
FROM course c
LEFT JOIN program_courses pc 
    ON pc.course_id = c.id 
    AND pc.program_id = sqlc.narg('user_program_id')::bigint
WHERE
    (sqlc.narg('level')::int  IS NULL OR c.level_number = sqlc.narg('level'))
    AND (sqlc.narg('term')::text  IS NULL OR c.term = sqlc.narg('term'))
    AND (sqlc.narg('code')::text  IS NULL OR c.code ILIKE sqlc.narg('code') || '%')
    AND NOT EXISTS (
        SELECT 1 FROM user_detail_avoided_courses uac
        WHERE uac.course_id = c.id AND uac.user_id = sqlc.arg('user_id')::uuid
    )
ORDER BY
    CASE WHEN sqlc.narg('embedding')::vector IS NULL 
        THEN (CASE WHEN pc.program_id IS NOT NULL THEN 0 ELSE 1 END)
        ELSE (c.embedding <=> sqlc.narg('embedding')::vector) - (CASE WHEN pc.program_id IS NOT NULL THEN 0.3 ELSE 0 END)
    END ASC
LIMIT sqlc.arg('limit')::int;