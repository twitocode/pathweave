-- +goose Up
CREATE TABLE IF NOT EXISTS program_antirequisites (
    program_id BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
    course_id BIGINT NOT NULL REFERENCES course(id) ON DELETE CASCADE,
    PRIMARY KEY (program_id, course_id)
);

-- +goose Down
DROP TABLE IF EXISTS program_antirequisites;
