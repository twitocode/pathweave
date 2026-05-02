package config

import (
	"os"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestNewConfig(t *testing.T) {
	t.Setenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/pathweave")
	t.Setenv("WORKOS_API_KEY", "sk_test")
	t.Setenv("WORKOS_CLIENT_ID", "client_test")
	t.Setenv("WORKOS_COOKIE_PASSWORD", "cookie_password")
	t.Setenv("INTERNAL_SERVICE_TOKEN", "token_123")
	t.Setenv("DEV_BYPASS_AUTH", "false")
	t.Setenv("APP_ENV", "development")

	cfg := New(os.Getenv)
	require.Equal(t, "postgresql://postgres:postgres@localhost:5432/pathweave", cfg.DatabaseURL)
	require.Equal(t, "token_123", cfg.InternalServiceToken)

	log := NewLogger(os.Getenv)
	require.NotNil(t, log)
}
