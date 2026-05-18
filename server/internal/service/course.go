package service

import (
	"context"
	"fmt"
	"strings"

	"github.com/pgvector/pgvector-go"
	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
	"golang.org/x/sync/errgroup"
)

type CourseService struct {
	db  *db.Queries
	log *zap.Logger
	es  *EmbeddingService
}

type CourseInfo struct {
	ID          int    `json:"id"`
	Code        string `json:"code"`
	Name        string `json:"name"`
	Description string `json:"description"`
	Units       int    `json:"units"`
	Term        string `json:"term"`
	LevelNumber int    `json:"level_number"`
}

type Schedule struct {
	ID               int     `json:"id"`
	ComboIndex       int     `json:"combo_index"`
	Day              string  `json:"day"`
	StartTime        string  `json:"start_time"`
	EndTime          string  `json:"end_time"`
	Type             string  `json:"type"`
	Section          string  `json:"section"`
	Teacher          string  `json:"teacher"`
	Building         string  `json:"building"`
	RoomNumber       string  `json:"room_number"`
	Mode             string  `json:"mode"`
	IsInPerson       bool    `json:"is_in_person"`
	AvgDifficulty    float64 `json:"avg_difficulty"`
	AvgRating        float64 `json:"avg_rating"`
	StudentSentiment string  `json:"student_sentiment"`
}

func NewCourseService(queries *db.Queries, log *zap.Logger, es *EmbeddingService) *CourseService {
	return &CourseService{
		db: queries, log: log, es: es,
	}
}

func (cs *CourseService) GetCourseInfo(ctx context.Context, code string) (*CourseInfo, error) {
	course, err := cs.db.GetCourseByCode(ctx, code)

	if err != nil {
		return nil, err
	}

	return &CourseInfo{
		ID:          int(course.ID),
		Code:        course.Code,
		Name:        course.Name,
		Description: course.Description,
		Units:       int(course.Units),
		Term:        course.Term,
		LevelNumber: int(course.LevelNumber.Int32),
	}, nil
}

func (cs *CourseService) GetCourseSchedules(ctx context.Context, id int) ([]*Schedule, error) {
	rows, err := cs.db.GetSchedulesForCourse(ctx, int64(id))

	schedules := make([]*Schedule, len(rows))

	for i, r := range rows {
		schedules[i] = &Schedule{
			ID:               int(r.ID),
			ComboIndex:       int(r.ComboIndex),
			Day:              r.Day,
			StartTime:        common.TimeToString(r.StartTime),
			EndTime:          common.TimeToString(r.EndTime),
			Type:             r.Type,
			Section:          strings.Split(r.Section, " ")[1],
			Teacher:          r.InstructorName,
			Building:         r.Building,
			RoomNumber:       r.RoomNumber,
			Mode:             r.Mode,
			IsInPerson:       r.IsInPerson,
			AvgDifficulty:    common.NumericToFloat64(r.AvgDifficulty),
			AvgRating:        common.NumericToFloat64(r.AvgRating),
			StudentSentiment: "",
		}
	}
	if err != nil {
		return make([]*Schedule, 0), err
	}

	return schedules, nil
}

func (cs *CourseService) CreateCourseEmbeddingsBatched(ctx context.Context, codes []string) error {
	var embeddingStrings []string
	var validCodes []string

	for _, code := range codes {
		info, err := cs.GetCourseInfo(ctx, code)
		if err != nil {
			cs.log.Warn("could not get info for course", zap.String("code", code), zap.Error(err))
			continue
		}

		embeddingString := fmt.Sprintf("course_code: %s, course_name: %s, description: %s, available in the %s term, is a level %d course", info.Code, info.Name, info.Description, info.Term, info.LevelNumber)
		embeddingStrings = append(embeddingStrings, embeddingString)
		validCodes = append(validCodes, code)
	}

	if len(embeddingStrings) == 0 {
		return nil
	}

	embeddings, err := cs.es.CreateEmbeddingBatched(ctx, embeddingStrings)
	if err != nil {
		return err
	}

	if len(embeddings) != len(validCodes) {
		return fmt.Errorf("embedding count mismatch: expected %d, got %d", len(validCodes), len(embeddings))
	}

	for i, embeddingArray := range embeddings {
		err = cs.db.CreateEmbedding(ctx, db.CreateEmbeddingParams{
			Code:      validCodes[i],
			Embedding: pgvector.NewVector(common.Float64ToFloat32Slice(embeddingArray)),
		})
		if err != nil {
			cs.log.Error("could not save embedding to db", zap.String("code", validCodes[i]), zap.Error(err))
		}
	}
	return nil
}

func (cs *CourseService) CreateEmbeddingForEveryCourse(ctx context.Context) {
	courseCodes, err := cs.db.GetAllCourseCodes(ctx)
	if err != nil {
		cs.log.Fatal("could not get course codes for embedding", zap.Error(err))
		return
	}

	batchSize := 50 //per api call
	g, gCtx := errgroup.WithContext(ctx)

	for i := 0; i < len(courseCodes); i += batchSize {
		end := i + batchSize
		if end > len(courseCodes) {
			end = len(courseCodes)
		}
		
		batch := courseCodes[i:end]
		
		g.Go(func() error {
			return cs.CreateCourseEmbeddingsBatched(gCtx, batch)
		})
	}

	if err := g.Wait(); err != nil {
		cs.log.Error("Something failed while creating embeddings", zap.Error(err))
	} else {
		cs.log.Info("Successfully created embeddings for all courses!")
	}
}
