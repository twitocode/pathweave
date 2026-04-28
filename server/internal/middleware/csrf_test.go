package middleware

import (
	"testing"
	"time"

	"github.com/stretchr/testify/require"
)

func TestGenerateAndValidateCSRFToken(t *testing.T) {
	now := time.Unix(1_700_000_000, 0)
	token, err := GenerateCSRFToken("secret", now)
	require.NoError(t, err)
	require.NotEmpty(t, token)

	err = ValidateCSRFToken("secret", token, now.Add(10*time.Minute))
	require.NoError(t, err)
}

func TestValidateCSRFTokenFailsWhenExpired(t *testing.T) {
	now := time.Unix(1_700_000_000, 0)
	token, err := GenerateCSRFToken("secret", now)
	require.NoError(t, err)

	err = ValidateCSRFToken("secret", token, now.Add(2*time.Hour))
	require.Error(t, err)
}
