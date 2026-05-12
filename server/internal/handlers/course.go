package handlers

import (
	"fmt"
	"net/http"

	"github.com/go-chi/chi/v5"
	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/middleware"
	"github.com/twitocode/pathweave/go-api/internal/service"
	"go.uber.org/zap"
)

func HandleGetCourseByCode(cs *service.CourseService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		code := chi.URLParam(r, "code")
		log := middleware.Logger(r)

		if code == "" {
			common.WriteError(w, http.StatusBadRequest, "course code not provided")
			return
		}

		course, err := cs.GetCourseInfo(r.Context(), code)
		if err != nil {
			log.Error("error getting course info", zap.Error(err))
		}

    if course == nil {
      common.WriteError(w, http.StatusNotFound, fmt.Sprintf("course %s not found", code))
      return
    }
		common.WriteJSON(w, http.StatusOK, course)
	}
}
