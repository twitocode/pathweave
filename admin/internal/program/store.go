package program

import (
	"context"
	"database/sql"
	"errors"
	"fmt"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"
)

type Store struct {
	pool *pgxpool.Pool
}

func NewStore(pool *pgxpool.Pool) *Store {
	return &Store{pool: pool}
}

func (s *Store) EnsureSchema(ctx context.Context) error {
	statements := []string{
		`CREATE TABLE IF NOT EXISTS program_requirement_level (
			id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
			program_id BIGINT NOT NULL REFERENCES program(id) ON DELETE CASCADE,
			level_number TEXT,
			sort_order INTEGER NOT NULL DEFAULT 0
		)`,
		`CREATE INDEX IF NOT EXISTS idx_program_requirement_level_program_id
			ON program_requirement_level(program_id)`,
		`ALTER TABLE program_requirement_group
			ALTER COLUMN group_units TYPE TEXT USING group_units::TEXT`,
		`ALTER TABLE program_requirement_group
			ADD COLUMN IF NOT EXISTS choose_one BOOLEAN NOT NULL DEFAULT FALSE`,
		`ALTER TABLE program_requirement_group
			ADD COLUMN IF NOT EXISTS requirement_level_id BIGINT REFERENCES program_requirement_level(id) ON DELETE CASCADE`,
		`ALTER TABLE program_requirement_group
			ADD COLUMN IF NOT EXISTS group_name TEXT`,
	}

	for _, statement := range statements {
		if _, err := s.pool.Exec(ctx, statement); err != nil {
			return fmt.Errorf("ensure program requirement schema: %w", err)
		}
	}

	return nil
}

func (s *Store) ListPrograms(ctx context.Context) ([]Summary, error) {
	rows, err := s.pool.Query(ctx, `SELECT id, name FROM program ORDER BY id`)
	if err != nil {
		return nil, fmt.Errorf("list programs: %w", err)
	}
	defer rows.Close()

	programs := make([]Summary, 0)
	for rows.Next() {
		var program Summary
		if err := rows.Scan(&program.ID, &program.Name); err != nil {
			return nil, fmt.Errorf("scan program summary: %w", err)
		}
		programs = append(programs, program)
	}
	if err := rows.Err(); err != nil {
		return nil, fmt.Errorf("iterate programs: %w", err)
	}
	return programs, nil
}

func (s *Store) GetProgram(ctx context.Context, id int64) (EditableProgram, error) {
	var program EditableProgram
	var sourceURL sql.NullString
	var requirementsByLevel []byte

	err := s.pool.QueryRow(
		ctx,
		`SELECT id, name, source_url, requirements_by_level
         FROM program
         WHERE id = $1`,
		id,
	).Scan(&program.ID, &program.Name, &sourceURL, &requirementsByLevel)
	if err != nil {
		return EditableProgram{}, fmt.Errorf("get program: %w", err)
	}

	if sourceURL.Valid {
		program.SourceURL = sourceURL.String
	}

	levels, err := LevelsFromRequirements(requirementsByLevel)
	if err != nil {
		return EditableProgram{}, err
	}
	program.Levels = levels
	return program, nil
}

type SaveResult struct {
	ProgramID              int64
	LinkedCourseCount      int
	PlaceholderCourseCount int
}

func (s *Store) SaveProgram(ctx context.Context, payload UpsertPayload) (SaveResult, error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return SaveResult{}, fmt.Errorf("begin tx: %w", err)
	}
	defer tx.Rollback(ctx)

	var programID int64
	err = tx.QueryRow(
		ctx,
		`SELECT id FROM program WHERE name = $1 LIMIT 1`,
		payload.Name,
	).Scan(&programID)

	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			err = tx.QueryRow(
				ctx,
				`INSERT INTO program (name, source_url, requirement_codes, requirements_by_level)
                 VALUES ($1, $2, $3, $4)
                 RETURNING id`,
				payload.Name,
				payload.SourceURL,
				payload.RequirementCodes,
				payload.RequirementsByLevel,
			).Scan(&programID)
			if err != nil {
				return SaveResult{}, fmt.Errorf("insert program: %w", err)
			}
		} else {
			return SaveResult{}, fmt.Errorf("lookup program: %w", err)
		}
	} else {
		_, err = tx.Exec(
			ctx,
			`UPDATE program
             SET source_url = $1,
                 requirement_codes = $2,
                 requirements_by_level = $3
             WHERE id = $4`,
			payload.SourceURL,
			payload.RequirementCodes,
			payload.RequirementsByLevel,
			programID,
		)
		if err != nil {
			return SaveResult{}, fmt.Errorf("update program: %w", err)
		}
	}

	_, err = tx.Exec(ctx, `DELETE FROM program_courses WHERE program_id = $1`, programID)
	if err != nil {
		return SaveResult{}, fmt.Errorf("clear program courses: %w", err)
	}

	linked, placeholders, err := linkProgramCourses(ctx, tx, programID, payload.RequirementCodes)
	if err != nil {
		return SaveResult{}, err
	}

	if err := replaceProgramRequirementHierarchy(ctx, tx, programID, payload.Levels); err != nil {
		return SaveResult{}, err
	}

	if err := tx.Commit(ctx); err != nil {
		return SaveResult{}, fmt.Errorf("commit tx: %w", err)
	}

	return SaveResult{
		ProgramID:              programID,
		LinkedCourseCount:      linked,
		PlaceholderCourseCount: placeholders,
	}, nil
}

