-- name: GetProgramIDByName :one
SELECT id
FROM program
WHERE name = $1
LIMIT 1;

