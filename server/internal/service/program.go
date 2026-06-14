package service

import (
	"context"
	"encoding/json"

	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type ProgramRequirements struct {
	ProgramID         int64           `json:"program_id"`
	ProgramName       string          `json:"program_name"`
	RequirementGroups json.RawMessage `json:"requirement_groups"`
}

type ProgramService struct {
	log *zap.Logger
	db  *db.Queries
}

func NewProgramService(queries *db.Queries, log *zap.Logger) *ProgramService {
	return &ProgramService{log: log, db: queries}
}

func (ps *ProgramService) GetUserProgramName(ctx context.Context, user *db.User) (string, error) {
  name, err := ps.db.GetUserProgramName(ctx, user.ID)
  if err != nil {
    return "", err
  }

  return name, nil
}

func (ps *ProgramService) GetProgramRequirements(ctx context.Context, name string) (ProgramRequirements, error) {
	data, err := ps.db.GetProgramRequirements(ctx, name)

	if err != nil {
		return ProgramRequirements{}, err
	}

	return ProgramRequirements{
		ProgramID:         data.ProgramID,
		ProgramName:       data.ProgramName,
		RequirementGroups: json.RawMessage(data.RequirementGroups),
	}, nil

}

func (ps *ProgramService) GetUserProgramRequirementCodes(ctx context.Context, user *db.User) ([]string, error) {
	codes, err := ps.db.GetUserProgramRequirementCodes(ctx, user.ID)
	if err != nil {
		return nil, err
	}
	return codes, nil
}

func (ps *ProgramService) GetUserProgramRequirementCodesAvailableInTerm(ctx context.Context, user *db.User, term string) ([]string, error) {
	codes, err := ps.db.GetUserProgramRequirementCodesAvailableInTerm(ctx, db.GetUserProgramRequirementCodesAvailableInTermParams{
		ID:   user.ID,
		Term: term,
	})
	if err != nil {
		return nil, err
	}
	return codes, nil
}
