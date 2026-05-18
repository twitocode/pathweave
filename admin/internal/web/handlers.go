package web

import (
	"embed"
	"encoding/json"
	"fmt"
	"html/template"
	"net/http"
	"strconv"
	"strings"

	"github.com/twitocode/pathweave/program-admin/internal/program"
)

//go:embed templates/*.html
var templatesFS embed.FS

type Server struct {
	store *program.Store
	tmpl  *template.Template
}

func NewServer(store *program.Store) (*Server, error) {
	tmpl, err := template.ParseFS(templatesFS, "templates/*.html")
	if err != nil {
		return nil, err
	}
	return &Server{store: store, tmpl: tmpl}, nil
}

type pageData struct {
	Message         string
	Error           string
	Programs        []program.Summary
	Selected        *program.EditableProgram
	InitialLevelsJS template.JS
	Antirequisites  []program.AntirequisiteCourse
	ProgramID       int64
	ReviewPrograms  []program.Summary
	Restrictions    []program.CourseRestriction
}

func (s *Server) Register(mux *http.ServeMux) {
	mux.HandleFunc("GET /", s.handleIndex)
	mux.HandleFunc("GET /programs/edit", s.handleEditProgram)
	mux.HandleFunc("POST /programs", s.handleSaveProgram)

	// Antirequisite routes
	mux.HandleFunc("POST /programs/antirequisites/populate", s.handlePopulateAntirequisites)
	mux.HandleFunc("POST /programs/antirequisites/populate-all", s.handlePopulateAllAntirequisites)
	mux.HandleFunc("POST /programs/antirequisites/add", s.handleAddAntirequisite)
	mux.HandleFunc("POST /programs/antirequisites/remove", s.handleRemoveAntirequisite)
	mux.HandleFunc("POST /programs/antirequisites/clear", s.handleClearAntirequisites)
	mux.HandleFunc("GET /antirequisites", s.handleReviewAntirequisites)
}

func (s *Server) handleIndex(w http.ResponseWriter, r *http.Request) {
	data, err := s.newPageData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	s.render(w, "index.html", data)
}

func (s *Server) handleEditProgram(w http.ResponseWriter, r *http.Request) {
	id, err := strconv.ParseInt(r.URL.Query().Get("id"), 10, 64)
	if err != nil || id <= 0 {
		http.Redirect(w, r, "/", http.StatusSeeOther)
		return
	}

	selected, err := s.store.GetProgram(r.Context(), id)
	if err != nil {
		data, pageErr := s.newPageData(r)
		if pageErr != nil {
			http.Error(w, pageErr.Error(), http.StatusInternalServerError)
			return
		}
		data.Error = "Could not load program: " + err.Error()
		s.render(w, "index.html", data)
		return
	}

	antireqs, _ := s.store.ListAntirequisites(r.Context(), id)

	data, err := s.newPageData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data.Selected = &selected
	data.InitialLevelsJS = levelsJS(selected.Levels)
	data.Antirequisites = antireqs
	data.ProgramID = id
	s.render(w, "index.html", data)
}

func (s *Server) handleSaveProgram(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		s.renderResult(w, pageData{Error: "Could not parse form input."})
		return
	}

	payload, err := program.BuildPayload(program.FormInput{
		Name:      r.FormValue("name"),
		SourceURL: r.FormValue("source_url"),
		Levels:    levelsFromForm(r),
	})
	if err != nil {
		s.renderResult(w, pageData{Error: err.Error()})
		return
	}

	result, err := s.store.SaveProgram(r.Context(), payload)
	if err != nil {
		s.renderResult(w, pageData{Error: "Database write failed: " + err.Error()})
		return
	}

	parts := []string{
		"Saved program \"" + payload.Name + "\".",
		"Linked " + itoa(result.LinkedCourseCount) + " course(s).",
	}
	if result.PlaceholderCourseCount > 0 {
		parts = append(parts,
			"Added "+itoa(result.PlaceholderCourseCount)+
				" placeholder course(s) for codes not yet in the catalog (named \"[pending] …\").")
	}
	message := strings.Join(parts, " ")

	s.renderResult(w, pageData{Message: message})
}

// --- Antirequisite Handlers ---

func (s *Server) handlePopulateAntirequisites(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		s.renderResult(w, pageData{Error: "Could not parse form."})
		return
	}
	programID, err := strconv.ParseInt(r.FormValue("program_id"), 10, 64)
	if err != nil || programID <= 0 {
		s.renderResult(w, pageData{Error: "Invalid program ID."})
		return
	}

	inserted, skipped, err := s.store.PopulateAntirequisites(r.Context(), programID)
	if err != nil {
		s.renderResult(w, pageData{Error: "Populate failed: " + err.Error()})
		return
	}

	msg := fmt.Sprintf("Populated %d antirequisite(s) from course restrictions.", inserted)
	if len(skipped) > 0 {
		msg += fmt.Sprintf(" Skipped %d code(s) not found in catalog: %s", len(skipped), strings.Join(skipped, ", "))
	}

	s.renderAntirequisiteResult(w, r, programID, msg, "")
}

