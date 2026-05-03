-- +goose Up
ALTER TABLE user_details ADD wake_up_time TIME DEFAULT('00:00:00');
ALTER TABLE user_details ADD bedtime TIME DEFAULT('00:00:00');

-- +goose Down
ALTER TABLE user_details DROP wake_up_time;
ALTER TABLE user_details DROP bedtime;