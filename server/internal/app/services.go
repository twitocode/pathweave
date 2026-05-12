package app

import (
	"github.com/jackc/pgx/v5/pgxpool"
	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"github.com/twitocode/pathweave/go-api/internal/service"
)

type Services struct {
	Auth *service.AuthService
	User *service.UserService
  Onboarding *service.OnboardingService
  Program *service.ProgramService
  Course *service.CourseService
}

func NewServices(cfg *config.Config, pool *pgxpool.Pool, log *zap.Logger) *Services {
	queries := db.New(pool)

	return &Services{
		Auth:       service.NewAuthService(cfg, queries, log),
		User:       service.NewUserService(queries, log),
		Onboarding: service.NewOnboardingService(queries, log),
    Course: service.NewCourseService(queries, log),
    Program: service.NewProgramService(queries, log),
	}
}
