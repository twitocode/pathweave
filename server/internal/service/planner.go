package service

import (
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type PlannerService struct {
	log *zap.Logger
	db  *db.Queries
}

func NewPlannerService(queries *db.Queries, log *zap.Logger) *PlannerService {
	return &PlannerService{log: log, db: queries}
}

func (ps *PlannerService) GetProgramInfo(name string) {

}
