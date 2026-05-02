package handlers

import (
	"net/http"

	"github.com/go-playground/validator/v10"
	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
	"github.com/twitocode/pathweave/go-api/internal/service"
)

var validate = validator.New()

func HandleOnboarding(os *service.OnboardingService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		var body common.OnboardingInfo
		if err := common.DecodeJSON(r, &body); err != nil {
			log.Warn("onboarding decode failed", zap.Error(err))
			common.WriteError(w, http.StatusBadRequest, "invalid onboarding info")
			return
		}

		if err := validate.Struct(body); err != nil {
			log.Warn("onboarding validation failed", zap.Error(err))
			common.WriteError(w, http.StatusBadRequest, "validation failed")
			return
		}

		user, _ := middleware.UserFromContext(r.Context())

		if err := os.Handle(r.Context(), user, body); err != nil {
			log.Warn("onboarding creation failed", zap.Error(err))
			common.WriteError(w, http.StatusInternalServerError, "onboarding failed")
		}

		w.WriteHeader(http.StatusNoContent)
	}
}
