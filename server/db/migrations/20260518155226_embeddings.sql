-- +goose Up
ALTER TABLE course ADD embedding vector(512);

-- +goose Down
ALTER TABLE course DROP embedding;
