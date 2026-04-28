package api

import (
	"net/http"

	"github.com/go-chi/render"

	"github.com/twitocode/pathweave/go-api/internal/service"
)

type AIHandlers struct {
	client *service.AIClient
}

func NewAIHandlers(client *service.AIClient) *AIHandlers {
	return &AIHandlers{client: client}
}

func (h *AIHandlers) HealthProxy(w http.ResponseWriter, r *http.Request) {
	status, err := h.client.Health(r.Context())
	if err != nil {
		http.Error(w, err.Error(), http.StatusBadGateway)
		return
	}
	render.JSON(w, r, map[string]any{
		"goApi":      "ok",
		"pythonAi":   status,
		"proxyRoute": "/ai/health",
	})
}
