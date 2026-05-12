package service

import (
	"context"
	"fmt"

	"go.uber.org/zap"

	"github.com/jackc/pgx/v5/pgtype"
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

	bedtime := common.StringToTime(onboardingInfo.Bedtime)
	wakeUpTime := common.StringToTime(onboardingInfo.WakeUpTime)

	programID, err := os.db.GetProgramIDByName(ctx, onboardingInfo.Program)
	if err != nil {
		return fmt.Errorf("failed to find program %q: %w", onboardingInfo.Program, err)
	}

	_, err = os.db.CreateUserDetails(ctx, db.CreateUserDetailsParams{
		UserID: user.ID,
		ProgramID: pgtype.Int8{
			Int64: programID,
			Valid: true,
		},
		Year:             int16(onboardingInfo.Year),
		JobInfo:          onboardingInfo.JobInfo,
		HomeAddress:      onboardingInfo.HomeAddress,
		FuturePlans:      onboardingInfo.FuturePlans,
		ProfessorQuality: int16(onboardingInfo.ProfessorQuality),
		TeachingStyle:    int16(onboardingInfo.TeachingStyle),
		Bedtime:          bedtime,
		WakeUpTime:       wakeUpTime,
	})

	if err != nil {
		return err
	}

	for _, completedCourseCode := range onboardingInfo.CompletedCourses {
		courseID, err := os.db.GetCourseIDByCode(ctx, completedCourseCode)
		if err != nil {
			return fmt.Errorf("failed to find completed course %q: %w", completedCourseCode, err)
		}

		if err := os.db.AddUserCompletedCourse(ctx, db.AddUserCompletedCourseParams{
			UserID:   user.ID,
			CourseID: courseID,
		}); err != nil {
			return err
		}
	}

	for _, avoidedCourseCode := range onboardingInfo.AvoidedCourses {
		courseID, err := os.db.GetCourseIDByCode(ctx, avoidedCourseCode)
		if err != nil {
			return fmt.Errorf("failed to find avoided course %q: %w", avoidedCourseCode, err)
		}

		if err := os.db.AddUserAvoidedCourse(ctx, db.AddUserAvoidedCourseParams{
			UserID:   user.ID,
			CourseID: courseID,
		}); err != nil {
			return err
		}
	}

	return nil
}
