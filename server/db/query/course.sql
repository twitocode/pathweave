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