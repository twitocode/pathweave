package handlers

import (
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/google/uuid"
	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
	"github.com/twitocode/pathweave/go-api/internal/service/scraping"
	"go.uber.org/zap"
)

func HandleCreateScrapeRun(s *scraping.ScrapeIngestService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var body scraping.CreateScrapeRunRequest
		if err := common.DecodeJSON(r, &body); err != nil {
			common.WriteError(w, http.StatusBadRequest, "invalid json in request")
			return
		}

		run, err := s.CreateRun(r.Context(), body)
		if err != nil {
			middleware.Logger(r).Error("could not create scrape run", zap.Error(err))
			common.WriteError(w, http.StatusBadRequest, err.Error())
			return
		}

		common.WriteJSON(w, http.StatusCreated, run)
	}
}

func HandleGetScrapeRun(s *scraping.ScrapeIngestService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		runID, ok := scrapeRunIDParam(w, r)
		if !ok {
			return
		}

		run, err := s.GetRun(r.Context(), runID)
		if err != nil {
			middleware.Logger(r).Error("could not get scrape run", zap.String("run_id", runID.String()), zap.Error(err))
			common.WriteError(w, http.StatusNotFound, "scrape run not found")
			return
		}

		common.WriteJSON(w, http.StatusOK, run)
	}
}

func HandleStageScrapeArtifacts(s *scraping.ScrapeIngestService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		runID, ok := scrapeRunIDParam(w, r)
		if !ok {
			return
		}

		var body scraping.StageScrapeArtifactsRequest
		if err := common.DecodeJSON(r, &body); err != nil {
			common.WriteError(w, http.StatusBadRequest, "invalid json in request")
			return
		}

		result, err := s.StageArtifacts(r.Context(), runID, body)
		if err != nil {
			middleware.Logger(r).Error("could not stage scrape artifacts", zap.String("run_id", runID.String()), zap.Error(err))
			common.WriteError(w, http.StatusBadRequest, err.Error())
			return
		}

		common.WriteJSON(w, http.StatusOK, result)
	}
}

func HandlePromoteScrapeRun(s *scraping.ScrapeIngestService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		runID, ok := scrapeRunIDParam(w, r)
		if !ok {
			return
		}

		result, err := s.PromoteRun(r.Context(), runID)
		if err != nil {
			middleware.Logger(r).Error("could not promote scrape run", zap.String("run_id", runID.String()), zap.Error(err))
			common.WriteError(w, http.StatusInternalServerError, err.Error())
			return
		}

		common.WriteJSON(w, http.StatusOK, result)
	}
}

func scrapeRunIDParam(w http.ResponseWriter, r *http.Request) (uuid.UUID, bool) {
	value := chi.URLParam(r, "run_id")
	runID, err := uuid.Parse(value)
	if err != nil {
		common.WriteError(w, http.StatusBadRequest, "invalid scrape run id")
		return uuid.Nil, false
	}
	return runID, true
}
