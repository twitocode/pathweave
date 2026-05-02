package middleware

import (
	"net/http"
	"time"
)

func RequireCSRF(secretKey string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			rawToken := r.Header.Get("X-CSRF-Token")
			if rawToken == "" {
				http.Error(w, "csrf token missing", http.StatusForbidden)
				return
			}
			if err := ValidateCSRFToken(secretKey, rawToken, time.Now()); err != nil {
				http.Error(w, "invalid csrf token", http.StatusForbidden)
				return
			}
			next.ServeHTTP(w, r)
		})
	}
}
