package scraping

import (
	"context"
	"encoding/json"
	"errors"
	"strings"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgtype"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

func (s *ScrapeIngestService) PromoteRun(ctx context.Context, runID uuid.UUID) (PromoteScrapeRunResult, error) {
	log := s.log.With(zap.String("run_id", runID.String()))
	log.Info("scrape promote started")

	tx, err := s.pool.Begin(ctx)
	if err != nil {
		log.Error("scrape promote failed to begin transaction", zap.Error(err))
		return PromoteScrapeRunResult{}, err
	}

	qtx := s.db.WithTx(tx)
	if err := qtx.MarkScrapeRunPromoting(ctx, runID); err != nil {
		_ = tx.Rollback(ctx)
		log.Error("scrape promote failed to mark run promoting", zap.Error(err))
		return PromoteScrapeRunResult{}, err
	}
	if err := s.promoteRunInTx(ctx, qtx, runID, log); err != nil {
		_ = tx.Rollback(ctx)
		_ = s.db.MarkScrapeRunFailed(ctx, db.MarkScrapeRunFailedParams{
			ID:           runID,
			ErrorMessage: pgtype.Text{String: err.Error(), Valid: true},
		})
		log.Error("scrape promote failed", zap.Error(err))
		return PromoteScrapeRunResult{}, err
	}
	if err := qtx.MarkScrapeRunSucceeded(ctx, runID); err != nil {
		_ = tx.Rollback(ctx)
		log.Error("scrape promote failed to mark run succeeded", zap.Error(err))
		return PromoteScrapeRunResult{}, err
	}
	if err := tx.Commit(ctx); err != nil {
		log.Error("scrape promote failed to commit transaction", zap.Error(err))
		return PromoteScrapeRunResult{}, err
	}
	log.Info("scrape promote completed")
	return PromoteScrapeRunResult{RunID: runID, Status: "succeeded", Promoted: true}, nil
}

func (s *ScrapeIngestService) promoteRunInTx(ctx context.Context, qtx *db.Queries, runID uuid.UUID, log *zap.Logger) error {
	log.Info("scrape promote loading staged payloads")
	courses, err := loadPayloads[rawCoursePayload](ctx, qtx.ListStagedCoursePayloads, runID)
	if err != nil {
		return err
	}
	programs, err := loadPayloads[rawProgramPayload](ctx, qtx.ListStagedProgramPayloads, runID)
	if err != nil {
		return err
	}
	teachers, err := loadPayloads[rawTeacherPayload](ctx, qtx.ListStagedTeacherPayloads, runID)
	if err != nil {
		return err
	}
	schedules, err := loadPayloads[rawScheduleCoursePayload](ctx, qtx.ListStagedSchedulePayloads, runID)
	if err != nil {
		return err
	}
	terms, err := qtx.ListStagedScheduleTerms(ctx, runID)
	if err != nil {
		return err
	}
	log.Info("scrape promote loaded staged payloads",
		zap.Int("courses", len(courses)),
		zap.Int("programs", len(programs)),
		zap.Int("teachers", len(teachers)),
		zap.Int("schedule_courses", len(schedules)),
		zap.Strings("terms", terms),
	)

	log.Info("scrape promote upserting courses", zap.Int("count", len(courses)))
	normalizedCourses, titleCodeMap, err := promoteCourses(ctx, qtx, courses)
	if err != nil {
		return err
	}
	log.Info("scrape promote upserted courses", zap.Int("count", len(normalizedCourses)))

	log.Info("scrape promote loading course ids")
	courseIDs, err := loadCourseIDs(ctx, qtx)
	if err != nil {
		return err
	}
	log.Info("scrape promote loaded course ids", zap.Int("count", len(courseIDs)))

	scheduleTeacherNames := collectScheduleTeacherNames(schedules)
	log.Info("scrape promote upserting teachers",
		zap.Int("rmp_teachers", len(teachers)),
		zap.Int("schedule_teacher_names", len(scheduleTeacherNames)),
	)
	if err := promoteTeachers(ctx, qtx, teachers, scheduleTeacherNames); err != nil {
		return err
	}
	log.Info("scrape promote upserted teachers")

	log.Info("scrape promote loading teacher ids")
	teacherIDs, err := loadTeacherIDsByName(ctx, qtx)
	if err != nil {
		return err
	}
	log.Info("scrape promote loaded teacher ids", zap.Int("count", len(teacherIDs)))

	log.Info("scrape promote upserting programs", zap.Int("count", len(programs)))
	if err := promotePrograms(ctx, qtx, programs, courseIDs); err != nil {
		return err
	}
	log.Info("scrape promote upserted programs", zap.Int("count", len(programs)))

	log.Info("scrape promote linking course teachers")
	if err := promoteCourseTeacherLinks(ctx, qtx, teachers, schedules, courseIDs, teacherIDs, titleCodeMap); err != nil {
		return err
	}
	log.Info("scrape promote linked course teachers")

	log.Info("scrape promote deleting sections for terms", zap.Strings("terms", terms))

	var normalizedTerms []string
	for _, term := range terms {
		normalizedTerms = append(normalizedTerms, normalizeTerm(term))
	}

	if err := deleteSectionsForTerms(ctx, qtx, normalizedTerms); err != nil {
		return err
	}
	log.Info("scrape promote deleted sections for terms")

	log.Info("scrape promote upserting sections", zap.Int("schedule_courses", len(schedules)))
	if err := promoteSections(ctx, qtx, schedules, courseIDs, teacherIDs, titleCodeMap); err != nil {
		return err
	}
	log.Info("scrape promote upserted sections")

	log.Info("scrape promote linking teacher programs")
	if err := promoteTeacherProgramLinks(ctx, qtx); err != nil {
		return err
	}
	log.Info("scrape promote linked teacher programs")
	return nil
}

func clearRunStaging(ctx context.Context, q *db.Queries, runID uuid.UUID) error {
	if err := q.ClearScrapeRunStagedSchedules(ctx, runID); err != nil {
		return err
	}
	if err := q.ClearScrapeRunStagedTeachers(ctx, runID); err != nil {
		return err
	}
	if err := q.ClearScrapeRunStagedPrograms(ctx, runID); err != nil {
		return err
	}
	return q.ClearScrapeRunStagedCourses(ctx, runID)
}

func loadPayloads[T any](ctx context.Context, list func(context.Context, uuid.UUID) ([][]byte, error), runID uuid.UUID) ([]T, error) {
	payloads, err := list(ctx, runID)
	if err != nil {
		return nil, err
	}
	items := make([]T, 0, len(payloads))
	for _, payload := range payloads {
		var item T
		if err := json.Unmarshal(payload, &item); err != nil {
			return nil, err
		}
		items = append(items, item)
	}
	return items, nil
}

func promoteCourses(ctx context.Context, q *db.Queries, courses []rawCoursePayload) ([]normalizedCourseRecord, map[string]string, error) {
	records := make([]normalizedCourseRecord, 0, len(courses))
	titleCodeMap := make(map[string]string, len(courses))
	for _, course := range courses {
		record, err := normalizeCourseRecord(course)
		if err != nil {
			return nil, nil, err
		}
		records = append(records, record)
		if record.Name != "" {
			titleCodeMap[record.Name] = record.Code
		}
		var level pgtype.Int4
		if record.LevelNumber != nil {
			level = pgtype.Int4{Int32: *record.LevelNumber, Valid: true}
		}
		if err := q.UpsertScrapeCourse(ctx, db.UpsertScrapeCourseParams{
			Code:          record.Code,
			Name:          record.Name,
			Description:   record.Description,
			Restrictions:  record.Restrictions,
			Prerequisites: record.Prerequisites,
			Units:         record.Units,
			LevelNumber:   level,
		}); err != nil {
			return nil, nil, err
		}
	}
	return records, titleCodeMap, nil
}

func promoteTeachers(ctx context.Context, q *db.Queries, teachers []rawTeacherPayload, scheduleTeacherNames map[string]struct{}) error {
	// 1. Deduplicate incoming teachers by keeping only the one with the most ratings per name
	bestTeachers := make(map[string]rawTeacherPayload)
	for _, teacher := range teachers {
		name := strings.TrimSpace(teacher.Name)
		if name == "" {
			continue
		}
		key := strings.ToLower(name)
		if existing, ok := bestTeachers[key]; ok {
			if teacher.NumRatings > existing.NumRatings {
				bestTeachers[key] = teacher
			}
		} else {
			bestTeachers[key] = teacher
		}
	}

	// 2. Upsert the deduplicated best teachers
	knownNames := make(map[string]struct{}, len(bestTeachers))
	for _, teacher := range bestTeachers {
		name := strings.TrimSpace(teacher.Name)
		rmpID := strings.TrimSpace(teacher.ID)
		if rmpID == "" {
			return errors.New("teacher id is required")
		}
		department := strings.TrimSpace(teacher.Department)
		if department == "" {
			department = "Unknown"
		}
		if err := q.UpsertScrapeTeacher(ctx, db.UpsertScrapeTeacherParams{
			Name:          name,
			AvgRating:     numericFromFloat64(teacher.AvgRating),
			AvgDifficulty: numericFromFloat64(teacher.AvgDifficulty),
			Department:    department,
			RmpID:         rmpID,
			NumRatings:    teacher.NumRatings,
		}); err != nil {
			return err
		}
		knownNames[strings.ToLower(name)] = struct{}{}
	}

	existingTeachers, err := q.ListScrapeTeacherIDsByName(ctx)
	if err == nil {
		for _, row := range existingTeachers {
			knownNames[strings.ToLower(row.Name)] = struct{}{}
		}
	}

	for name := range scheduleTeacherNames {
		if _, ok := knownNames[strings.ToLower(name)]; ok {
			continue
		}
		rmpID := nonRMPID(name)
		if err := q.UpsertScrapeTeacher(ctx, db.UpsertScrapeTeacherParams{
			Name:          name,
			AvgRating:     numericFromFloat64(0),
			AvgDifficulty: numericFromFloat64(0),
			Department:    "Unknown",
			RmpID:         rmpID,
			NumRatings:    0,
		}); err != nil {
			return err
		}
	}
	return nil
}

func promotePrograms(ctx context.Context, q *db.Queries, programs []rawProgramPayload, courseIDs map[string]int64) error {
	for _, program := range programs {
		name := strings.TrimSpace(program.ProgramName)
		if name == "" {
			return errors.New("program_name is required")
		}
		requirementsByLevel := program.RequirementsByLevel
		if len(requirementsByLevel) == 0 {
			requirementsByLevel = json.RawMessage(`[]`)
		}
		requirementCodes := normalizeProgramRequirementCodes(program.Requirements)
		programID, err := q.UpsertScrapeProgram(ctx, db.UpsertScrapeProgramParams{
			ProgramName:         name,
			SourceUrl:           nullableText(program.URL),
			RequirementCodes:    requirementCodes,
			RequirementsByLevel: []byte(requirementsByLevel),
		})
		if err != nil {
			return err
		}
		if err := q.DeleteScrapeProgramCourses(ctx, programID); err != nil {
			return err
		}
		for _, code := range requirementCodes {
			courseID, ok := courseIDs[code]
			if !ok {
				continue
			}
			if err := q.InsertScrapeProgramCourse(ctx, db.InsertScrapeProgramCourseParams{
				ProgramID: programID,
				CourseID:  courseID,
			}); err != nil {
				return err
			}
		}
	}
	return nil
}

func promoteCourseTeacherLinks(ctx context.Context, q *db.Queries, teachers []rawTeacherPayload, schedules []rawScheduleCoursePayload, courseIDs map[string]int64, teacherIDs map[string]int32, titleCodeMap map[string]string) error {
	for _, teacher := range teachers {
		teacherID, ok := teacherIDs[strings.TrimSpace(teacher.Name)]
		if !ok {
			continue
		}
		for _, code := range teacher.Courses {
			courseID, ok := courseIDs[strings.TrimSpace(code)]
			if !ok {
				continue
			}
			if err := q.InsertScrapeCourseTeacher(ctx, db.InsertScrapeCourseTeacherParams{
				CourseID:  courseID,
				TeacherID: teacherID,
			}); err != nil {
				return err
			}
		}
	}

	for _, course := range schedules {
		courseID, ok := courseIDs[resolveScheduleCourseCode(course, titleCodeMap)]
		if !ok {
			continue
		}
		for _, section := range course.Sections {
			for _, name := range getAllInstructorNames(section) {
				teacherID, ok := teacherIDs[name]
				if !ok {
					continue
				}
				if err := q.InsertScrapeCourseTeacher(ctx, db.InsertScrapeCourseTeacherParams{
					CourseID:  courseID,
					TeacherID: teacherID,
				}); err != nil {
					return err
				}
			}
		}
	}
	return nil
}

func deleteSectionsForTerms(ctx context.Context, q *db.Queries, terms []string) error {
	if len(terms) == 0 {
		return nil
	}
	return q.DeleteScrapeSectionsForTerms(ctx, terms)
}

func promoteSections(ctx context.Context, q *db.Queries, schedules []rawScheduleCoursePayload, courseIDs map[string]int64, teacherIDs map[string]int32, titleCodeMap map[string]string) error {
	for _, course := range schedules {
		term := normalizeTerm(course.Term)
		courseID, ok := courseIDs[resolveScheduleCourseCode(course, titleCodeMap)]
		if !ok {
			continue
		}
		insertedSections := make([]normalizedSection, 0, len(course.Sections))
		for _, section := range course.Sections {
			name, sectionType := parseSectionName(section.SectionName)
			if name == "" {
				continue
			}
			mode, isInPerson := detectDeliveryMode(section)
			sectionID, err := q.CreateScrapeSection(ctx, db.CreateScrapeSectionParams{
				CourseID:   courseID,
				Name:       name,
				Type:       sectionType,
				Term:       term,
				Mode:       mode,
				IsInPerson: isInPerson,
			})
			if err != nil {
				return err
			}
			for _, detail := range section.Details {
				startTime, err := parseNullableScrapeTime(detail.StartTime)
				if err != nil {
					return err
				}
				endTime, err := parseNullableScrapeTime(detail.EndTime)
				if err != nil {
					return err
				}
				building, room := parseScrapeLocation(detail.Room)
				if err := q.CreateScrapeSectionMeeting(ctx, db.CreateScrapeSectionMeetingParams{
					SectionID: sectionID,
					Days:      strings.TrimSpace(detail.Days),
					StartTime: startTime,
					EndTime:   endTime,
					Building:  building,
					Room:      room,
				}); err != nil {
					return err
				}
			}
			linkedTeacherIDs := make(map[int32]struct{})
			for _, instructor := range getAllInstructorNames(section) {
				teacherID, ok := teacherIDs[instructor]
				if !ok {
					continue
				}
				if _, seen := linkedTeacherIDs[teacherID]; seen {
					continue
				}
				linkedTeacherIDs[teacherID] = struct{}{}
				if err := q.InsertScrapeSectionTeacher(ctx, db.InsertScrapeSectionTeacherParams{
					SectionID: sectionID,
					TeacherID: teacherID,
				}); err != nil {
					return err
				}
			}
			insertedSections = append(insertedSections, normalizedSection{
				ID:            sectionID,
				Name:          name,
				Type:          sectionType,
				ParentName:    strings.TrimSpace(section.Parent),
				InstructorSet: getSectionInstructorSet(section),
			})
		}
		for _, ref := range buildSectionReferences(insertedSections) {
			if err := q.InsertScrapeSectionReference(ctx, db.InsertScrapeSectionReferenceParams{
				ParentSectionID: ref.ParentID,
				ChildSectionID:  ref.ChildID,
			}); err != nil {
				return err
			}
		}
	}
	return nil
}

func promoteTeacherProgramLinks(ctx context.Context, q *db.Queries) error {
	return q.InsertScrapeTeacherProgramLinks(ctx)
}

func loadCourseIDs(ctx context.Context, q *db.Queries) (map[string]int64, error) {
	rows, err := q.ListScrapeCourseIDs(ctx)
	if err != nil {
		return nil, err
	}
	ids := make(map[string]int64, len(rows))
	for _, row := range rows {
		ids[row.Code] = row.ID
	}
	return ids, nil
}

func loadTeacherIDsByName(ctx context.Context, q *db.Queries) (map[string]int32, error) {
	rows, err := q.ListScrapeTeacherIDsByName(ctx)
	if err != nil {
		return nil, err
	}
	ids := make(map[string]int32, len(rows))
	for _, row := range rows {
		ids[row.Name] = row.ID
	}
	return ids, nil
}
