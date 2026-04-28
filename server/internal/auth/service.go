package auth

import (
	"context"
	"errors"

	"github.com/workos/workos-go/v7"

	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/store"
	"github.com/twitocode/pathweave/go-api/internal/store/sqlcgen"
)

const SessionCookieName = "wos_session"

type Service struct {
	cfg          config.Config
	client       *workos.Client
	publicClient *workos.PublicClient
	store        *store.Store
}

func NewService(cfg config.Config, s *store.Store) *Service {
	client := workos.NewClient(cfg.WorkOSAPIKey, workos.WithClientID(cfg.WorkOSClientID))
	publicClient := workos.NewPublicClient(cfg.WorkOSClientID)
	return &Service{
		cfg:          cfg,
		client:       client,
		publicClient: publicClient,
		store:        s,
	}
}

func (s *Service) LoginURL() (string, error) {
	provider := "GoogleOAuth"
	result, err := s.publicClient.GetAuthorizationURL(workos.AuthKitAuthorizationURLParams{
		RedirectURI: s.cfg.WorkOSRedirectURI,
		Provider:    &provider,
		ClientID:    s.cfg.WorkOSClientID,
	})
	if err != nil {
		return "", err
	}
	return result.URL, nil
}

func (s *Service) AuthenticateWithCode(ctx context.Context, code string) (sealedSession string, user sqlcgen.User, err error) {
	authResponse, err := s.client.UserManagement().AuthenticateWithCode(ctx, &workos.UserManagementAuthenticateWithCodeParams{
		Code: code,
	})
	if err != nil {
		return "", sqlcgen.User{}, err
	}

	if authResponse.User == nil || authResponse.User.Email == "" {
		return "", sqlcgen.User{}, errors.New("workos user email missing")
	}

	user, err = s.store.GetOrCreateUserByEmail(ctx, authResponse.User.Email)
	if err != nil {
		return "", sqlcgen.User{}, err
	}

	sealedSession, err = workos.SealSessionFromAuthResponse(
		authResponse.AccessToken,
		authResponse.RefreshToken,
		authResponse.User,
		authResponse.Impersonator,
		s.cfg.WorkOSCookiePassword,
	)
	if err != nil {
		return "", sqlcgen.User{}, err
	}
	return sealedSession, user, nil
}

func (s *Service) GetLogoutURL(ctx context.Context, sealedSession string) (string, error) {
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

func (s *Service) AuthenticateSession(ctx context.Context, sealedSession string) (*sqlcgen.User, string, error) {
	if sealedSession == "" {
		return nil, "", errors.New("no session cookie provided")
	}
	session := workos.NewSession(s.client, sealedSession, s.cfg.WorkOSCookiePassword)
	authResult, err := session.Authenticate()

	if err == nil && authResult.Authenticated && authResult.User != nil {
		dbUser, dbErr := s.store.GetOrCreateUserByEmail(ctx, authResult.User.Email)
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
		return nil, "", errors.New("session is not authenticated")
	}

	refreshedSession := workos.NewSession(s.client, refreshed.SealedSession, s.cfg.WorkOSCookiePassword)
	refreshedAuth, secondErr := refreshedSession.Authenticate()
  
	if secondErr != nil || !refreshedAuth.Authenticated || refreshedAuth.User == nil {
		if secondErr != nil {
			return nil, "", secondErr
		}
		return nil, "", errors.New("refreshed session is not authenticated")
	}
	dbUser, dbErr := s.store.GetOrCreateUserByEmail(ctx, refreshedAuth.User.Email)
	if dbErr != nil {
		return nil, "", dbErr
	}
	return &dbUser, refreshed.SealedSession, nil
}
