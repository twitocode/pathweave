package middleware

import (
	"crypto/hmac"
	"crypto/sha256"
	"encoding/base64"
	"encoding/hex"
	"errors"
	"strconv"
	"strings"
	"time"
)

const csrfTTLSeconds int64 = 3600

func GenerateCSRFToken(secret string, now time.Time) (string, error) {
	if secret == "" {
		return "", errors.New("secret key is required for csrf")
	}
	timestamp := strconv.FormatInt(now.Unix(), 10)
	payload := timestamp
	mac := hmac.New(sha256.New, []byte(secret))
	_, _ = mac.Write([]byte(payload))
	signature := hex.EncodeToString(mac.Sum(nil))
	token := payload + "." + signature
	return base64.RawURLEncoding.EncodeToString([]byte(token)), nil
}

func ValidateCSRFToken(secret, token string, now time.Time) error {
	if secret == "" {
		return errors.New("secret key is required for csrf")
	}
	raw, err := base64.RawURLEncoding.DecodeString(token)
	if err != nil {
		return errors.New("invalid csrf token")
	}
	parts := strings.SplitN(string(raw), ".", 2)
	if len(parts) != 2 {
		return errors.New("invalid csrf token format")
	}
	timestampPart, signaturePart := parts[0], parts[1]
	issuedAt, err := strconv.ParseInt(timestampPart, 10, 64)
	if err != nil {
		return errors.New("invalid csrf timestamp")
	}
	if now.Unix()-issuedAt > csrfTTLSeconds {
		return errors.New("csrf token expired")
	}

	mac := hmac.New(sha256.New, []byte(secret))
	_, _ = mac.Write([]byte(timestampPart))
	expected := mac.Sum(nil)
	decodedSig, err := hex.DecodeString(signaturePart)
	if err != nil || !hmac.Equal(expected, decodedSig) {
		return errors.New("invalid csrf signature")
	}
	return nil
}
