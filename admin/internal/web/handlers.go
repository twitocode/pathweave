package web

import (
	"embed"
	"encoding/json"
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
}

func (s *Server) Register(mux *http.ServeMux) {
	mux.HandleFunc("GET /", s.handleIndex)
	mux.HandleFunc("GET /programs/edit", s.handleEditProgram)
	mux.HandleFunc("POST /programs", s.handleSaveProgram)
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

	data, err := s.newPageData(r)
	if err != nil {
		http.Error(w, err.Error(), http.StatusInternalServerError)
		return
	}
	data.Selected = &selected
	data.InitialLevelsJS = levelsJS(selected.Levels)
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
