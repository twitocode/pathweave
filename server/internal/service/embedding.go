package service

import (
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/twitocode/pathweave/go-api/internal/db"

	"go.uber.org/zap"
)

type EmbeddingService struct {
	log  *zap.Logger
	db   *db.Queries
	pool *pgxpool.Pool
}

func NewEmbeddingService(queries *db.Queries, log *zap.Logger, pool *pgxpool.Pool) *EmbeddingService {
	return &EmbeddingService{log: log, db: queries, pool: pool}
}

