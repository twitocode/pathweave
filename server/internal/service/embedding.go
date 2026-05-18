package service

import (
	"context"
	"fmt"

	openrouter "github.com/revrost/go-openrouter"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

var dimensions int = 512

type EmbeddingService struct {
	log    *zap.Logger
	db     *db.Queries
	cfg    *config.Config
	client *openrouter.Client
}

func NewEmbeddingService(cfg *config.Config, queries *db.Queries, log *zap.Logger) *EmbeddingService {
	return &EmbeddingService{
		log:    log,
		db:     queries,
		cfg:    cfg,
		client: openrouter.NewClient(cfg.OpenRouterAPIKey),
	}
}

func (es *EmbeddingService) CreateEmbedding(ctx context.Context, data string) ([]float64, error) {
	req := openrouter.EmbeddingsRequest{
		Model:      "qwen/qwen3-embedding-8b",
		Input:      data,
		Dimensions: &dimensions,
	}

	res, err := es.client.CreateEmbeddings(ctx, req)
	if err != nil {
		es.log.Error("could not create embedding", zap.Error(err))
		return nil, err
	}

	if len(res.Data) > 0 {
		return res.Data[0].Embedding.Vector, nil
	}

	return nil, fmt.Errorf("no embedding returned")
}

func (es *EmbeddingService) CreateEmbeddingBatched(ctx context.Context, data []string) ([][]float64, error) {
	req := openrouter.EmbeddingsRequest{
		Model:      "qwen/qwen3-embedding-8b",
		Input:      data,
		Dimensions: &dimensions,
	}

	res, err := es.client.CreateEmbeddings(ctx, req)
	if err != nil {
		es.log.Error("could not create batched embeddings", zap.Error(err))
		return nil, err
	}

	var embeddings [][]float64
	for _, item := range res.Data {
		embeddings = append(embeddings, item.Embedding.Vector)
	}

	return embeddings, nil
}
