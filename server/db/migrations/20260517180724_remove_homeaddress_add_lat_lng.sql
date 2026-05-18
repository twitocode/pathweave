-- +goose Up
ALTER TABLE user_details DROP COLUMN home_address;
ALTER TABLE user_details ADD COLUMN lat DOUBLE PRECISION;
ALTER TABLE user_details ADD COLUMN lng DOUBLE PRECISION;

-- +goose Down
ALTER TABLE user_details DROP COLUMN lat;
ALTER TABLE user_details DROP COLUMN lng;
ALTER TABLE user_details ADD COLUMN home_address TEXT NOT NULL DEFAULT '';