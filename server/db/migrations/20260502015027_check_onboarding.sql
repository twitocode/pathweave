-- +goose Up
ALTER TABLE user_details ADD completed BOOLEAN;
-- +goose Down
ALTER TABLE user_details DROP completed;