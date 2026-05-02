package middleware

import (
	"context"
	"net/http"

	"go.uber.org/zap"
)

type loggerCtxKey struct{}

// AttachLogger stores the application logger on the request context. Register
// early in the middleware chain so handlers can use Logger(r).
func AttachLogger(log *zap.Logger) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := context.WithValue(r.Context(), loggerCtxKey{}, log)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// Logger returns the logger set by AttachLogger, or a no-op logger (e.g. in tests).
func Logger(r *http.Request) *zap.Logger {
	log, _ := r.Context().Value(loggerCtxKey{}).(*zap.Logger)
	if log == nil {
		return zap.NewNop()
	}
	return log
}
