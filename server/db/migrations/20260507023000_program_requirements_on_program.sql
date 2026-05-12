-- +goose Up
ALTER TABLE program
  ADD COLUMN IF NOT EXISTS source_url TEXT,
  ADD COLUMN IF NOT EXISTS requirement_codes TEXT[] NOT NULL DEFAULT '{}',
  ADD COLUMN IF NOT EXISTS requirements_by_level JSONB NOT NULL DEFAULT '[]'::jsonb;

ALTER TABLE course
  ADD COLUMN IF NOT EXISTS level_number INTEGER;

CREATE INDEX IF NOT EXISTS idx_program_requirement_codes_gin
  ON program
  USING GIN (requirement_codes);

-- +goose Down
DROP INDEX IF EXISTS idx_program_requirement_codes_gin;

ALTER TABLE course
  DROP COLUMN IF EXISTS level_number;

ALTER TABLE program
  DROP COLUMN IF EXISTS requirements_by_level,
  DROP COLUMN IF EXISTS requirement_codes,
  DROP COLUMN IF EXISTS source_url;
