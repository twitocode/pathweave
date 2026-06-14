package service

import (
	"context"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type PlannerService struct {
	db  *db.Queries
}

type Plan struct {
	ID          string `json:"id"`
	Title       string `json:"title"`
	Term        string `json:"term"`
	CreatedAt   string `json:"created_at"`
	UpdatedAt   string `json:"updated_at"`
	UserID      string `json:"user_id"`
	CourseCount int    `json:"course_count"`
}

func NewPlannerService(queries *db.Queries, _ *zap.Logger) *PlannerService {
	return &PlannerService{db: queries}
}

func (ps *PlannerService) Create(ctx context.Context, user *db.User, info *common.PlanInfo) (string, error) {
	id, err := ps.db.CreatePlan(ctx, db.CreatePlanParams{
		Title:  info.Title,
		Term:   info.Term,
		UserID: user.ID,
	})

	if err != nil {
		return "", err
	}

	return id.String(), nil
}

func (ps *PlannerService) GetAll(ctx context.Context, user *db.User) ([]*Plan, error) {
	res, err := ps.db.GetPlans(ctx, user.ID)

	if err != nil {
		return nil, err
	}

	result := make([]*Plan, 0, len(res))

	for _, plan := range res {
		result = append(result, &Plan{
			ID:          plan.ID.String(),
			Title:       plan.Title,
			Term:        plan.Term,
			CreatedAt:   common.TimestamptzToString(plan.CreatedAt),
			UpdatedAt:   common.TimestamptzToString(plan.UpdatedAt),
			UserID:      plan.UserID.String(),
			CourseCount: int(plan.CourseCount),
		})
	}

	return result, nil
}
