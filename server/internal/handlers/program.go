package handlers

import (
	"net/http"
	"slices"

	"github.com/go-chi/chi/v5"
	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
	"github.com/twitocode/pathweave/go-api/internal/service"
	"go.uber.org/zap"
)

func HandleGetProgramRequirements(ps *service.ProgramService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)

		var body common.ProgramRequirementsInfo
		if err := common.DecodeJSON(r, &body); err != nil {
			log.Warn("onboarding decode failed", zap.Error(err))
			common.WriteError(w, http.StatusBadRequest, "invalid onboarding info")
			return
		}
		requirements, err := ps.GetProgramRequirements(r.Context(), body.Name)
		if err != nil {
			log.Error("error with finding program requirements", zap.Error(err))
			common.WriteError(w, http.StatusInternalServerError, "An error occurred")
			return
		}

		common.WriteJSON(w, http.StatusOK, requirements)
	}
}
func HandleGetUserProgramName(ps *service.ProgramService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		user, _ := middleware.UserFromContext(r.Context())

		requirements, err := ps.GetUserProgramName(r.Context(), user)
		if err != nil {
			log.Error("error with finding user's program name", zap.Error(err))
			common.WriteError(w, http.StatusInternalServerError, "An error occurred")
			return
		}

		common.WriteJSON(w, http.StatusOK, requirements)
	}
}

func HandleGetUserProgramRequirementCodes(ps *service.ProgramService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		user, _ := middleware.UserFromContext(r.Context())

		codes, err := ps.GetUserProgramRequirementCodes(r.Context(), user)
		if err != nil {
			log.Error("error getting user program requirement codes", zap.Error(err))
			common.WriteError(w, http.StatusInternalServerError, "An error occurred")
			return
		}

		common.WriteJSON(w, http.StatusOK, codes)
	}
}

func HandleGetUserProgramRequirementCodesAvailableInTerm(ps *service.ProgramService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		user, _ := middleware.UserFromContext(r.Context())
		term := chi.URLParam(r, "term")

		if term == "" {
			common.WriteError(w, http.StatusBadRequest, "term not provided")
			return
		}

		if !slices.Contains(common.ValidTerms, term) {
			common.WriteError(w, http.StatusBadRequest, "invalid term provided")
			return
		}

		termString := common.TermNumberToString[term]

		codes, err := ps.GetUserProgramRequirementCodesAvailableInTerm(r.Context(), user, termString)
		if err != nil {
			log.Error("error getting user program requirement codes for term", zap.Error(err))
			common.WriteError(w, http.StatusInternalServerError, "An error occurred")
			return
		}

		common.WriteJSON(w, http.StatusOK, codes)
	}
}
