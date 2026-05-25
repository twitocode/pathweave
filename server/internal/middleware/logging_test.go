package middleware

import (
	"strings"
	"testing"
	"time"
)

func TestFormatHTTPRequestPretty(t *testing.T) {
	msg := formatHTTPRequestPretty("GET", "/auth/me", 200, 19*time.Millisecond+692708*time.Nanosecond, "[::1]:64682")

	if msg != "\x1b[36mGET\x1b[0m /auth/me \x1b[32m200\x1b[0m 19.7ms \x1b[90m[::1]\x1b[0m" {
		t.Fatalf("unexpected message:\n%s", msg)
	}
}

func TestStripPort(t *testing.T) {
	cases := []struct {
		addr string
		want string
	}{
		{"[::1]:64682", "[::1]"},
		{"127.0.0.1:8080", "127.0.0.1"},
		{"no-port", "no-port"},
	}
	for _, tc := range cases {
		if got := stripPort(tc.addr); got != tc.want {
			t.Fatalf("stripPort(%q) = %q, want %q", tc.addr, got, tc.want)
		}
	}
}

func TestFormatHTTPRequestPrettyStatusColors(t *testing.T) {
	cases := []struct {
		status int
		color  string
	}{
		{200, "32"},
		{301, "36"},
		{404, "33"},
		{500, "31"},
	}

	for _, tc := range cases {
		msg := formatHTTPRequestPretty("GET", "/x", tc.status, time.Millisecond, "127.0.0.1")
		want := "\x1b[" + tc.color + "m" + formatStatus(tc.status) + "\x1b[0m"
		if !strings.Contains(msg, want) {
			t.Fatalf("status %d: expected %q in %q", tc.status, want, msg)
		}
	}
}
