package tests

import (
	"context"
	"os"
	"testing"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/stretchr/testify/require"
	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/db"
	"github.com/twitocode/pathweave/go-api/internal/service"
)

func TestGetOrCreateUserByEmail_Integration(t *testing.T) {
	databaseURL := os.Getenv("PGTEST_DATABASE_URL")
	if databaseURL == "" {
		t.Skip("set PGTEST_DATABASE_URL to run integration tests")
	}

	ctx := context.Background()
	pool, err := pgxpool.New(ctx, databaseURL)
	require.NoError(t, err)
	defer pool.Close()

	_, err = pool.Exec(ctx, `
		CREATE TABLE IF NOT EXISTS users (
			id BIGSERIAL PRIMARY KEY,
			email TEXT NOT NULL UNIQUE,
			created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
			updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
		)
	`)
	require.NoError(t, err)

	uniqueEmail := "integration_test_user@example.com"
	_, _ = pool.Exec(ctx, "DELETE FROM users WHERE email = $1", uniqueEmail)

	queries := db.New(pool)
	log := zap.NewNop()
	userSvc := service.NewUserService(queries, log)

	user, err := userSvc.GetOrCreateByEmail(ctx, uniqueEmail)
	require.NoError(t, err)
	require.Equal(t, uniqueEmail, user.Email)

	sameUser, err := userSvc.GetOrCreateByEmail(ctx, uniqueEmail)
	require.NoError(t, err)
	require.Equal(t, user.ID, sameUser.ID)
}
