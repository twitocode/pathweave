-- +goose Up
ALTER TABLE section ADD class_number SMALLINT NOT NULL DEFAULT -1;

-- +goose Down
ALTER TABLE section DROP COLUMN class_number;