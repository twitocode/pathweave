package service

import (
	"context"
	"encoding/json"

	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type ProgramRequirements struct {
	ProgramID          int64           `json:"program_id"`
	ProgramName        string          `json:"program_name"`
	RequirementGroups  json.RawMessage `json:"requirement_groups"`
	RequirementCourses any             `json:"requirement_courses"`
}

type ProgramService struct {
	log *zap.Logger
	db  *db.Queries
}

func NewProgramService(queries *db.Queries, log *zap.Logger) *ProgramService {
	return &ProgramService{log: log, db: queries}
}

func (ps *ProgramService) GetProgramInfo(name string) {

}

func (ps *ProgramService) GetProgramRequirements(ctx context.Context, name string) (ProgramRequirements, error) {
	data, err := ps.db.GetProgramRequirements(ctx, name)

	if err != nil {
		return ProgramRequirements{}, err
	}

	return ProgramRequirements{
		ProgramID:          data.ProgramID,
		ProgramName:        data.ProgramName,
		RequirementGroups:  json.RawMessage(data.RequirementGroups),
		RequirementCourses: data.RequirementCourses,
	}, nil

}
