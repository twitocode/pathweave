package api

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/cors"
)

func NewRouter(authHandlers *AuthHandlers, domainHandlers *DomainHandlers, aiHandlers *AIHandlers) http.Handler {
	r := chi.NewRouter()
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:3000"},
		AllowedMethods:   []string{"GET", "POST", "OPTIONS"},
		AllowedHeaders:   []string{"Accept", "Authorization", "Content-Type", "X-CSRF-Token"},
		AllowCredentials: true,
	}))

	r.Get("/health", domainHandlers.Health)
	r.Get("/", domainHandlers.Health)

	r.Get("/csrf-token", authHandlers.CSRFToken)
	r.Post("/logout", authHandlers.Logout)

	r.Route("/auth", func(r chi.Router) {
		r.Get("/login", authHandlers.Login)
		r.Get("/login/google", authHandlers.Login)
		r.Get("/callback", authHandlers.Callback)
		r.Get("/me", authHandlers.Me)
	})

	r.Route("/onboarding", func(r chi.Router) {

	})
	r.Route("/pathfinder", func(r chi.Router) {

	})

	r.Route("/ai", func(r chi.Router) {
		r.Get("/health", aiHandlers.HealthProxy)
	})

	return r
}
