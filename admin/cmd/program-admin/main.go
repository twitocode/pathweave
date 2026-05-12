package main

import (
	"context"
	"errors"
	"fmt"
	"log"
	"net/http"
	"os"
	"os/signal"
	"syscall"
	"time"

	"github.com/jackc/pgx/v5/pgxpool"
	"github.com/joho/godotenv"

	"github.com/twitocode/pathweave/program-admin/internal/program"
	"github.com/twitocode/pathweave/program-admin/internal/web"
)

func main() {
	if err := run(context.Background(), os.Getenv); err != nil {
		log.Fatal(err)
	}
}

func run(ctx context.Context, getenv func(string) string) error {
	if err := godotenv.Load(".env", "../.env", "../server/.env"); err != nil && !errors.Is(err, os.ErrNotExist) {
		return fmt.Errorf("load env files: %w", err)
	}

	databaseURL := getenv("DATABASE_URL")
	if databaseURL == "" {
		return fmt.Errorf("DATABASE_URL is required")
	}

	port := getenv("PROGRAM_ADMIN_PORT")
	if port == "" {
		port = "8091"
	}

	ctx, cancel := signal.NotifyContext(ctx, os.Interrupt, syscall.SIGTERM)
	defer cancel()

	pool, err := pgxpool.New(ctx, databaseURL)
	if err != nil {
		return fmt.Errorf("create db pool: %w", err)
	}
	defer pool.Close()

	if err := pool.Ping(ctx); err != nil {
		return fmt.Errorf("ping db: %w", err)
	}

	store := program.NewStore(pool)
	if err := store.EnsureSchema(ctx); err != nil {
		return err
	}

	webServer, err := web.NewServer(store)
	if err != nil {
		return fmt.Errorf("create web server: %w", err)
	}

	mux := http.NewServeMux()
	webServer.Register(mux)

	server := &http.Server{
		Addr:         ":" + port,
		Handler:      mux,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 20 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	errCh := make(chan error, 1)
	go func() {
		log.Printf("program-admin listening on http://localhost:%s\n", port)
		if err := server.ListenAndServe(); err != nil && !errors.Is(err, http.ErrServerClosed) {
			errCh <- err
		}
	}()

	select {
	case <-ctx.Done():
	case err := <-errCh:
		return err
	}

	shutdownCtx, shutdownCancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer shutdownCancel()
	return server.Shutdown(shutdownCtx)
}
