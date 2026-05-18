package service

import (
	"context"
	"fmt"

	openrouter "github.com/OpenRouterTeam/go-sdk"
	"github.com/OpenRouterTeam/go-sdk/models/components"
	"github.com/OpenRouterTeam/go-sdk/optionalnullable"
	"github.com/twitocode/pathweave/go-api/internal/common"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type AIService struct {
	log    *zap.Logger
	db     *db.Queries
	cfg    *config.Config
	router *openrouter.OpenRouter
}

func NewAIService(cfg *config.Config, queries *db.Queries, log *zap.Logger) *AIService {
	return &AIService{
		log: log,
		db:  queries,
		cfg: cfg,
		router: openrouter.New(
			openrouter.WithSecurity(cfg.OpenRouterAPIKey),
		),
	}
}

func (ais *AIService) SearchQueryToJson(ctx context.Context, query string) (map[string]any, error) {
	res, err := ais.router.Chat.Send(ctx, components.ChatRequest{
		MaxTokens: optionalnullable.From(openrouter.Pointer[int64](200)),
		Messages: []components.ChatMessages{
			components.CreateChatMessagesSystem(
				components.ChatSystemMessage{
					Content: components.CreateChatSystemMessageContentStr(
						common.QuerySystemPrompt,
					),
					Role: components.ChatSystemMessageRoleSystem,
				},
			),
			{
				ChatUserMessage: &components.ChatUserMessage{
					Content: components.ChatUserMessageContent{
						Str: openrouter.String(query),
					},
				},
			},
		},
		Model:       openrouter.Pointer("deepseek/deepseek-v4-flash"),
		Temperature: optionalnullable.From(new(0.7)),
	})
	if err != nil {
		return nil, err
	}

	if res != nil && len(res.ChatResult.Choices) > 0 {
		message := res.ChatResult.Choices[0].Message

		if content, ok := message.Content.Get(); ok {
			// Content is a ChatAssistantMessageContent union —
			// check which variant is set
			if content.Str != nil {
				fmt.Println(*content.Str)
			}
		}
	}

	return nil, nil
}