func (s *Server) handlePopulateAllAntirequisites(w http.ResponseWriter, r *http.Request) {
	inserted, err := s.store.PopulateAllAntirequisites(r.Context())
	if err != nil {
		s.renderResult(w, pageData{Error: "Failed to populate all: " + err.Error()})
		return
	}
	s.renderResult(w, pageData{Message: fmt.Sprintf("Populated %d antirequisite(s) across all programs.", inserted)})
}

func (s *Server) handleReviewAntirequisites(w http.ResponseWriter, r *http.Request) {
	programs, err := s.store.ListProgramsWithAntirequisites(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}

	data, err := s.newPageData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data.ReviewPrograms = programs

	// If a program is selected, load its antirequisites
	if idStr := r.URL.Query().Get("id"); idStr != "" {
		if id, err := strconv.ParseInt(idStr, 10, 64); err == nil && id > 0 {
			if selected, err := s.store.GetProgram(r.Context(), id); err == nil {
				data.Selected = &selected
				data.ProgramID = id
				data.Antirequisites, _ = s.store.ListAntirequisites(r.Context(), id)
				data.Restrictions, _ = s.store.GetRestrictionsForProgramCourses(r.Context(), id)
			}
		}
	}

	s.render(w, "review.html", data)
}

func (s *Server) handleAddAntirequisite(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		s.renderResult(w, pageData{Error: "Could not parse form."})
		return
	}
	programID, _ := strconv.ParseInt(r.FormValue("program_id"), 10, 64)
	courseCode := strings.TrimSpace(strings.ToUpper(r.FormValue("course_code")))

	if programID <= 0 || courseCode == "" {
		s.renderAntirequisiteResult(w, r, programID, "", "Program ID and course code are required.")
		return
	}

	if err := s.store.AddAntirequisite(r.Context(), programID, courseCode); err != nil {
		s.renderAntirequisiteResult(w, r, programID, "", "Could not add: "+err.Error())
		return
	}

	s.renderAntirequisiteResult(w, r, programID, fmt.Sprintf("Added %s as antirequisite.", courseCode), "")
}

func (s *Server) handleRemoveAntirequisite(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		s.renderResult(w, pageData{Error: "Could not parse form."})
		return
	}
	programID, _ := strconv.ParseInt(r.FormValue("program_id"), 10, 64)
	courseID, _ := strconv.ParseInt(r.FormValue("course_id"), 10, 64)

	if programID <= 0 || courseID <= 0 {
		s.renderResult(w, pageData{Error: "Invalid IDs."})
		return
	}

	if err := s.store.RemoveAntirequisite(r.Context(), programID, courseID); err != nil {
		s.renderAntirequisiteResult(w, r, programID, "", "Remove failed: "+err.Error())
		return
	}

	s.renderAntirequisiteResult(w, r, programID, "Removed antirequisite.", "")
}

func (s *Server) handleClearAntirequisites(w http.ResponseWriter, r *http.Request) {
	if err := r.ParseForm(); err != nil {
		s.renderResult(w, pageData{Error: "Could not parse form."})
		return
	}
	programID, _ := strconv.ParseInt(r.FormValue("program_id"), 10, 64)
	if programID <= 0 {
		s.renderResult(w, pageData{Error: "Invalid program ID."})
		return
	}

	if err := s.store.ClearAntirequisites(r.Context(), programID); err != nil {
		s.renderAntirequisiteResult(w, r, programID, "", "Clear failed: "+err.Error())
		return
	}

	s.renderAntirequisiteResult(w, r, programID, "Cleared all antirequisites.", "")
}

func (s *Server) renderAntirequisiteResult(w http.ResponseWriter, r *http.Request, programID int64, message, errMsg string) {
	antireqs, _ := s.store.ListAntirequisites(r.Context(), programID)

	data := pageData{
		Message:        message,
		Error:          errMsg,
		Antirequisites: antireqs,
		ProgramID:      programID,
	}
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	s.render(w, "antirequisites_panel.html", data)
}

func (s *Server) renderResult(w http.ResponseWriter, data pageData) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	s.render(w, "result.html", data)
}

func (s *Server) render(w http.ResponseWriter, name string, data pageData) {
	if err := s.tmpl.ExecuteTemplate(w, name, data); err != nil {
		http.Error(w, "template render failed: "+err.Error(), http.StatusInternalServerError)
	}
}

func itoa(v int) string {
	return strconv.Itoa(v)
}

func levelsFromForm(r *http.Request) []program.LevelInput {
	var input struct {
		Levels []program.LevelInput `json:"levels"`
	}
	if err := json.Unmarshal([]byte(r.FormValue("requirements_structure")), &input); err != nil {
		return nil
	}
	return input.Levels
}

func (s *Server) newPageData(r *http.Request) (pageData, error) {
	programs, err := s.store.ListPrograms(r.Context())
	if err != nil {
		return pageData{}, err
	}
	return pageData{
		Programs:        programs,
		InitialLevelsJS: levelsJS(nil),
	}, nil
}

func levelsJS(levels []program.LevelInput) template.JS {
	if len(levels) == 0 {
		levels = []program.LevelInput{{
			Index: 1,
			Groups: []program.GroupInput{{
				Requirements: []program.RequirementRowInput{{Kind: "course"}},
			}},
		}}
	}
	data, err := json.Marshal(levels)
	if err != nil {
		return template.JS("[]")
	}
	return template.JS(data)
}
