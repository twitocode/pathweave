package middleware

import (
	"context"
	"net/http"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"github.com/twitocode/pathweave/go-api/internal/service"
)

type authUserContextKey struct{}

// RequireAuth rejects requests without a valid session and attaches *db.User to request context.
func RequireAuth(cfg *config.Config, svc *service.AuthService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			// Dev-only auth bypass:
			if cfg.DevBypassAuth && cfg.AppEnv != "production" {
				user, err := svc.GetOrCreateUserByEmail(r.Context(), cfg.DevBypassAuthEmail)
				if err != nil {
					common.WriteError(w, http.StatusInternalServerError, "dev auth bypass failed")
					return
				}

				ctx := context.WithValue(r.Context(), authUserContextKey{}, &user)
				next.ServeHTTP(w, r.WithContext(ctx))
				return
			}

			cookie, err := r.Cookie(service.SessionCookieName)
			if err != nil || cookie.Value == "" {
				common.WriteError(w, http.StatusUnauthorized, "unauthorized")
				return
			}

			user, refreshedCookie, err := svc.AuthenticateSession(r.Context(), cookie.Value)
			if err != nil {
				common.WriteError(w, http.StatusUnauthorized, "unauthorized")
				return
			}

			if refreshedCookie != "" {
				http.SetCookie(w, SessionCookie(refreshedCookie, r))
			}

			ctx := context.WithValue(r.Context(), authUserContextKey{}, user)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// OptionalAuth attaches *db.User to context when a valid session cookie is present; otherwise continues without user.
func OptionalAuth(svc *service.AuthService) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			ctx := r.Context()
			cookie, err := r.Cookie(service.SessionCookieName)
			if err == nil && cookie.Value != "" {
				user, refreshedCookie, err := svc.AuthenticateSession(ctx, cookie.Value)
				if err == nil && user != nil {
					if refreshedCookie != "" {
						http.SetCookie(w, SessionCookie(refreshedCookie, r))
					}
					ctx = context.WithValue(ctx, authUserContextKey{}, user)
				}
			}
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// UserFromContext returns the authenticated user set by RequireAuth or OptionalAuth.
func UserFromContext(ctx context.Context) (*db.User, bool) {
	u, ok := ctx.Value(authUserContextKey{}).(*db.User)
	return u, ok && u != nil
}

// SessionCookie builds the standard auth session cookie (TLS-aware Secure flag).
func SessionCookie(value string, r *http.Request) *http.Cookie {
	return &http.Cookie{
		Name:     service.SessionCookieName,
		Value:    value,
		HttpOnly: true,
		Secure:   r.TLS != nil,
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
	}
}

// PKCECookie builds the PKCE verifier cookie.
func PKCECookie(value string, r *http.Request) *http.Cookie {
	return &http.Cookie{
		Name:     service.PKCECookieName,
		Value:    value,
		HttpOnly: true,
		Secure:   r.TLS != nil,
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
		MaxAge:   300, // 5 minutes
	}
}
