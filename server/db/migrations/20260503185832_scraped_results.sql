-- +goose Up

-- many courses and many students
CREATE TABLE IF NOT EXISTS program (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  name TEXT NOT NULL
);

-- many teachers, many students, and many schedule combos
CREATE TABLE IF NOT EXISTS course (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  restrictions TEXT NOT NULL,
  prerequisites TEXT[] NOT NULL DEFAULT '{}',
  units INTEGER NOT NULL,
  term TEXT NOT NULL
);

-- many courses 
CREATE TABLE IF NOT EXISTS teacher (
  id SERIAL PRIMARY KEY,
  name TEXT NOT NULL,
  avg_rating NUMERIC(3, 1) CHECK (avg_rating >= 0 AND avg_rating <= 10),
  avg_difficulty NUMERIC(3, 1) CHECK (avg_difficulty >= 0 AND avg_difficulty <= 10),
  department TEXT NOT NULL,
  rmp_id TEXT NOT NULL UNIQUE,
  num_ratings INTEGER NOT NULL
);

-- one course
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

  -- makes it a one to many relationship
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE
);

-- many to many relationship

-- this is known as a join table
CREATE TABLE IF NOT EXISTS program_courses (
  program_id BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,

  -- this is a composite id
  PRIMARY KEY (program_id, course_id)
);

CREATE TABLE IF NOT EXISTS course_teachers (
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,
  teacher_id INTEGER NOT NULL REFERENCES teacher(id) ON DELETE CASCADE,
  PRIMARY KEY (course_id, teacher_id)
);

CREATE TABLE IF NOT EXISTS teacher_programs (
  teacher_id INTEGER NOT NULL REFERENCES teacher(id) ON DELETE CASCADE,
  program_id BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
  PRIMARY KEY (teacher_id, program_id)
);

-- one user <-> one course
ALTER TABLE user_details
  ADD COLUMN IF NOT EXISTS program_id BIGINT REFERENCES program(id) ON DELETE RESTRICT;

ALTER TABLE user_details
  DROP COLUMN IF EXISTS program,
  DROP COLUMN IF EXISTS completed_courses,
  DROP COLUMN IF EXISTS avoided_courses;


CREATE TABLE IF NOT EXISTS user_detail_completed_courses (
  user_id UUID NOT NULL REFERENCES user_details(user_id) ON DELETE CASCADE,
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, course_id)
);

CREATE TABLE IF NOT EXISTS user_detail_avoided_courses (
  user_id UUID NOT NULL REFERENCES user_details(user_id) ON DELETE CASCADE,
  course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,
  PRIMARY KEY (user_id, course_id)
);

-- +goose Down

DROP TABLE IF EXISTS user_detail_avoided_courses;
DROP TABLE IF EXISTS user_detail_completed_courses;

ALTER TABLE user_details
  ADD COLUMN IF NOT EXISTS program TEXT NOT NULL DEFAULT '',
  ADD COLUMN IF NOT EXISTS completed_courses TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
  ADD COLUMN IF NOT EXISTS avoided_courses TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
  DROP COLUMN IF EXISTS program_id;

DROP TABLE IF EXISTS teacher_programs;
DROP TABLE IF EXISTS course_teachers;
DROP TABLE IF EXISTS program_courses;
DROP TABLE IF EXISTS schedule_combo;
DROP TABLE IF EXISTS teacher;
DROP TABLE IF EXISTS course;
DROP TABLE IF EXISTS program;
