-- +goose Up
CREATE TABLE IF NOT EXISTS users (
    id BIGSERIAL PRIMARY KEY,
    email TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS user_details (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL UNIQUE REFERENCES users (id) ON DELETE CASCADE,

    program TEXT NOT NULL,
    year SMALLINT NOT NULL,
    completed_courses TEXT[] NOT NULL DEFAULT '{}'::TEXT[],
    
    job_info TEXT NOT NULL CHECK (char_length(job_info) <= 1000),
    home_address TEXT NOT NULL,
    future_plans TEXT NOT NULL CHECK (char_length(future_plans) <= 2000),

    professor_quality SMALLINT NOT NULL CHECK (professor_quality BETWEEN 1 AND 3),
    teaching_style SMALLINT NOT NULL CHECK (teaching_style BETWEEN 1 AND 3),
    avoided_courses TEXT[] NOT NULL DEFAULT '{}'::TEXT[],

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- +goose Down
DROP TABLE user_details;
DROP TABLE users;