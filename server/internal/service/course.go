package service

import (
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type CourseService struct {

}

func NewCourseService(queries *db.Queries, log *zap.Logger) *CourseService {
  return &CourseService{}
}

func (cs *CourseService) GetCourseInfo() {
  
}
