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
		r.With(mw.RequireAuth(cfg, s.Auth)).Get("/me", handlers.HandleMe(s.Auth))
	})

	r.Route("/onboarding", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))
		r.Post("/", handlers.HandleOnboarding(s.Onboarding))
	})

	r.Route("/programs", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))

		r.Get("/", handlers.HandleGetProgramRequirements(s.Program))
		r.Get("/requirements/codes", handlers.HandleGetUserProgramRequirementCodes(s.Program))
		r.Get("/requirements/codes/{term}", handlers.HandleGetUserProgramRequirementCodesAvailableInTerm(s.Program))
	})

	r.Route("/user", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))
		r.Get("/program", handlers.HandleGetUserProgramName(s.Program))
	})

	r.Route("/courses", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))

		r.Get("/{code}", handlers.HandleGetCourseByCode(s.Course))
		r.Get("/{course_id}/schedules", handlers.HandleGetSchedulesForCourse(s.Course))
		r.Get("/{course_id}/sections", handlers.HandleGetCourseSectionsByTerm(s.Course))
		r.Post("/embeddings", handlers.HandleCreateAllCourseEmbeddings(s.Course))
		r.Get("/search", handlers.HandleVectorSearchCourse(s.Course))
	})

	r.Route("/plan", func(r chi.Router) {
		r.Use(mw.RequireAuth(cfg, s.Auth))

		r.Post("/", handlers.HandleCreatePlan(s.Planner))
		r.Get("/", handlers.HandleGetAllPlans(s.Planner))
	})

	r.Route("/internal", func(r chi.Router) {
		r.Use(mw.RequireInternalToken(cfg.InternalServiceToken))

		r.Post("/scrape-runs", handlers.HandleCreateScrapeRun(s.ScrapeIngest))
		r.Get("/scrape-runs/{run_id}", handlers.HandleGetScrapeRun(s.ScrapeIngest))
		r.Post("/scrape-runs/{run_id}/artifacts", handlers.HandleStageScrapeArtifacts(s.ScrapeIngest))
		r.Post("/scrape-runs/{run_id}/promote", handlers.HandlePromoteScrapeRun(s.ScrapeIngest))
	})

	r.With(mw.RequireCSRF(cfg.SecretKey)).Post("/logout", handlers.HandleLogout(cfg, s.Auth))
}
