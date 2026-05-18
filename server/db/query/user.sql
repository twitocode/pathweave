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
    lat,
    lng,
    future_plans,
    professor_quality,
    teaching_style,
    completed
)
VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, true)
RETURNING user_id;

-- name: HasCompletedOnboarding :one
SELECT COALESCE((SELECT completed FROM user_details WHERE user_id = $1), false)::boolean;


