package service

import (
	"context"
	"fmt"

	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/db"
)

type OnboardingService struct {
	log *zap.Logger
	db  *db.Queries
}

func NewOnboardingService(queries *db.Queries, log *zap.Logger) *OnboardingService {
	return &OnboardingService{log: log, db: queries}
}

func (os *OnboardingService) Handle(ctx context.Context, user *db.User, onboardingInfo common.OnboardingInfo) error {
	os.log.Debug("onboarding submitted",
		zap.String("program", onboardingInfo.Program),
		zap.Int("year", onboardingInfo.Year),
	)

	completed, err := os.db.HasCompletedOnboarding(ctx, user.ID)
	if err != nil {
		return err
	}

	if completed {
		return fmt.Errorf("onboarding is already completed")
	}

	_, err = os.db.CreateUserDetails(ctx, db.CreateUserDetailsParams{
		UserID:           user.ID,
		Program:          onboardingInfo.Program,
		Year:             int16(onboardingInfo.Year),
		CompletedCourses: onboardingInfo.CompletedCourses,
		AvoidedCourses:   onboardingInfo.AvoidedCourses,
		JobInfo:          onboardingInfo.JobInfo,
		HomeAddress:      onboardingInfo.HomeAddress,
		FuturePlans:      onboardingInfo.FuturePlans,
		ProfessorQuality: int16(onboardingInfo.ProfessorQuality),
		TeachingStyle:    int16(onboardingInfo.TeachingStyle),
	})

	if err != nil {
		return err
	}

	return nil
}
