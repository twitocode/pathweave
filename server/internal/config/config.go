package config

import (
	"errors"
	"os"
	"strings"

	"github.com/joho/godotenv"
)

type Config struct {
	Port                 string
	DatabaseURL          string
	FrontendAppURL       string
	WorkOSAPIKey         string
	WorkOSClientID       string
	WorkOSCookiePassword string
	WorkOSRedirectURI    string
	SecretKey            string
	InternalServiceToken string
	PythonAIBaseURL      string
}

func Load() (Config, error) {
	_ = godotenv.Load(".env")

	cfg := Config{
		Port:                 getEnv("PORT", "8000"),
		DatabaseURL:          getEnv("DATABASE_URL", ""),
		FrontendAppURL:       getEnv("FRONTEND_APP_URL", "http://localhost:3000"),
		WorkOSAPIKey:         getEnv("WORKOS_API_KEY", ""),
		WorkOSClientID:       getEnv("WORKOS_CLIENT_ID", ""),
		WorkOSCookiePassword: getEnv("WORKOS_COOKIE_PASSWORD", ""),
		WorkOSRedirectURI:    getEnv("WORKOS_REDIRECT_URI", "http://localhost:8000/auth/callback"),
		SecretKey:            getEnv("SECRET_KEY", ""),
		InternalServiceToken: getEnv("INTERNAL_SERVICE_TOKEN", ""),
		PythonAIBaseURL:      strings.TrimRight(getEnv("PYTHON_AI_BASE_URL", "http://localhost:8000"), "/"),
	}

	if cfg.DatabaseURL == "" {
		return Config{}, errors.New("DATABASE_URL is required")
	}
	if cfg.WorkOSAPIKey == "" || cfg.WorkOSClientID == "" || cfg.WorkOSCookiePassword == "" {
		return Config{}, errors.New("WORKOS_API_KEY, WORKOS_CLIENT_ID and WORKOS_COOKIE_PASSWORD are required")
	}
	if cfg.InternalServiceToken == "" {
		return Config{}, errors.New("INTERNAL_SERVICE_TOKEN is required")
	}
	return cfg, nil
}

func getEnv(key, fallback string) string {
	value := os.Getenv(key)
	if value == "" {
		return fallback
	}
	return value
}
