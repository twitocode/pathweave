package middleware

import (
	"net/http"
	"strings"

	"github.com/twitocode/pathweave/go-api/internal/common"
)

func RequireInternalToken(token string) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			if token == "" {
				common.WriteError(w, http.StatusUnauthorized, "internal service token is not configured")
				return
			}

			authHeader := strings.TrimSpace(r.Header.Get("Authorization"))
			if authHeader != "Bearer "+token {
				common.WriteError(w, http.StatusUnauthorized, "invalid internal service token")
				return
			}

			next.ServeHTTP(w, r)
		})
	}
}
