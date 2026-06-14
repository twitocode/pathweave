package scraping

import (
	"context"
	"encoding/json"
	"errors"
	"strings"

	"github.com/google/uuid"
	"github.com/twitocode/pathweave/go-api/internal/db"
)

func (s *ScrapeIngestService) StageArtifacts(ctx context.Context, runID uuid.UUID, req StageScrapeArtifactsRequest) (StageScrapeArtifactsResult, error) {
	tx, err := s.pool.Begin(ctx)
	if err != nil {
		return StageScrapeArtifactsResult{}, err
	}
	defer func() { _ = tx.Rollback(ctx) }()

	qtx := s.db.WithTx(tx)
	if err := clearRunStaging(ctx, qtx, runID); err != nil {
		return StageScrapeArtifactsResult{}, err
	}

	for _, course := range req.Courses {
		record, err := normalizeCourseRecord(course)
		if err != nil {
			return StageScrapeArtifactsResult{}, err
		}
		payload, err := json.Marshal(course)
		if err != nil {
			return StageScrapeArtifactsResult{}, err
		}
		if err := qtx.StageCoursePayload(ctx, db.StageCoursePayloadParams{
			RunID:      runID,
			CourseCode: record.Code,
			Payload:    payload,
		}); err != nil {
			return StageScrapeArtifactsResult{}, err
		}
	}

	for _, program := range req.Programs {
		name := strings.TrimSpace(program.ProgramName)
		if name == "" {
			return StageScrapeArtifactsResult{}, errors.New("program_name is required")
		}
		payload, err := json.Marshal(program)
		if err != nil {
			return StageScrapeArtifactsResult{}, err
		}
		if err := qtx.StageProgramPayload(ctx, db.StageProgramPayloadParams{
			RunID:       runID,
			ProgramName: name,
			Payload:     payload,
		}); err != nil {
			return StageScrapeArtifactsResult{}, err
		}
	}

	for _, teacher := range req.Teachers {
		rmpID := strings.TrimSpace(teacher.ID)
		if rmpID == "" {
			return StageScrapeArtifactsResult{}, errors.New("teacher id is required")
		}
		payload, err := json.Marshal(teacher)
		if err != nil {
			return StageScrapeArtifactsResult{}, err
		}
		if err := qtx.StageTeacherPayload(ctx, db.StageTeacherPayloadParams{
			RunID:   runID,
			RmpID:   rmpID,
			Payload: payload,
		}); err != nil {
			return StageScrapeArtifactsResult{}, err
		}
	}

	terms := make(map[string]struct{})
	for _, termPayload := range req.Schedules {
		term := normalizeTerm(termPayload.Term)
		if term == "Unknown" {
			return StageScrapeArtifactsResult{}, errors.New("schedule term is required")
		}
		terms[term] = struct{}{}
		for _, course := range termPayload.Courses {
			if course.Term == "" {
				course.Term = term
			}
			courseCode := strings.TrimSpace(course.CourseCode)
			if courseCode == "" {
				return StageScrapeArtifactsResult{}, errors.New("schedule course_code is required")
			}
			payload, err := json.Marshal(course)
			if err != nil {
				return StageScrapeArtifactsResult{}, err
			}
			if err := qtx.StageSchedulePayload(ctx, db.StageSchedulePayloadParams{
				RunID:      runID,
				Term:       term,
				CourseCode: courseCode,
				Payload:    payload,
			}); err != nil {
				return StageScrapeArtifactsResult{}, err
			}
		}
	}

	result := StageScrapeArtifactsResult{
		RunID:             runID,
		CourseCount:       len(req.Courses),
		ProgramCount:      len(req.Programs),
		TeacherCount:      len(req.Teachers),
		ScheduleTermCount: len(terms),
	}
	if err := qtx.MarkScrapeRunStaged(ctx, db.MarkScrapeRunStagedParams{
		ID:                runID,
		CourseCount:       int32(result.CourseCount),
		ProgramCount:      int32(result.ProgramCount),
		TeacherCount:      int32(result.TeacherCount),
		ScheduleTermCount: int32(result.ScheduleTermCount),
	}); err != nil {
		return StageScrapeArtifactsResult{}, err
	}

	return result, tx.Commit(ctx)
}
