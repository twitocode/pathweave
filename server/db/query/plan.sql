-- name: GetPlans :many
SELECT p.*, COUNT(ps.course_id) as course_count
FROM plan p
LEFT JOIN plan_section ps ON p.id = ps.plan_id
WHERE p.user_id = @user_id
GROUP BY p.id;

-- name: CreatePlan :one
INSERT INTO plan (title, term, user_id) VALUES (@title, @term, @user_id)
RETURNING id;