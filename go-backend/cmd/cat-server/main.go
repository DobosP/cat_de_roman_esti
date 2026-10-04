// cat-server serves the native arcade and optional PostgreSQL accounts.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

func main() {
	addr := flag.String("listen", "127.0.0.1:8081", "HTTP bind address")
	migrate := flag.Bool("migrate", false, "apply native account schema to configured PostgreSQL")
	replay := flag.Bool("replay", false, "offline JSON-lines HTTP request replay on stdin/stdout")
	flag.Parse()
	if err := validateRuntimeEnvironment(); err != nil {
		log.Fatal(err)
	}
	c, err := content.Load()
	if err != nil {
		log.Fatal(err)
	}
	handler := httpapi.New(c)
	bootCtx, bootCancel := context.WithTimeout(context.Background(), 30*time.Second)
	closeAccounts, err := enableAccounts(bootCtx, handler, *addr, *migrate)
	bootCancel()
	if err != nil {
		log.Fatal(err)
	}
	defer closeAccounts()
	if *replay {
		if err = replayRequests(handler); err != nil {
			log.Fatal(err)
		}
		return
	}
	server := &http.Server{Addr: *addr, Handler: handler, ReadHeaderTimeout: 5 * time.Second, ReadTimeout: 15 * time.Second, WriteTimeout: 30 * time.Second, IdleTimeout: 60 * time.Second, MaxHeaderBytes: 16 * 1024}
	ctx, stop := signal.NotifyContext(context.Background(), os.Interrupt, syscall.SIGTERM)
	defer stop()
	go func() {
		<-ctx.Done()
		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()
		if err := server.Shutdown(ctx); err != nil {
			log.Print(err)
		}
	}()
	log.Printf("Go arcade %s: all six games and exploration; listen %s", c.AppVersion, *addr)
	if err = server.ListenAndServe(); err != nil && err != http.ErrServerClosed {
		log.Fatal(err)
	}
}

// Source overrides must be validated/exported before building the sealed release.
func validateRuntimeEnvironment() error {
	for _, name := range []string{"CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS"} {
		if os.Getenv(name) != "" {
			return fmt.Errorf("%s is not supported: Go uses the sealed bundled content", name)
		}
	}
	if accountsEnabled() && os.Getenv("CAT_DATABASE_URL") == "" && os.Getenv("DATABASE_URL") == "" {
		return fmt.Errorf("CAT_ACCOUNTS_ENABLED requires CAT_DATABASE_URL")
	}
	if limit, defined := os.LookupEnv("CAT_MAX_REQUEST_BYTES"); defined {
		cfg, err := session.ParseConfig(nil, &limit)
		if err != nil || cfg.MaxSessions != 65536 {
			return fmt.Errorf("CAT_MAX_REQUEST_BYTES must retain the 65536-byte budget")
		}
	}
	optional := func(name string) *string {
		if value, ok := os.LookupEnv(name); ok {
			return &value
		}
		return nil
	}
	_, err := session.ParseConfig(optional("CAT_SESSION_TTL_SECONDS"), optional("CAT_MAX_SESSIONS_PER_GAME"))
	return err
}

func replayRequests(handler http.Handler) error {
	scanner := bufio.NewScanner(os.Stdin)
	scanner.Buffer(make([]byte, 4096), 1024*1024)
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	for scanner.Scan() {
		input, err := decodeReplayInput(scanner.Bytes())
		if err != nil {
			return err
		}
		request := httptest.NewRequest(input.Method, input.Path, strings.NewReader(input.Body))
		for k, v := range input.Headers {
			request.Header.Set(k, v)
		}
		response := httptest.NewRecorder()
		start := time.Now()
		handler.ServeHTTP(response, request)
		elapsed := time.Since(start).Nanoseconds()
		var body any
		if response.Body.Len() > 0 {
			decoder := json.NewDecoder(bytes.NewReader(response.Body.Bytes()))
			decoder.UseNumber()
			if err := decoder.Decode(&body); err != nil {
				return err
			}
		}
		if err := enc.Encode(map[string]any{"status": response.Code, "body": body, "duration_ns": elapsed}); err != nil {
			return err
		}
	}
	return scanner.Err()
}
