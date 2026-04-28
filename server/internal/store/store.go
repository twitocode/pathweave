package store

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/jackc/pgx/v5/pgxpool"

	"github.com/twitocode/pathweave/go-api/internal/store/sqlcgen"
)

type Store struct {
	Queries *sqlcgen.Queries
}

func New(pool *pgxpool.Pool) *Store {
	return &Store{
		Queries: sqlcgen.New(pool),
	}
}

func (s *Store) GetOrCreateUserByEmail(ctx context.Context, email string) (sqlcgen.User, error) {
	user, err := s.Queries.GetUserByEmail(ctx, email)
	if err == nil {
		return user, nil
	}
	if !errors.Is(err, pgx.ErrNoRows) {
		return sqlcgen.User{}, err
	}
	return s.Queries.CreateUser(ctx, email)
}
