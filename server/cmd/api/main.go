package main

import (
	"context"
	"log"
	"net/http"
	"time"

	"github.com/twitocode/pathweave/go-api/internal/api"
	"github.com/twitocode/pathweave/go-api/internal/auth"
	"github.com/twitocode/pathweave/go-api/internal/config"
	"github.com/twitocode/pathweave/go-api/internal/db"
	"github.com/twitocode/pathweave/go-api/internal/service"
	"github.com/twitocode/pathweave/go-api/internal/store"
)

func main() {
	cfg, err := config.Load()
	if err != nil {
		log.Fatalf("load config: %v", err)
	}

	ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
	defer cancel()

	pool, err := db.NewPool(ctx, cfg.DatabaseURL)
	if err != nil {
		log.Fatalf("database startup failed: %v", err)
	}
	defer pool.Close()

	st := store.New(pool)
	authService := auth.NewService(cfg, st)
	aiClient := service.NewAIClient(cfg.PythonAIBaseURL, cfg.InternalServiceToken)

	router := api.NewRouter(
		api.NewAuthHandlers(cfg, authService),
		api.NewDomainHandlers(),
		api.NewAIHandlers(aiClient),
	)

	server := &http.Server{
		Addr:         ":" + cfg.Port,
		Handler:      router,
		ReadTimeout:  15 * time.Second,
		WriteTimeout: 15 * time.Second,
		IdleTimeout:  30 * time.Second,
	}

	log.Printf("go api listening on :%s", cfg.Port)
	if err := server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatalf("server failed: %v", err)
	}
}
