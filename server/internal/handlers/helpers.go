package handlers

import (
	"net/url"
)

func authErrorRedirect(baseURL, reason string) string {
	base, err := url.Parse(baseURL)
	if err != nil {
		return baseURL
	}

	query := base.Query()
	query.Set("auth_error", reason)
	base.RawQuery = query.Encode()
	return base.String()
}
