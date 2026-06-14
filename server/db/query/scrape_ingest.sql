-- name: CreateScrapeRun :one
INSERT INTO scrape_runs (source, metadata)
VALUES ($1, $2)
RETURNING id, source, status, metadata, error_message, course_count, program_count, teacher_count, schedule_term_count, started_at, staged_at, promoted_at, failed_at, created_at, updated_at;

-- name: GetScrapeRun :one
SELECT id, source, status, metadata, error_message, course_count, program_count, teacher_count, schedule_term_count, started_at, staged_at, promoted_at, failed_at, created_at, updated_at
FROM scrape_runs
WHERE id = $1
LIMIT 1;

-- name: MarkScrapeRunStaged :exec
UPDATE scrape_runs
SET status = 'staged',
    course_count = $2,
    program_count = $3,
    teacher_count = $4,
    schedule_term_count = $5,
    staged_at = NOW(),
    updated_at = NOW(),
    error_message = NULL
WHERE id = $1;

-- name: MarkScrapeRunPromoting :exec
UPDATE scrape_runs
SET status = 'promoting',
    updated_at = NOW(),
    error_message = NULL
WHERE id = $1;

-- name: MarkScrapeRunSucceeded :exec
UPDATE scrape_runs
SET status = 'succeeded',
    promoted_at = NOW(),
    updated_at = NOW(),
    error_message = NULL
WHERE id = $1;

-- name: MarkScrapeRunFailed :exec
UPDATE scrape_runs
SET status = 'failed',
    failed_at = NOW(),
    updated_at = NOW(),
    error_message = $2
WHERE id = $1;

-- name: ClearScrapeRunStagedSchedules :exec
DELETE FROM staging_schedules WHERE run_id = $1;

-- name: ClearScrapeRunStagedTeachers :exec
DELETE FROM staging_teachers WHERE run_id = $1;

-- name: ClearScrapeRunStagedPrograms :exec
DELETE FROM staging_programs WHERE run_id = $1;

-- name: ClearScrapeRunStagedCourses :exec
DELETE FROM staging_courses WHERE run_id = $1;

-- name: StageCoursePayload :exec
INSERT INTO staging_courses (run_id, course_code, payload)
VALUES ($1, $2, $3)
ON CONFLICT (run_id, course_code) DO UPDATE SET
  payload = EXCLUDED.payload;

-- name: StageProgramPayload :exec
INSERT INTO staging_programs (run_id, program_name, payload)
VALUES ($1, $2, $3)
ON CONFLICT (run_id, program_name) DO UPDATE SET
  payload = EXCLUDED.payload;

-- name: StageTeacherPayload :exec
INSERT INTO staging_teachers (run_id, rmp_id, payload)
VALUES ($1, $2, $3)
ON CONFLICT (run_id, rmp_id) DO UPDATE SET
  payload = EXCLUDED.payload;

-- name: StageSchedulePayload :exec
INSERT INTO staging_schedules (run_id, term, course_code, payload)
VALUES ($1, $2, $3, $4)
ON CONFLICT (run_id, term, course_code) DO UPDATE SET
  payload = EXCLUDED.payload;

-- name: ListStagedCoursePayloads :many
SELECT payload
FROM staging_courses
WHERE run_id = $1
ORDER BY course_code;

-- name: ListStagedProgramPayloads :many
SELECT payload
FROM staging_programs
WHERE run_id = $1
ORDER BY program_name;

-- name: ListStagedTeacherPayloads :many
SELECT payload
FROM staging_teachers
WHERE run_id = $1
ORDER BY rmp_id;

-- name: ListStagedSchedulePayloads :many
SELECT payload
FROM staging_schedules
WHERE run_id = $1
ORDER BY term, course_code;

-- name: ListStagedScheduleTerms :many
SELECT DISTINCT term
FROM staging_schedules
WHERE run_id = $1
ORDER BY term;

-- name: UpsertScrapeCourse :exec
INSERT INTO course (code, name, description, restrictions, prerequisites, units, level_number)
VALUES ($1, $2, $3, $4, $5, $6, $7)
ON CONFLICT (code) DO UPDATE SET
  name = EXCLUDED.name,
  description = EXCLUDED.description,
  restrictions = EXCLUDED.restrictions,
  prerequisites = EXCLUDED.prerequisites,
  units = EXCLUDED.units,
  level_number = EXCLUDED.level_number;

-- name: ListScrapeCourseIDs :many
SELECT code, id
FROM course
ORDER BY code;

-- name: UpsertScrapeTeacher :exec
INSERT INTO teacher (name, avg_rating, avg_difficulty, department, rmp_id, num_ratings)
VALUES ($1, $2, $3, $4, $5, $6)
ON CONFLICT (rmp_id) DO UPDATE SET
  name = EXCLUDED.name,
  avg_rating = EXCLUDED.avg_rating,
  avg_difficulty = EXCLUDED.avg_difficulty,
  department = EXCLUDED.department,
  num_ratings = EXCLUDED.num_ratings;

-- name: ListScrapeTeacherIDsByName :many
SELECT name, id
FROM teacher
ORDER BY name;

-- name: UpsertScrapeProgram :one
WITH updated AS (
  UPDATE program
  SET source_url = sqlc.arg('source_url'),
      requirement_codes = sqlc.arg('requirement_codes'),
      requirements_by_level = sqlc.arg('requirements_by_level')
  WHERE program.name = sqlc.arg('program_name')
  RETURNING id
),
inserted AS (
  INSERT INTO program (name, source_url, requirement_codes, requirements_by_level)
  SELECT sqlc.arg('program_name'),
         sqlc.arg('source_url'),
         sqlc.arg('requirement_codes'),
         sqlc.arg('requirements_by_level')
  WHERE NOT EXISTS (SELECT 1 FROM updated)
  RETURNING id
)
SELECT id FROM updated
UNION ALL
SELECT id FROM inserted
LIMIT 1;

-- name: DeleteScrapeProgramCourses :exec
DELETE FROM program_courses
WHERE program_id = $1;

-- name: InsertScrapeProgramCourse :exec
INSERT INTO program_courses (program_id, course_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: InsertScrapeCourseTeacher :exec
INSERT INTO course_teachers (course_id, teacher_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: DeleteScrapeSectionsForTerms :exec
DELETE FROM section
WHERE term = ANY($1::text[]);

-- name: CreateScrapeSection :one
INSERT INTO section (course_id, name, type, term, mode, is_in_person)
VALUES ($1, $2, $3, $4, $5, $6)
RETURNING id;

-- name: CreateScrapeSectionMeeting :exec
INSERT INTO section_meeting (section_id, days, start_time, end_time, building, room)
VALUES ($1, $2, $3, $4, $5, $6);

-- name: InsertScrapeSectionTeacher :exec
INSERT INTO section_teachers (section_id, teacher_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: InsertScrapeSectionReference :exec
INSERT INTO section_references (parent_section_id, child_section_id)
VALUES ($1, $2)
ON CONFLICT DO NOTHING;

-- name: InsertScrapeTeacherProgramLinks :exec
INSERT INTO teacher_programs (teacher_id, program_id)
SELECT DISTINCT ct.teacher_id, pc.program_id
FROM course_teachers ct
JOIN program_courses pc ON pc.course_id = ct.course_id
ON CONFLICT DO NOTHING;
