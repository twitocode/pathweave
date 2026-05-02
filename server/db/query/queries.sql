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
    user_id,
    program,
    year,
    completed_courses,
    job_info,
    home_address,
    future_plans,
    professor_quality,
    teaching_style,
    avoided_courses,
    completed
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, true)
RETURNING id;


-- name: HasCompletedOnboarding :one
SELECT EXISTS (SELECT user_id FROM user_details WHERE user_id=$1);