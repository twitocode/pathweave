package config

import (
	"os"
	"strings"

	"github.com/joho/godotenv"
	"go.uber.org/zap"
	"go.uber.org/zap/buffer"
	"go.uber.org/zap/zapcore"
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
	core := zapcore.NewCore(
		newDevelopmentEncoder(),
		zapcore.Lock(os.Stderr),
		zap.NewAtomicLevelAt(zap.DebugLevel),
	)
	return zap.New(core, zap.AddCaller(), zap.AddStacktrace(zapcore.ErrorLevel), zap.Development())
}

var logBufferPool = buffer.NewPool()

type levelFirstConsoleEncoder struct {
	zapcore.Encoder
}

func newDevelopmentEncoder() zapcore.Encoder {
	cfg := zap.NewDevelopmentEncoderConfig()
	cfg.TimeKey = ""
	cfg.LevelKey = ""
	cfg.NameKey = ""
	cfg.ConsoleSeparator = " "

	return &levelFirstConsoleEncoder{
		Encoder: zapcore.NewConsoleEncoder(cfg),
	}
}

func (e *levelFirstConsoleEncoder) Clone() zapcore.Encoder {
	return &levelFirstConsoleEncoder{Encoder: e.Encoder.Clone()}
}

func (e *levelFirstConsoleEncoder) EncodeEntry(entry zapcore.Entry, fields []zapcore.Field) (*buffer.Buffer, error) {
	rest, err := e.Encoder.EncodeEntry(entry, fields)
	if err != nil {
		return nil, err
	}
	defer rest.Free()

	buf := logBufferPool.Get()
	buf.AppendString(coloredBracketedLevel(entry.Level))
	buf.AppendByte(' ')
	buf.AppendString(entry.Time.Format("15:04:05"))

	restText := strings.TrimSuffix(rest.String(), "\n")
	if restText != "" {
		buf.AppendByte(' ')
		buf.AppendString(restText)
	}
	buf.AppendByte('\n')

	return buf, nil
}

func coloredBracketedLevel(level zapcore.Level) string {
	color := "37"
	switch level {
	case zapcore.DebugLevel:
		color = "35"
	case zapcore.InfoLevel:
		color = "34"
	case zapcore.WarnLevel:
		color = "33"
	case zapcore.ErrorLevel, zapcore.DPanicLevel, zapcore.PanicLevel, zapcore.FatalLevel:
		color = "31"
	}
	return "\x1b[" + color + "m[" + level.CapitalString() + "]\x1b[0m"
}
