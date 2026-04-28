package api

import (
	"net/http"
	"net/url"
	"time"

	"github.com/go-chi/render"

	"github.com/twitocode/pathweave/go-api/internal/auth"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
)

type AuthHandlers struct {
	cfg  config.Config
	auth *auth.Service
}

func NewAuthHandlers(cfg config.Config, authService *auth.Service) *AuthHandlers {
	return &AuthHandlers{cfg: cfg, auth: authService}
}

func (h *AuthHandlers) Login(w http.ResponseWriter, r *http.Request) {
	// Guard against callback misconfiguration pointing back to a login route.
	if r.URL.Query().Get("code") != "" || r.URL.Query().Get("error") != "" {
		h.Callback(w, r)
		return
	}

	url, err := h.auth.LoginURL()
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	http.Redirect(w, r, url, http.StatusFound)
}

func (h *AuthHandlers) Callback(w http.ResponseWriter, r *http.Request) {
	if providerErr := r.URL.Query().Get("error"); providerErr != "" {
		http.Redirect(w, r, h.authErrorRedirect(providerErr), http.StatusFound)
		return
	}

	code := r.URL.Query().Get("code")
	if code == "" {
		http.Redirect(w, r, h.authErrorRedirect("missing_code"), http.StatusFound)
		return
	}
	sealedSession, _, err := h.auth.AuthenticateWithCode(r.Context(), code)
	if err != nil {
		http.Redirect(w, r, h.authErrorRedirect("auth_failed"), http.StatusFound)
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name:     auth.SessionCookieName,
		Value:    sealedSession,
		HttpOnly: true,
		Secure:   r.TLS != nil,
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
	})
	http.Redirect(w, r, h.cfg.FrontendAppURL, http.StatusFound)
}

func (h *AuthHandlers) authErrorRedirect(reason string) string {
	base, err := url.Parse(h.cfg.FrontendAppURL)
	if err != nil {
		return h.cfg.FrontendAppURL
	}

	query := base.Query()
	query.Set("auth_error", reason)
	base.RawQuery = query.Encode()
	return base.String()
}

func (h *AuthHandlers) Me(w http.ResponseWriter, r *http.Request) {
	cookie, _ := r.Cookie(auth.SessionCookieName)
	if cookie == nil {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	workosUser, refreshedCookie, err := h.auth.AuthenticateSession(r.Context(), cookie.Value)
	if err != nil {
		http.Error(w, "unauthorized", http.StatusUnauthorized)
		return
	}
	if refreshedCookie != "" {
		http.SetCookie(w, &http.Cookie{
			Name:     auth.SessionCookieName,
			Value:    refreshedCookie,
			HttpOnly: true,
			Secure:   r.TLS != nil,
			SameSite: http.SameSiteLaxMode,
			Path:     "/",
		})
	}
	render.JSON(w, r, map[string]any{
		"id":    workosUser.ID,
		"email": workosUser.Email,
	})
}

func (h *AuthHandlers) CSRFToken(w http.ResponseWriter, r *http.Request) {
	token, err := middleware.GenerateCSRFToken(h.cfg.SecretKey, time.Now())
	if err != nil {
		http.Error(w, err.Error(), http.StatusServiceUnavailable)
		return
	}
	render.JSON(w, r, map[string]string{"csrfToken": token})
}

func (h *AuthHandlers) Logout(w http.ResponseWriter, r *http.Request) {
	rawToken := r.Header.Get("X-CSRF-Token")
	if rawToken == "" {
		http.Error(w, "csrf token missing", http.StatusForbidden)
		return
	}
	if err := middleware.ValidateCSRFToken(h.cfg.SecretKey, rawToken, time.Now()); err != nil {
		http.Error(w, "invalid csrf token", http.StatusForbidden)
		return
	}

	cookie, _ := r.Cookie(auth.SessionCookieName)
	sealed := ""
	if cookie != nil {
		sealed = cookie.Value
	}
	logoutURL, err := h.auth.GetLogoutURL(r.Context(), sealed)
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	http.SetCookie(w, &http.Cookie{
		Name:     auth.SessionCookieName,
		Value:    "",
		HttpOnly: true,
		Secure:   r.TLS != nil,
		SameSite: http.SameSiteLaxMode,
		Path:     "/",
		MaxAge:   -1,
	})
	http.Redirect(w, r, logoutURL, http.StatusFound)
}
