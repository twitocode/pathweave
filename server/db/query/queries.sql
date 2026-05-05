-- name: GetUserByEmail :one
SELECT id, email, created_at, updated_at
FROM users
WHERE email = $1
LIMIT 1;

-- name: CreateUser :one
INSERT INTO users (email)
VALUES ($1)
RETURNING id, email, created_at, updated_at;


-- name: CreateUserDetails :one
INSERT INTO user_details (
    wake_up_time,
    bedtime,
    user_id,
    program_id,
    year,
    job_info,
    home_address,
    future_plans,
    professor_quality,
    teaching_style,
    completed
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true)
RETURNING user_id;

-- name: AddUserCompletedCourse :exec
INSERT INTO user_detail_completed_courses (user_id, course_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: AddUserAvoidedCourse :exec
INSERT INTO user_detail_avoided_courses (user_id, course_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: GetProgramIDByName :one
SELECT id
FROM program
WHERE name = $1
LIMIT 1;

-- name: GetCourseIDByCode :one
SELECT id
FROM course
WHERE code = $1
LIMIT 1;

-- name: HasCompletedOnboarding :one
SELECT COALESCE((SELECT completed FROM user_details WHERE user_id = $1), false)::boolean;

