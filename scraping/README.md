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
   - `GO_API_BASE_URL`
2. Start Python AI service:
   - `just dev`
3. Start Go API:
   - `just go-dev`

## Scraping Ingestion Pipeline

Python still owns browser scraping and writes JSON artifacts under `data/`. The Go API now owns validation, staging, and promotion into Postgres through internal scrape-run endpoints.

Recommended flow:

1. Run the scraper scripts that produce:
   - `data/all_courses.json`
   - `data/all_programs_with_requirements.json`
   - `data/rmp_data.json`
   - `data/all_possible_schedules.json`
2. Start the Go API with `INTERNAL_SERVICE_TOKEN` configured.
3. Publish and promote the artifacts:
   - `just publish`

For inspection before promotion:

- `just publish-stage-only`
- Then call `POST /internal/scrape-runs/{run_id}/promote` with `Authorization: Bearer $INTERNAL_SERVICE_TOKEN`.

`scripts/seed_db.py` is now legacy. It still exists as a compatibility fallback, but new scrape runs should go through `scripts/publish_scrape_run.py` so database writes stay in the Go server.

## Go API Commands

- `cd go-api && make run`
- `cd go-api && make test`
- `cd go-api && make sqlc`
