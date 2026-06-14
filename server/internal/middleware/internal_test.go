package middleware

import (
	"net/http"
	"net/http/httptest"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestRequireInternalTokenAllowsMatchingBearerToken(t *testing.T) {
	called := false
	handler := RequireInternalToken("secret")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		called = true
		w.WriteHeader(http.StatusNoContent)
	}))

	req := httptest.NewRequest(http.MethodPost, "/internal/scrape-runs", nil)
	req.Header.Set("Authorization", "Bearer secret")
	res := httptest.NewRecorder()

	handler.ServeHTTP(res, req)

	require.True(t, called)
	require.Equal(t, http.StatusNoContent, res.Code)
}

func TestRequireInternalTokenRejectsMissingToken(t *testing.T) {
	handler := RequireInternalToken("secret")(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		t.Fatal("handler should not be called")
	}))

	req := httptest.NewRequest(http.MethodPost, "/internal/scrape-runs", nil)
	res := httptest.NewRecorder()

	handler.ServeHTTP(res, req)

	require.Equal(t, http.StatusUnauthorized, res.Code)
}
