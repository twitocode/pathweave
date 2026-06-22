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
SELECT id, code, name, description, restrictions, prerequisites, units, level_number
FROM course c
WHERE c.code = $1
LIMIT 1;

-- name: GetSchedulesForCourse :many
SELECT 
  sm.id,
  s.name AS section,
  s.type,
  s.term,
  s.mode,
  s.class_number,
  s.is_in_person,
  sm.days AS day,
  sm.start_time,
  sm.end_time,
  sm.building,
  sm.room,
  COALESCE(STRING_AGG(DISTINCT t.name, ', '), 'Staff') AS instructor_name,
  COALESCE(AVG(t.avg_difficulty), 0) AS avg_difficulty,
  COALESCE(AVG(t.avg_rating), 0) AS avg_rating,
  COALESCE(ARRAY_AGG(DISTINCT parent_s.name) FILTER (WHERE parent_s.name IS NOT NULL), '{}'::varchar[])::varchar[] AS parents
FROM section AS s
JOIN section_meeting AS sm ON sm.section_id = s.id
LEFT JOIN section_teachers AS st ON st.section_id = s.id
LEFT JOIN teacher AS t ON t.id = st.teacher_id
LEFT JOIN section_references sr ON sr.child_section_id = s.id
LEFT JOIN section parent_s ON parent_s.id = sr.parent_section_id
WHERE s.course_id = $1
GROUP BY sm.id, s.id
ORDER BY s.name;

-- name: GetCourseSectionsByTerm :many
SELECT 
  sm.id,
  s.name AS section,
  s.type,
  s.term,
  s.mode,
  s.class_number,
  s.is_in_person,
  sm.days AS day,
  sm.start_time,
  sm.end_time,
  sm.building,
  sm.room,
  COALESCE(STRING_AGG(DISTINCT t.name, ', '), 'Staff') AS instructor_name,
  COALESCE(AVG(t.avg_difficulty), 0) AS avg_difficulty,
  COALESCE(AVG(t.avg_rating), 0) AS avg_rating,
  COALESCE(ARRAY_AGG(DISTINCT parent_s.name) FILTER (WHERE parent_s.name IS NOT NULL), '{}'::varchar[])::varchar[] AS parents
FROM section AS s
JOIN section_meeting AS sm ON sm.section_id = s.id
LEFT JOIN section_teachers AS st ON st.section_id = s.id
LEFT JOIN teacher AS t ON t.id = st.teacher_id
JOIN course AS c ON c.id = s.course_id
LEFT JOIN section_references sr ON sr.child_section_id = s.id
LEFT JOIN section parent_s ON parent_s.id = sr.parent_section_id
WHERE c.code = sqlc.arg('code')::text AND s.term = sqlc.arg('term')::text
GROUP BY sm.id, s.id
ORDER BY s.name;

-- name: CreateEmbedding :exec
UPDATE course
SET embedding = $2
WHERE code = $1;

-- name: GetAllCourseCodes :one
SELECT array_agg(code)::varchar[]
FROM course;


-- name: GetCoursesByVectorSearch :many
SELECT 
    c.id, c.code, c.name, c.description, c.restrictions, c.prerequisites, c.units, c.level_number,
    CASE WHEN sqlc.arg('has_embedding')::boolean = false 
        THEN NULL 
        ELSE c.embedding <=> sqlc.arg('embedding')::vector 
    END AS distance
FROM course c
LEFT JOIN program_courses pc 
    ON pc.course_id = c.id 
    AND pc.program_id = sqlc.narg('user_program_id')::bigint
WHERE
    (sqlc.narg('level')::int  IS NULL OR c.level_number = sqlc.narg('level'))
    AND (sqlc.narg('term')::text IS NULL OR EXISTS (
        SELECT 1 FROM section sec WHERE sec.course_id = c.id AND sec.term = sqlc.narg('term')
    ))
    AND (sqlc.narg('code')::text  IS NULL OR c.code ILIKE sqlc.narg('code') || '%')
    AND NOT EXISTS (
        SELECT 1 FROM user_detail_avoided_courses uac
        WHERE uac.course_id = c.id AND uac.user_id = sqlc.arg('user_id')::uuid
    )
    AND (sqlc.narg('user_program_id')::bigint IS NULL OR c.id NOT IN (
        SELECT course_id FROM program_antirequisites WHERE program_id = sqlc.narg('user_program_id')::bigint
    ))
ORDER BY
    CASE WHEN sqlc.arg('has_embedding')::boolean = false 
        THEN (CASE WHEN pc.program_id IS NOT NULL THEN 0 ELSE 1 END)
        ELSE (c.embedding <=> sqlc.arg('embedding')::vector) - (CASE WHEN pc.program_id IS NOT NULL THEN 0.3 ELSE 0 END)
    END ASC
LIMIT sqlc.arg('limit')::int;

-- name: GetTermsForCourse :one
SELECT coalesce(array_agg(DISTINCT s.term)::varchar[], '{}'::varchar[])::varchar[] as terms
FROM section s
JOIN course c ON c.id = s.course_id
WHERE c.code = $1;