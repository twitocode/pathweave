package handlers

import (
	"errors"
	"net/http"

	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
	"github.com/twitocode/pathweave/go-api/internal/service"
)

func HandleLogin(svc *service.AuthService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		if r.URL.Query().Get("code") != "" || r.URL.Query().Get("error") != "" {
			log.Debug("auth login redirecting to callback",
				zap.String("path", r.URL.Path))
			http.Redirect(w, r, "/auth/callback?"+r.URL.RawQuery, http.StatusFound)
			return
		}

		url, err := svc.LoginURL()
		if err != nil {
			log.Warn("auth login URL failed", zap.Error(err))
			common.WriteError(w, http.StatusBadGateway, "Failed to generate login URL")
			return
		}
		http.Redirect(w, r, url, http.StatusFound)
	}
}

func HandleCallback(cfg *config.Config, svc *service.AuthService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		if providerErr := r.URL.Query().Get("error"); providerErr != "" {
			log.Warn("auth callback provider error", zap.String("error", providerErr))
			http.Redirect(w, r, authErrorRedirect(cfg.FrontendAppURL, providerErr), http.StatusFound)
			return
		}

		code := r.URL.Query().Get("code")
		if code == "" {
			log.Warn("auth callback missing code")
			http.Redirect(w, r, authErrorRedirect(cfg.FrontendAppURL, "missing_code"), http.StatusFound)
			return
		}

		sealedSession, _, err := svc.AuthenticateWithCode(r.Context(), code)
		if err != nil {
			log.Warn("auth callback exchange failed", zap.Error(err))
			http.Redirect(w, r, authErrorRedirect(cfg.FrontendAppURL, "auth_failed"), http.StatusFound)
			return
		}

		http.SetCookie(w, middleware.SessionCookie(sealedSession, r))
		http.Redirect(w, r, cfg.FrontendAppURL, http.StatusFound)
	}
}

func HandleMe() http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		user, ok := middleware.UserFromContext(r.Context())
		if !ok {
			log.Warn("auth me unauthorized")
			common.WriteError(w, http.StatusUnauthorized, "unauthorized")
			return
		}

		common.WriteJSON(w, http.StatusOK, map[string]any{
			"id":    user.ID,
			"email": user.Email,
		})
	}
}

func HandleLogout(cfg *config.Config, svc *service.AuthService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		cookie, _ := r.Cookie(service.SessionCookieName)
		sealed := ""
		if cookie != nil {
			sealed = cookie.Value
		}

		logoutURL, err := svc.GetLogoutURL(r.Context(), sealed)
		if err != nil && !errors.Is(err, service.ErrNoSession) {
			log.Warn("auth logout URL failed", zap.Error(err))
			common.WriteError(w, http.StatusBadGateway, err.Error())
			return
		}

		http.SetCookie(w, &http.Cookie{
			Name:     service.SessionCookieName,
			Value:    "",
			HttpOnly: true,
			Secure:   r.TLS != nil,
			SameSite: http.SameSiteLaxMode,
			Path:     "/",
			MaxAge:   -1,
		})
		http.Redirect(w, r, logoutURL, http.StatusFound)
	}
}
