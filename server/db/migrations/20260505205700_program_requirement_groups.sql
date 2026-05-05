-- +goose Up
CREATE TABLE IF NOT EXISTS program_requirement_group (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  program_id BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
  level_label TEXT NOT NULL,
  level_total_units INTEGER,
  group_units INTEGER,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_program_requirement_group_program_id
  ON program_requirement_group(program_id);

CREATE TABLE IF NOT EXISTS program_requirement_item (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  requirement_group_id BIGINT NOT NULL REFERENCES program_requirement_group(id) ON DELETE CASCADE,
  requirement_text TEXT NOT NULL,
  course_code TEXT,
  course_id BIGINT REFERENCES course(id) ON DELETE SET NULL,
  is_course BOOLEAN NOT NULL DEFAULT FALSE,
  sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_program_requirement_item_requirement_group_id
  ON program_requirement_item(requirement_group_id);

CREATE INDEX IF NOT EXISTS idx_program_requirement_item_course_id
  ON program_requirement_item(course_id);

-- +goose Down
DROP TABLE IF EXISTS program_requirement_item;
DROP TABLE IF EXISTS program_requirement_group;
