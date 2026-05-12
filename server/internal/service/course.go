package service

import (
	"context"

	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type CourseService struct {
	db  *db.Queries
	log *zap.Logger
}

type CourseInfo struct {
	Code        string `json:"code"`
	Name        string `json:"name"`
	Description string `json:"description`
	Units       int    `json:"units"`
	Term        string `json:"term"`
	LevelNumber int    `json:"level_number"`
}

func NewCourseService(queries *db.Queries, log *zap.Logger) *CourseService {
	return &CourseService{
		db: queries, log: log,
	}
}

func (cs *CourseService) GetCourseInfo(ctx context.Context, code string) (*CourseInfo, error) {
	course, err := cs.db.GetCourseByCode(ctx, code)

	if err != nil {
		return nil, err
	}

	return &CourseInfo{
		Code:        course.Code,
		Name:        course.Name,
		Description: course.Description,
		Units:       int(course.Units),
		Term:        course.Term,
		LevelNumber: int(course.LevelNumber.Int32),
	}, nil
}