// ensureCourseID returns the course row id for code, inserting a minimal placeholder row
// when the catalog has no match so program links and FKs can still be stored.
func ensureCourseID(ctx context.Context, tx pgx.Tx, code string) (id int64, createdPlaceholder bool, err error) {
	err = tx.QueryRow(ctx, `SELECT id FROM course WHERE code = $1 LIMIT 1`, code).Scan(&id)
	if err == nil {
		return id, false, nil
	}
	if !errors.Is(err, pgx.ErrNoRows) {
		return 0, false, fmt.Errorf("lookup course %s: %w", code, err)
	}

	const placeholderNamePrefix = "[pending] "
	name := placeholderNamePrefix + code
	tag, err := tx.Exec(
		ctx,
		`INSERT INTO course (code, name, description, restrictions, prerequisites, units, term)
         VALUES ($1, $2, '', '', $3, 0, 'Unknown')
         ON CONFLICT (code) DO NOTHING`,
		code,
		name,
		[]string{},
	)
	if err != nil {
		return 0, false, fmt.Errorf("insert placeholder course %s: %w", code, err)
	}
	createdPlaceholder = tag.RowsAffected() > 0

	err = tx.QueryRow(ctx, `SELECT id FROM course WHERE code = $1 LIMIT 1`, code).Scan(&id)
	if err != nil {
		return 0, false, fmt.Errorf("resolve course id for %s: %w", code, err)
	}
	return id, createdPlaceholder, nil
}

func linkProgramCourses(ctx context.Context, tx pgx.Tx, programID int64, codes []string) (linked int, placeholders int, err error) {
	for _, code := range codes {
		courseID, created, err := ensureCourseID(ctx, tx, code)
		if err != nil {
			return 0, 0, err
		}
		if created {
			placeholders++
		}

		_, err = tx.Exec(
			ctx,
			`INSERT INTO program_courses (program_id, course_id)
             VALUES ($1, $2)
             ON CONFLICT DO NOTHING`,
			programID,
			courseID,
		)
		if err != nil {
			return 0, 0, fmt.Errorf("insert program course %s: %w", code, err)
		}
		linked++
	}

	return linked, placeholders, nil
}

func replaceProgramRequirementHierarchy(ctx context.Context, tx pgx.Tx, programID int64, levels []LevelInput) error {
	_, err := tx.Exec(ctx, `DELETE FROM program_requirement_group WHERE program_id = $1`, programID)
	if err != nil {
		return fmt.Errorf("clear program requirement groups: %w", err)
	}

	_, err = tx.Exec(ctx, `DELETE FROM program_requirement_level WHERE program_id = $1`, programID)
	if err != nil {
		return fmt.Errorf("clear program requirement levels: %w", err)
	}

	for levelIdx, level := range levels {
		var levelID int64
		err := tx.QueryRow(
			ctx,
			`INSERT INTO program_requirement_level (program_id, level_number, sort_order)
             VALUES ($1, NULLIF($2, ''), $3)
             RETURNING id`,
			programID,
			level.LevelNumber,
			normalizedSortOrder(level.Index, levelIdx),
		).Scan(&levelID)
		if err != nil {
			return fmt.Errorf("insert requirement level: %w", err)
		}

		for groupIdx, group := range level.Groups {
			var groupID int64
			err := tx.QueryRow(
				ctx,
				`INSERT INTO program_requirement_group (
                    program_id,
                    requirement_level_id,
                    level_label,
                    group_name,
                    group_units,
                    choose_one,
                    sort_order
                 )
                 VALUES ($1, $2, COALESCE(NULLIF($3, ''), ''), NULLIF($4, ''), NULLIF($5, ''), $6, $7)
                 RETURNING id`,
				programID,
				levelID,
				level.LevelNumber,
				group.Name,
				group.Units,
				group.ChooseOne,
				groupIdx+1,
			).Scan(&groupID)
			if err != nil {
				return fmt.Errorf("insert requirement group: %w", err)
			}

			for requirementIdx, requirement := range group.Requirements {
				if err := insertRequirementItem(ctx, tx, groupID, requirement, requirementIdx); err != nil {
					return err
				}
			}
		}
	}

	return nil
}

func insertRequirementItem(ctx context.Context, tx pgx.Tx, groupID int64, requirement RequirementRowInput, index int) error {
	item, courseCode, ok := buildRequirementItem(requirement)
	if !ok {
		return nil
	}

	var courseID *int64
	if courseCode != "" {
		id, _, err := ensureCourseID(ctx, tx, courseCode)
		if err != nil {
			return fmt.Errorf("resolve requirement course %s: %w", courseCode, err)
		}
		courseID = &id
	}

	_, err := tx.Exec(
		ctx,
		`INSERT INTO program_requirement_item (
            requirement_group_id,
            requirement_text,
            course_code,
            course_id,
            is_course,
            sort_order
         )
         VALUES ($1, $2, $3, $4, $5, $6)`,
		groupID,
		item.Text,
		item.CourseCode,
		courseID,
		item.Type == "course",
		index+1,
	)
	if err != nil {
		return fmt.Errorf("insert requirement item: %w", err)
	}
	return nil
}

func normalizedSortOrder(value int, fallback int) int {
	if value > 0 {
		return value
	}
	return fallback + 1
}
