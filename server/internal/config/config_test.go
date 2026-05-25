package config

import (
	"os"
	"strings"
	"testing"
	"time"

	"github.com/stretchr/testify/require"
	"go.uber.org/zap/zapcore"
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

func TestDevelopmentEncoderOrdersTypeBeforeTime(t *testing.T) {
	encoder := newDevelopmentEncoder()
	entry := zapcore.Entry{
		Level:   zapcore.InfoLevel,
		Time:    time.Date(2026, 5, 25, 15, 4, 5, 0, time.FixedZone("EDT", -4*60*60)),
		Caller:  zapcore.EntryCaller{Defined: true, File: "internal/config/config.go", Line: 70},
		Message: "starting server",
	}

	buf, err := encoder.EncodeEntry(entry, nil)
	require.NoError(t, err)
	defer buf.Free()

	line := strings.TrimSuffix(buf.String(), "\n")
	require.True(t, strings.HasPrefix(line, "\x1b[34m[INFO]\x1b[0m 15:04:05 "))
	require.Contains(t, line, "config/config.go:70 starting server")
	require.NotContains(t, line, "port")
}
