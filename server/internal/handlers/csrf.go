package handlers

import (
	"net/http"
	"time"

	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
)

func HandleCSRFToken(cfg *config.Config) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		token, err := middleware.GenerateCSRFToken(cfg.SecretKey, time.Now())
		if err != nil {
			middleware.Logger(r).Warn("csrf token generation failed", zap.Error(err))
			common.WriteError(w, http.StatusServiceUnavailable, err.Error())
			return
		}
		common.WriteJSON(w, http.StatusOK, map[string]string{"csrfToken": token})
	}
}
