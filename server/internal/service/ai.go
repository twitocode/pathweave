package service

import (
	"context"
	"encoding/json"
	"errors"

	openrouter "github.com/revrost/go-openrouter"

	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type AIService struct {
	log    *zap.Logger
	db     *db.Queries
	cfg    *config.Config
	router *openrouter.Client
}

func NewAIService(cfg *config.Config, queries *db.Queries, log *zap.Logger) *AIService {
	return &AIService{
		log: log,
		db:  queries,
		cfg: cfg,
		router: openrouter.NewClient(
			cfg.OpenRouterAPIKey,
		),
	}
}

type QueryMetadata struct {
	Query string  `json:"query"`
	Level *int    `json:"level"`
	Term  *string `json:"term"`
	Unit  *string `json:"unit"`
	Code  *string `json:"code"`
}

func (ais *AIService) SearchQueryToJson(ctx context.Context, query string) (*QueryMetadata, error) {
	resp, err := ais.router.CreateChatCompletion(
		ctx,
		openrouter.ChatCompletionRequest{
			Model: "google/gemini-2.5-flash-lite",
			Messages: []openrouter.ChatCompletionMessage{
				openrouter.SystemMessage(common.QuerySystemPrompt),
				openrouter.UserMessage(query),
			},
		},
	)

	if err != nil {
		return nil, err
	}
	if len(resp.Choices) == 0 {
		return nil, errors.New("no choices returned from model")
	}

	var data QueryMetadata
	responseText := resp.Choices[0].Message.Content.Text
  ais.log.Debug("ai response",zap.String("res",responseText))
	if err := json.Unmarshal([]byte(common.ExtractJSON(responseText)), &data); err != nil {
		return nil, err
	}

	return &data, nil
}
