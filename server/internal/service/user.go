package service

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/db"
)

var ErrNotFound = errors.New("not found")

type UserService struct {
	queries *db.Queries
	log     *zap.Logger
}

func NewUserService(queries *db.Queries, log *zap.Logger) *UserService {
	return &UserService{
		queries: queries,
		log:     log,
	}
}

func (s *UserService) GetByEmail(ctx context.Context, email string) (db.User, error) {
	user, err := s.queries.GetUserByEmail(ctx, email)
	if err != nil {
		if errors.Is(err, pgx.ErrNoRows) {
			return db.User{}, ErrNotFound
		}
		s.log.Error("get user by email", zap.String("email", email), zap.Error(err))
		return db.User{}, err
	}
	return user, nil
}

func (s *UserService) GetOrCreateByEmail(ctx context.Context, email string) (db.User, error) {
	user, err := s.queries.GetUserByEmail(ctx, email)
	if err == nil {
		return user, nil
	}
	if errors.Is(err, pgx.ErrNoRows) {
		return s.queries.CreateUser(ctx, email)
	}
	s.log.Error("get or create user", zap.String("email", email), zap.Error(err))
	return db.User{}, err
}

func (s *UserService) Create(ctx context.Context, email string) (db.User, error) {
	user, err := s.queries.CreateUser(ctx, email)
	if err != nil {
		s.log.Error("create user", zap.String("email", email), zap.Error(err))
		return db.User{}, err
	}
	return user, nil
}
