# PathWeave Backend Split

## Services

- `go-api/`: Primary API service (auth, onboarding, pathfinder) built with Go, WorkOS, sqlc, and testify.
- `src/`: Python AI integration service (future AI and RateMyProfessor integrations only).

## Local Run

1. Set environment values in `.env`:
   - `DATABASE_URL`
   - `WORKOS_API_KEY`
   - `WORKOS_CLIENT_ID`
   - `WORKOS_COOKIE_PASSWORD`
   - `INTERNAL_SERVICE_TOKEN`
2. Start Python AI service:
   - `just dev`
3. Start Go API:
   - `just go-dev`

## Go API Commands

- `cd go-api && make run`
- `cd go-api && make test`
- `cd go-api && make sqlc`
