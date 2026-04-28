package api

import (
	"net/http"

	"github.com/go-chi/render"
)

type DomainHandlers struct{}

func NewDomainHandlers() *DomainHandlers {
	return &DomainHandlers{}
}

func (h *DomainHandlers) Health(w http.ResponseWriter, r *http.Request) {
	render.JSON(w, r, map[string]string{"status": "ok", "service": "go-api"})
}
