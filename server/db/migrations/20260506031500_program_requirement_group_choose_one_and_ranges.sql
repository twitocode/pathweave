-- +goose Up
ALTER TABLE program_requirement_group
  ALTER COLUMN group_units TYPE TEXT USING group_units::TEXT;

ALTER TABLE program_requirement_group
  ADD COLUMN IF NOT EXISTS choose_one BOOLEAN NOT NULL DEFAULT FALSE;

-- +goose Down
ALTER TABLE program_requirement_group
  DROP COLUMN IF EXISTS choose_one;

ALTER TABLE program_requirement_group
  ALTER COLUMN group_units TYPE INTEGER USING (
    CASE
      WHEN group_units ~ '^\d+$' THEN group_units::INTEGER
      ELSE NULL
    END
  );
