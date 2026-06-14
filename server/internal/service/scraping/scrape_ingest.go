package scraping

import (
	"context"
	"encoding/json"
	"errors"
	"strings"

	"github.com/google/uuid"
	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"go.uber.org/zap"
)

type ScrapeIngestService struct {
	db   *db.Queries
	pool *pgxpool.Pool
	log  *zap.Logger
}

func NewScrapeIngestService(queries *db.Queries, pool *pgxpool.Pool, log *zap.Logger) *ScrapeIngestService {
	return &ScrapeIngestService{db: queries, pool: pool, log: log}
}

func (s *ScrapeIngestService) CreateRun(ctx context.Context, req CreateScrapeRunRequest) (db.ScrapeRun, error) {
	source := strings.TrimSpace(req.Source)
	if source == "" {
		source = "manual"
	}
	metadata := req.Metadata
	if len(metadata) == 0 {
		metadata = json.RawMessage(`{}`)
	}
	if !json.Valid(metadata) {
		return db.ScrapeRun{}, errors.New("metadata must be valid JSON")
	}
	return s.db.CreateScrapeRun(ctx, db.CreateScrapeRunParams{
		Source:   source,
		Metadata: []byte(metadata),
	})
}

func (s *ScrapeIngestService) GetRun(ctx context.Context, runID uuid.UUID) (db.ScrapeRun, error) {
	return s.db.GetScrapeRun(ctx, runID)
}
