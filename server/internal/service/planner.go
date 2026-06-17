package service

import (
	"context"
	"encoding/json"

	"github.com/google/uuid"
	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type PlannerService struct {
	db *db.Queries
}

type Plan struct {
	ID          string       `json:"id"`
	Title       string       `json:"title"`
	Term        string       `json:"term"`
	CreatedAt   string       `json:"created_at"`
	UpdatedAt   string       `json:"updated_at"`
	UserID      string       `json:"user_id,omitempty"`
	CourseCount int          `json:"course_count,omitempty"`
	Courses     []PlanCourse `json:"courses"`
}

type PlanCourse struct {
	ID            string        `json:"id"`
	CourseID      int64         `json:"course_id"`
	Code          string        `json:"code"`
	Name          string        `json:"name"`
	Description   string        `json:"description"`
	Restrictions  string        `json:"restrictions"`
	Prerequisites []string      `json:"prerequisites"`
	Units         int           `json:"units"`
	Types         []string      `json:"types"`
	Teachers      []TeacherInfo `json:"teachers"`
	Sections      []SectionInfo `json:"sections"`
}

type SectionInfo struct {
	ID         int           `json:"id"`
	Name       string        `json:"name"`
	Type       string        `json:"type"`
	Term       string        `json:"term"`
	Mode       string        `json:"mode"`
	IsInPerson bool          `json:"is_in_person"`
	Meetings   []MeetingInfo `json:"meetings"`
	Teachers   []TeacherInfo `json:"teachers"`
}

type MeetingInfo struct {
	ID        int     `json:"id"`
	Days      string  `json:"days"`
	StartTime *string `json:"start_time"`
	EndTime   *string `json:"end_time"`
	Building  string  `json:"building"`
	Room      string  `json:"room"`
}

type TeacherInfo struct {
	ID            int      `json:"id"`
	Name          string   `json:"name"`
	AvgRating     *float64 `json:"avg_rating"`
	AvgDifficulty *float64 `json:"avg_difficulty"`
	Department    string   `json:"department"`
	RmpID         string   `json:"rmp_id"`
	NumRatings    int      `json:"num_ratings"`
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
			Courses:     []PlanCourse{},
		})
	}

	return result, nil
}

func (ps *PlannerService) Get(ctx context.Context, user *db.User, id string) (*Plan, error) {
	planUUID, err := uuid.Parse(id)
	if err != nil {
		return nil, err
	}

	data, err := ps.db.GetPlanInfo(ctx, db.GetPlanInfoParams{
		PlanID: planUUID,
		UserID: user.ID,
	})

	if err != nil {
		return nil, err
	}

	var courses []PlanCourse
	if len(data.Courses) > 0 {
		if err := json.Unmarshal(data.Courses, &courses); err != nil {
			return nil, err
		}
	}

	info := &Plan{
		ID:        data.ID.String(),
		Title:     data.Title,
		Term:      data.Term,
		CreatedAt: data.CreatedAt.Time.String(),
		UpdatedAt: data.UpdatedAt.Time.String(),
		Courses:   courses,
	}

	return info, nil
}
