package service

import (
	"bytes"
	"context"
	"encoding/json"

	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type ProgramService struct {
	log *zap.Logger
	db  *db.Queries
}

func NewProgramService(queries *db.Queries, log *zap.Logger) *ProgramService {
	return &ProgramService{log: log, db: queries}
}

func (ps *ProgramService) GetProgramInfo(name string) {

}

func (ps *ProgramService) GetProgramRequirements(ctx context.Context, name string) error {
	data, err := ps.db.GetProgramRequirements(ctx, name)

	if err != nil {
		return err
	}
  
	var requirementGroups interface{}
	json.Unmarshal(data.RequirementGroups, &requirementGroups)

	var prettyJSON bytes.Buffer
	err = json.Indent(&prettyJSON, data.RequirementGroups, "", "\t")
	if err != nil {

		return err
	}

	ps.log.Info("CSP Violation: %s", zap.String("groups", prettyJSON.String()))

	return nil
}
