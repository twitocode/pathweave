package service

import (
	"context"
	"errors"

	"github.com/jackc/pgx/v5"
	"github.com/workos/workos-go/v7"
	"go.uber.org/zap"

	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
)

const SessionCookieName = "wos_session"
const PKCECookieName = "wos_pkce"

var (
	ErrNoSession    = errors.New("no session cookie provided")
	ErrUnauthorized = errors.New("unauthorized")
)

type AuthService struct {
	cfg          *config.Config
	client       *workos.Client
	publicClient *workos.PublicClient
	db           *db.Queries
	log          *zap.Logger
}

func NewAuthService(cfg *config.Config, queries *db.Queries, log *zap.Logger) *AuthService {
	client := workos.NewClient(cfg.WorkOSAPIKey, workos.WithClientID(cfg.WorkOSClientID))
	publicClient := workos.NewPublicClient(cfg.WorkOSClientID)
	return &AuthService{
		cfg:          cfg,
		client:       client,
		publicClient: publicClient,
		db:           queries,
		log:          log,
	}
}

func (s *AuthService) LoginURL() (string, string, error) {
	provider := "GoogleOAuth"
	result, err := s.publicClient.GetAuthorizationURL(workos.AuthKitAuthorizationURLParams{
		RedirectURI: s.cfg.WorkOSRedirectURI,
		Provider:    &provider,
		ClientID:    s.cfg.WorkOSClientID,
	})
	if err != nil {
		return "", "", err
	}
	return result.URL, result.CodeVerifier, nil
}

func (s *AuthService) AuthenticateWithCode(ctx context.Context, code, codeVerifier string) (sealedSession string, user db.User, err error) {
	params := &workos.UserManagementAuthenticateWithCodeParams{
		Code: code,
	}
	if codeVerifier != "" {
		params.CodeVerifier = &codeVerifier
	}

	authResponse, err := s.client.UserManagement().AuthenticateWithCode(ctx, params)
	if err != nil {
		return "", db.User{}, err
	}

	if authResponse.User == nil || authResponse.User.Email == "" {
		return "", db.User{}, errors.New("workos user email missing")
	}

	user, err = s.GetOrCreateUserByEmail(ctx, authResponse.User.Email)
	if err != nil {
		return "", db.User{}, err
	}

	sealedSession, err = workos.SealSessionFromAuthResponse(
		authResponse.AccessToken,
		authResponse.RefreshToken,
		authResponse.User,
		authResponse.Impersonator,
		s.cfg.WorkOSCookiePassword,
	)
	if err != nil {
		return "", db.User{}, err
	}
	return sealedSession, user, nil
}

func (s *AuthService) GetLogoutURL(ctx context.Context, sealedSession string) (string, error) {
	if sealedSession == "" {
		return s.cfg.FrontendAppURL, nil
	}
	session := workos.NewSession(s.client, sealedSession, s.cfg.WorkOSCookiePassword)
	logoutURL, err := session.GetLogoutURL(ctx, s.cfg.FrontendAppURL)

	if err != nil {
		return s.cfg.FrontendAppURL, nil
	}
	return logoutURL, nil
}

func (s *AuthService) AuthenticateSession(ctx context.Context, sealedSession string) (*db.User, string, error) {
	if sealedSession == "" {
		return nil, "", ErrNoSession
	}
	session := workos.NewSession(s.client, sealedSession, s.cfg.WorkOSCookiePassword)
	authResult, err := session.Authenticate()

	if err == nil && authResult.Authenticated && authResult.User != nil {
		dbUser, dbErr := s.GetOrCreateUserByEmail(ctx, authResult.User.Email)
		if dbErr != nil {
			return nil, "", dbErr
		}
		return &dbUser, "", nil
	}

	refreshed, refreshErr := session.Refresh(ctx)
	if refreshErr != nil || !refreshed.Authenticated {
		if err != nil {
			return nil, "", err
		}
		return nil, "", ErrUnauthorized
	}

	refreshedSession := workos.NewSession(s.client, refreshed.SealedSession, s.cfg.WorkOSCookiePassword)
	refreshedAuth, secondErr := refreshedSession.Authenticate()

	if secondErr != nil || !refreshedAuth.Authenticated || refreshedAuth.User == nil {
		if secondErr != nil {
			return nil, "", secondErr
		}
		return nil, "", ErrUnauthorized
	}
	dbUser, dbErr := s.GetOrCreateUserByEmail(ctx, refreshedAuth.User.Email)
	if dbErr != nil {
		return nil, "", dbErr
	}
	return &dbUser, refreshed.SealedSession, nil
}

func (s *AuthService) GetOrCreateUserByEmail(ctx context.Context, email string) (db.User, error) {
	user, err := s.db.GetUserByEmail(ctx, email)
	if err == nil {
		return user, nil
	}
	if errors.Is(err, pgx.ErrNoRows) {
		return s.db.CreateUser(ctx, email)
	}
	return db.User{}, err
}

func (s *AuthService) GetOnboardingState(ctx context.Context, user *db.User) (bool, error) {
	exists, err := s.db.HasCompletedOnboarding(ctx, user.ID)
	if err != nil {
		return false, err
	}

	return exists, nil
}

func (s *AuthService) GetMe(ctx context.Context, user *db.User) (map[string]any, error) {
	onboarded, err := s.GetOnboardingState(ctx, user)
	if err != nil {
		return nil, err
	}

	if onboarded {
		s.log.Debug("user has already completed onboarding")
	} else {
		s.log.Debug("user hasn't completed onboarding")
	}

	return map[string]any{
		"id":        user.ID,
		"email":     user.Email,
		"onboarded": onboarded,
	}, nil
}
