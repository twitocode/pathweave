-- +goose Up
ALTER TABLE user_details ADD completed BOOLEAN;
-- +goose Down
ALTER TABLE users_details DROP completed;