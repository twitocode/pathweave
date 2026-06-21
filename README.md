# PathWeave

PathWeave is a modern, full-stack McMaster course planner designed to make academic planning seamless and intelligent. it makes use of Mapbox to visually see the routes a student would take during a day, as well as RateMyProfessor data to determine if classes are worth going to.

## Tech Stack

### Frontend (`/client`)

- **Framework**: [SvelteKit](https://kit.svelte.dev/)
- **Language**: TypeScript
- **Styling**: Tailwind CSS + ShadcnSvelte
- **Tooling**: Vite, ESLint, Prettier, Bun

### Backend (`/server`)

- **Language**: Go
- **Database**: PostgreSQL with `pgvector` extension
- **Database Tools**: `sqlc` for query generation, `goose` for migrations

### Scraping (`/scraping`)

- **Language**: Python
- **Tools**: Playwright & BeautifulSoup
- **Environment**: `uv`

## Getting Started

### Prerequisites

Make sure you have the following installed on your machine:

- [Bun](https://bun.sh/) (for frontend dependencies)
- [Go](https://golang.org/) (1.20+)
- [Python 3.10+](https://www.python.org/) and [uv](https://github.com/astral-sh/uv)
- [PostgreSQL](https://www.postgresql.org/) with the `[pgvector](https://github.com/pgvector/pgvector)` extension enabled

### 1. Database Setup

Ensure PostgreSQL is running and create a database for PathWeave.
Apply the database migrations to set up the schemas:

```bash
cd server
# Ensure your DATABASE_URL environment variable is set
goose -dir db/migrations postgres "$DATABASE_URL" up
```

### 2. Backend Setup

Navigate to the server directory and start the Go backend:

```bash
cd server
go mod download
go run cmd/api/main.go
```

### 3. Frontend Setup

Navigate to the client directory, install dependencies, and run the development server:

```bash
cd client
bun install
bun run dev
```

*(Note: Ensure your `.env` is configured with portal credentials and database access for the scrapers).*

