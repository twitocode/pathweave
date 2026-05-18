package service

import (
	"context"

	openrouter "github.com/OpenRouterTeam/go-sdk"
	"github.com/OpenRouterTeam/go-sdk/models/operations"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type EmbeddingService struct {
	log    *zap.Logger
	db     *db.Queries
	cfg    *config.Config
	router *openrouter.OpenRouter
}

func NewEmbeddingService(cfg *config.Config, queries *db.Queries, log *zap.Logger) *EmbeddingService {
	return &EmbeddingService{
		log: log,
		db:  queries,
		cfg: cfg,
		router: openrouter.New(
			openrouter.WithSecurity(cfg.OpenRouterAPIKey),
		),
	}
}

func (es *EmbeddingService) CreateEmbedding(ctx context.Context, data string) ([]float64, error) {
	res, err := es.router.Embeddings.Generate(ctx, operations.CreateEmbeddingsRequest{
		Input: operations.CreateInputUnionStr(
			data,
		),
		Model:      "qwen/qwen3-embedding-8b",
		Dimensions: openrouter.Int64(512),
	})

	if err != nil {
		es.log.Fatal("could not create embedding", zap.Error(err))
		return nil, err
	}

	if res != nil {
		switch res.Type {
		case operations.CreateEmbeddingsResponseTypeCreateEmbeddingsResponseBody:
			body := res.CreateEmbeddingsResponseBody
			return body.Data[0].Embedding.ArrayOfNumber, nil
		case operations.CreateEmbeddingsResponseTypeStr:
			es.log.Debug("got a string for a vector embedding", zap.String("res", *res.Str))
		}
	}

	return nil, nil
}

func (es *EmbeddingService) CreateEmbeddingBatched(ctx context.Context, data []string) ([][]float64, error) {
	res, err := es.router.Embeddings.Generate(ctx, operations.CreateEmbeddingsRequest{
		Input: operations.CreateInputUnionArrayOfStr(
			data,
		),
		Model:      "qwen/qwen3-embedding-8b",
		Dimensions: openrouter.Int64(512),
	})

	if err != nil {
		es.log.Error("could not create batched embeddings", zap.Error(err))
		return nil, err
	}

	if res != nil {
		switch res.Type {
		case operations.CreateEmbeddingsResponseTypeCreateEmbeddingsResponseBody:
			body := res.CreateEmbeddingsResponseBody
			var embeddings [][]float64
			for _, item := range body.Data {
				embeddings = append(embeddings, item.Embedding.ArrayOfNumber)
			}
			return embeddings, nil
		case operations.CreateEmbeddingsResponseTypeStr:
			es.log.Debug("got a string for a vector embedding", zap.String("res", *res.Str))
		}
	}

	return nil, nil
}
