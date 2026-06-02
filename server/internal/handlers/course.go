package handlers

import (
	"fmt"
	"net/http"
	"slices"
	"strconv"

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
func HandleGetSchedulesForCourse(cs *service.CourseService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "course_id")
		course_id, err := strconv.Atoi(id)
		if err != nil {
			common.WriteError(w, http.StatusBadRequest, "course id is not an integer")
			return
		}
		log := middleware.Logger(r)

		res, err := cs.GetCourseSchedules(r.Context(), course_id)
		if err != nil {
			log.Error("error getting course schedules", zap.Error(err))
		}

		if res.Count == 0 {
			log.Warn(fmt.Sprintf("course with id %d has no schedules", course_id))
		}

		common.WriteJSON(w, http.StatusOK, res)
	}
}

func HandleGetCourseSectionsByTerm(cs *service.CourseService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		id := chi.URLParam(r, "course_id")
		var body struct {
			Term string `json:"term"`
		}
		common.DecodeJSON(r, &body)

		course_id, err := strconv.Atoi(id)
		if err != nil {
			common.WriteError(w, http.StatusBadRequest, "course id is not an integer")
			return
		}

		if body.Term == "" {
			common.WriteError(w, http.StatusBadRequest, "term not provided")
			return
		}

		if !slices.Contains(common.ValidTerms, body.Term) {
			common.WriteError(w, http.StatusBadRequest, "invalid term provided")
			return
		}

		log := middleware.Logger(r)
		termString := common.TermNumberToString[body.Term]

		res, err := cs.GetCourseSectionsByTerm(r.Context(), course_id, termString)
		if err != nil {
			log.Error("error getting course schedules", zap.Error(err))
		}

		if res.Count == 0 {
			log.Warn(fmt.Sprintf("course with id %d has no schedules", course_id))
		}

		common.WriteJSON(w, http.StatusOK, res)
	}
}

func HandleCreateAllCourseEmbeddings(cs *service.CourseService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		cs.CreateEmbeddingForEveryCourse(r.Context())
		common.WriteJSON(w, http.StatusOK, "done")
	}
}

func HandleVectorSearchCourse(cs *service.CourseService) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		log := middleware.Logger(r)
		user, _ := middleware.UserFromContext(r.Context())

		query := r.URL.Query().Get("q")

		if query == "" {
			log.Info("search query not provided")
			common.WriteError(w, http.StatusBadRequest, "search query not provided")
			return
		}

		results, err := cs.VectorSearch(r.Context(), query, user)
		if err != nil {
			common.WriteError(w, http.StatusInternalServerError, "could not query courses")
			log.Error("could not vector search courses", zap.String("query", query), zap.Error(err))
			return
		}

		common.WriteJSON(w, http.StatusOK, results)
	}
}
