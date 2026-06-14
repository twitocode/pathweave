-- +goose Up

CREATE TABLE IF NOT EXISTS scrape_runs (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  source TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'received',
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT,
  course_count INTEGER NOT NULL DEFAULT 0,
  program_count INTEGER NOT NULL DEFAULT 0,
  teacher_count INTEGER NOT NULL DEFAULT 0,
  schedule_term_count INTEGER NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  staged_at TIMESTAMPTZ,
  promoted_at TIMESTAMPTZ,
  failed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  CONSTRAINT scrape_runs_status_check CHECK (
    status IN ('received', 'staged', 'promoting', 'succeeded', 'failed')
  )
);

CREATE TABLE IF NOT EXISTS staging_courses (
  run_id UUID NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
  course_code TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (run_id, course_code)
);

CREATE TABLE IF NOT EXISTS staging_programs (
  run_id UUID NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
  program_name TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (run_id, program_name)
);

CREATE TABLE IF NOT EXISTS staging_teachers (
  run_id UUID NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
  rmp_id TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (run_id, rmp_id)
);

CREATE TABLE IF NOT EXISTS staging_schedules (
  run_id UUID NOT NULL REFERENCES scrape_runs(id) ON DELETE CASCADE,
  term TEXT NOT NULL,
  course_code TEXT NOT NULL,
  payload JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  PRIMARY KEY (run_id, term, course_code)
);

CREATE INDEX IF NOT EXISTS idx_staging_courses_run_id
  ON staging_courses (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_programs_run_id
  ON staging_programs (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_teachers_run_id
  ON staging_teachers (run_id);

CREATE INDEX IF NOT EXISTS idx_staging_schedules_run_id_term
  ON staging_schedules (run_id, term);

-- +goose Down

DROP INDEX IF EXISTS idx_staging_schedules_run_id_term;
DROP INDEX IF EXISTS idx_staging_teachers_run_id;
DROP INDEX IF EXISTS idx_staging_programs_run_id;
DROP INDEX IF EXISTS idx_staging_courses_run_id;

DROP TABLE IF EXISTS staging_schedules;
DROP TABLE IF EXISTS staging_teachers;
DROP TABLE IF EXISTS staging_programs;
DROP TABLE IF EXISTS staging_courses;
DROP TABLE IF EXISTS scrape_runs;
