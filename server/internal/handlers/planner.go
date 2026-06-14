package handlers

import (
	"fmt"
	"net/http"
	"slices"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
	"github.com/twitocode/pathweave/go-api/internal/service"
	"go.uber.org/zap"
)

func HandleCreatePlan(ps *service.PlannerService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user, _ := middleware.UserFromContext(r.Context())
		log := middleware.Logger(r)

		var body common.PlanInfo
		if err := common.DecodeJSON(r, &body); err != nil {
			common.WriteError(w, http.StatusBadRequest, "invalid plan info provided")
			return
		}

    if (!slices.Contains(common.ValidTerms, body.Term)) {
      common.WriteError(w, http.StatusBadRequest, "invalid term provided")
			return
    }

		id, err := ps.Create(r.Context(), user, &body)

		if err != nil {
			common.WriteError(w, http.StatusInternalServerError, "could not create plan")
			log.Error(fmt.Sprintf("plan for user %s could not be created", user.ID), zap.Error(err))
			return
		}

		common.WriteJSON(w, http.StatusCreated, map[string]string{
			"plan_id": id,
		})
	}
}

func HandleGetAllPlans(ps *service.PlannerService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		user, _ := middleware.UserFromContext(r.Context())
		log := middleware.Logger(r)

    plans, err := ps.GetAll(r.Context(),user)
		if err != nil {
			common.WriteError(w, http.StatusInternalServerError, "could not create plan")
			log.Error(fmt.Sprintf("plan for user %s could not be created", user.ID), zap.Error(err))
			return
		}

		common.WriteJSON(w, http.StatusOK, plans)
	}
}
