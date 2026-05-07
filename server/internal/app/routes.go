package app

import (
	"net/http"

	"github.com/go-chi/chi/v5"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/handlers"
	mw "github.com/twitocode/pathweave/go-api/internal/middleware"
)

func addRoutes(r *chi.Mux, cfg *config.Config, s *Services) {
	r.Get("/health", func(w http.ResponseWriter, _ *http.Request) {
		common.WriteJSON(w, http.StatusOK, map[string]string{"status": "ok"})
	})
	r.Get("/", func(w http.ResponseWriter, _ *http.Request) {
		common.WriteJSON(w, http.StatusOK, map[string]string{"status": "ok", "service": "go-api"})
	})

	r.Get("/csrf-token", handlers.HandleCSRFToken(cfg))

	r.Route("/auth", func(r chi.Router) {
		r.Get("/login", handlers.HandleLogin(s.Auth))
		r.Get("/login/google", handlers.HandleLogin(s.Auth))
		r.Get("/callback", handlers.HandleCallback(cfg, s.Auth))
		r.With(mw.RequireAuth(cfg, s.Auth)).Get("/me", handlers.HandleMe())
	})

	r.Route("/onboarding", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))
		r.Post("/", handlers.HandleOnboarding(s.Onboarding))
	})

	r.Route("/programs", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))

		r.Get("/", handlers.HandleGetProgramRequirements(s.Program))
	})

	r.With(mw.RequireCSRF(cfg.SecretKey)).Post("/logout", handlers.HandleLogout(cfg, s.Auth))
}
