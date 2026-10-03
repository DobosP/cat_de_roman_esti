// cat-server serves the complete anonymous arcade. Default binding is loopback.
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
	"unicode"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/session"
)

func main() {
	addr := flag.String("listen", "127.0.0.1:8081", "HTTP bind address")
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

// Deployment supports the anonymous compiled-data runtime. Reject activation
// of dormant features rather than silently proxying requests to another runtime.
func validateRuntimeEnvironment() error {
	for _, name := range []string{"CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS"} {
		if os.Getenv(name) != "" {
			return fmt.Errorf("%s is not supported: Go uses the sealed bundled content", name)
		}
	}
	for _, value := range []string{"1", "true", "yes", "on"} {
		if strings.ToLower(strings.TrimFunc(os.Getenv("CAT_ACCOUNTS_ENABLED"), func(r rune) bool { return unicode.IsSpace(r) || r >= 0x1c && r <= 0x1f })) == value {
			return fmt.Errorf("CAT_ACCOUNTS_ENABLED must remain off for the anonymous Go runtime")
		}
	}
	if os.Getenv("CAT_SUBMISSIONS_DIR") != "" {
		return fmt.Errorf("CAT_SUBMISSIONS_DIR is not supported by the anonymous Go runtime")
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
		var input struct {
			Method  string            `json:"method"`
			Path    string            `json:"path"`
			Body    string            `json:"body"`
			Headers map[string]string `json:"headers"`
		}
		if err := json.Unmarshal(scanner.Bytes(), &input); err != nil {
			return err
		}
		if input.Method == "" {
			input.Method = "GET"
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
