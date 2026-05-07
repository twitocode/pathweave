package handlers

import (
	"net/http"

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
		err := ps.GetProgramRequirements(r.Context(), body.Name)
    if err != nil {
      log.Error("error with finding program requirements", zap.Error(err))
      common.WriteError(w, http.StatusInternalServerError,"An error occured")
    }
	}
}
