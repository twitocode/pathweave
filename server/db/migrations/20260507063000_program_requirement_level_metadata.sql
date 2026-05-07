-- +goose Up
CREATE TABLE IF NOT EXISTS program_requirement_level (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  program_id BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
  level_number TEXT,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_program_requirement_level_program_id
  ON program_requirement_level(program_id);

ALTER TABLE program_requirement_group
  ADD COLUMN IF NOT EXISTS requirement_level_id BIGINT REFERENCES program_requirement_level(id) ON DELETE CASCADE,
  ADD COLUMN IF NOT EXISTS group_name TEXT;

-- +goose Down
ALTER TABLE program_requirement_group
  DROP COLUMN IF EXISTS group_name,
  DROP COLUMN IF EXISTS requirement_level_id;

DROP TABLE IF EXISTS program_requirement_level;
