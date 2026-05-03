package service

import (
	"context"
	"fmt"
	"time"

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

	bedtime, wakeUpTime := parseTime(onboardingInfo)

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
		Bedtime:          bedtime,
    WakeUpTime: wakeUpTime,
	})

	if err != nil {
		return err
	}

	return nil
}

func parseTime(onboardingInfo common.OnboardingInfo) (pgtype.Time, pgtype.Time) {
	parsedBedtime, err := time.Parse("15:04:05", onboardingInfo.Bedtime)
	if err != nil {
		panic(err)
	}

	parsedWakeUpTime, err := time.Parse("15:04:05", onboardingInfo.WakeUpTime)

	if err != nil {
		panic(err)
	}

	bedtimeMicroseconds := int64(parsedBedtime.Hour()*3600+parsedBedtime.Minute()*60+parsedBedtime.Second()) * 1000000
	wakeUpTimeMicroseconds := int64(parsedWakeUpTime.Hour()*3600+parsedWakeUpTime.Minute()*60+parsedWakeUpTime.Second()) * 1000000

	bedtime := pgtype.Time{
		Microseconds: bedtimeMicroseconds,
		Valid:        true,
	}
	wakeUpTime := pgtype.Time{
		Microseconds: wakeUpTimeMicroseconds,
		Valid:        true,
	}
	return bedtime, wakeUpTime
}
