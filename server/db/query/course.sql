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


