-- +goose Up
DROP TABLE IF EXISTS plan_section CASCADE;

CREATE TABLE IF NOT EXISTS plan_course (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  plan_id UUID NOT NULL REFERENCES plan(id) ON DELETE CASCADE,
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,

  UNIQUE(plan_id, course_id)
);

CREATE TABLE IF NOT EXISTS plan_section (
  plan_course_id UUID NOT NULL REFERENCES plan_course(id) ON DELETE CASCADE,
  section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
  
  PRIMARY KEY (plan_course_id, section_id)
);

-- +goose Down
DROP TABLE IF EXISTS plan_section CASCADE;
DROP TABLE IF EXISTS plan_course CASCADE;

CREATE TABLE IF NOT EXISTS plan_section (
  plan_id UUID NOT NULL REFERENCES plan(id) ON DELETE CASCADE,
  course_id BIGINT NOT NULL REFERENCES section(id) ON DELETE CASCADE,
  PRIMARY KEY (plan_id, course_id)
);