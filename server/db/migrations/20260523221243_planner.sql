-- +goose Up
CREATE TABLE IF NOT EXISTS plan (
  id UUID PRIMARY KEY DEFAULT uuidv7(),
  title TEXT NOT NULL DEFAULT '',
  term TEXT NOT NULL DEFAULT 'Unknown',
  
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

  user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE
);

-- the plan is to save the plan's section details and then fetch specific course details using the plan's course_id
CREATE TABLE IF NOT EXISTS plan_section (
  plan_id UUID NOT NULL REFERENCES plan(id) ON DELETE CASCADE,
  course_id BIGINT NOT NULL REFERENCES section(id) ON DELETE CASCADE,

  PRIMARY KEY (plan_id, course_id)
);

-- +goose Down
DROP TABLE plan_section;
DROP TABLE plan;