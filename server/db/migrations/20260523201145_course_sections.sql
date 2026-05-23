-- +goose Up
DROP TABLE IF EXISTS schedule_combo CASCADE;

ALTER TABLE course DROP COLUMN IF EXISTS term;

CREATE TABLE IF NOT EXISTS section (
  id SERIAL PRIMARY KEY,
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  type VARCHAR(3) NOT NULL,
  term TEXT NOT NULL DEFAULT 'Unknown',
  mode TEXT NOT NULL DEFAULT 'Unknown',
  is_in_person BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS section_meeting (
  id SERIAL PRIMARY KEY,
  section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
  days TEXT NOT NULL DEFAULT '',
  start_time TIME,
  end_time TIME,
  building TEXT NOT NULL DEFAULT '',
  room TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS section_teachers (
  section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
  teacher_id INTEGER NOT NULL REFERENCES teacher(id) ON DELETE CASCADE,
  PRIMARY KEY (section_id, teacher_id)
);

CREATE TABLE IF NOT EXISTS section_references (
  parent_section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
  child_section_id INTEGER NOT NULL REFERENCES section(id) ON DELETE CASCADE,
  PRIMARY KEY (parent_section_id, child_section_id)
);

-- +goose Down
DROP TABLE IF EXISTS section_references;
DROP TABLE IF EXISTS section_teachers;
DROP TABLE IF EXISTS section_meeting;
DROP TABLE IF EXISTS section;

ALTER TABLE course ADD COLUMN IF NOT EXISTS term TEXT NOT NULL DEFAULT '';

CREATE TABLE IF NOT EXISTS schedule_combo (
  id SERIAL PRIMARY KEY,
  combo_index INTEGER NOT NULL DEFAULT 0,
  day VARCHAR(3) NOT NULL,
  start_time TIME NOT NULL DEFAULT '00:00:00',
  end_time TIME NOT NULL DEFAULT '00:00:00',
  type VARCHAR(3) NOT NULL,
  section TEXT NOT NULL,
  instructor_name TEXT NOT NULL DEFAULT 'Staff',
  building TEXT NOT NULL DEFAULT '',
  room TEXT NOT NULL DEFAULT '',
  mode TEXT NOT NULL DEFAULT 'Unknown',
  is_in_person BOOLEAN NOT NULL DEFAULT FALSE,
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE
);
