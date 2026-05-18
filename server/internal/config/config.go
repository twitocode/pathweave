package config

import (
	"strings"

	"github.com/joho/godotenv"
	"go.uber.org/zap"
)

type Config struct {
	Host                 string
	Port                 string
	AppEnv               string
	DatabaseURL          string
	FrontendAppURL       string
	WorkOSAPIKey         string
	WorkOSClientID       string
	WorkOSCookiePassword string
	WorkOSRedirectURI    string
	SecretKey            string
	InternalServiceToken string
	PythonAIBaseURL      string
	AllowedOrigins       []string
	OpenRouterAPIKey     string
	DevBypassAuth        bool
	DevBypassAuthEmail   string
}

func New(getenv func(string) string) *Config {
	_ = godotenv.Load(".env")

	port := getenv("PORT")
	if port == "" {
		port = "8000"
	}

	allowedOrigins := []string{getenv("FRONTEND_APP_URL")}
	if allowedOrigins[0] == "" {
		allowedOrigins = []string{"http://localhost:3000"}
	}

	devBypassAuth := strings.ToLower(strings.TrimSpace(getenv("DEV_BYPASS_AUTH"))) == "true"
	devBypassAuthEmail := getenv("DEV_BYPASS_AUTH_EMAIL")
	if devBypassAuthEmail == "" {
		devBypassAuthEmail = "dev@example.com"
	}

	return &Config{
		Host:                 getenv("HOST"),
		Port:                 port,
		AppEnv:               getenv("APP_ENV"),
		DatabaseURL:          getenv("DATABASE_URL"),
		FrontendAppURL:       getenv("FRONTEND_APP_URL"),
		WorkOSAPIKey:         getenv("WORKOS_API_KEY"),
		WorkOSClientID:       getenv("WORKOS_CLIENT_ID"),
		WorkOSCookiePassword: getenv("WORKOS_COOKIE_PASSWORD"),
		WorkOSRedirectURI:    getenv("WORKOS_REDIRECT_URI"),
		SecretKey:            getenv("SECRET_KEY"),
		InternalServiceToken: getenv("INTERNAL_SERVICE_TOKEN"),
		OpenRouterAPIKey:     getenv("OPENROUTER_API_KEY"),
		PythonAIBaseURL:      strings.TrimRight(getenv("PYTHON_AI_BASE_URL"), "/"),
		AllowedOrigins:       allowedOrigins,
		DevBypassAuth:        devBypassAuth,
		DevBypassAuthEmail:   devBypassAuthEmail,
	}
}

// NewLogger builds the application logger. Call once at startup and inject the
// returned value into the HTTP stack and services (do not store it on Config).
func NewLogger(getenv func(string) string) *zap.Logger {
	if getenv("APP_ENV") == "production" {
		return zap.Must(zap.NewProduction())
	}
	return zap.Must(zap.NewDevelopment())
}
