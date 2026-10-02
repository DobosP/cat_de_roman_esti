// cat-server serves the complete anonymous arcade. Default binding is loopback.
package main

import (
	"bufio"
	"bytes"
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"log"
	"net"
	"net/http"
	"net/http/httptest"
	"net/url"
	"os"
	"os/signal"
	"strings"
	"syscall"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/httpapi"
)

func main() {
	addr := flag.String("listen", "127.0.0.1:8081", "HTTP bind address")
	upstream := flag.String("python-upstream", "", "optional anonymous Python backend, numeric loopback HTTP only")
	replay := flag.Bool("replay", false, "offline JSON-lines HTTP request replay on stdin/stdout")
	flag.Parse()
	for _, name := range []string{"CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS"} {
		if os.Getenv(name) != "" {
			log.Fatal("Go backend requires bundled content without source overrides")
		}
	}
	for _, v := range []string{"1", "true", "yes", "on"} {
		if strings.ToLower(strings.TrimSpace(os.Getenv("CAT_ACCOUNTS_ENABLED"))) == v {
			log.Fatal("Go backend requires accounts OFF")
		}
	}
	if os.Getenv("CAT_SUBMISSIONS_DIR") != "" {
		log.Fatal("Go backend does not support CAT_SUBMISSIONS_DIR; use Python for enabled submissions")
	}
	if limit := os.Getenv("CAT_MAX_REQUEST_BYTES"); limit != "" && limit != "65536" {
		log.Fatal("Go backend requires the default CAT_MAX_REQUEST_BYTES budget")
	}
	c, err := content.Load()
	if err != nil {
		log.Fatal(err)
	}
	var target *url.URL
	if *upstream != "" {
		target, err = url.Parse(*upstream)
		if err != nil || target.Scheme != "http" || target.User != nil || !net.ParseIP(target.Hostname()).IsLoopback() || target.RawQuery != "" || target.Fragment != "" || target.Path != "" {
			log.Fatal("Python upstream must be numeric loopback HTTP without credentials/path/query")
		}
		if *replay {
			log.Fatal("replay is offline; Python upstream is unavailable")
		}
		if err = checkUpstream(target, c); err != nil {
			log.Fatal(err)
		}
	}
	handler := httpapi.New(c, target)
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

func checkUpstream(target *url.URL, c *content.Content) error {
	client := &http.Client{Timeout: 5 * time.Second, CheckRedirect: func(r *http.Request, via []*http.Request) error { return http.ErrUseLastResponse }}
	for _, path := range []string{"/api/me", "/api/manifest"} {
		resp, err := client.Get(target.String() + path)
		if err != nil {
			return fmt.Errorf("anonymous upstream probe failed: %w", err)
		}
		var body map[string]any
		err = json.NewDecoder(io.LimitReader(resp.Body, 64*1024)).Decode(&body)
		resp.Body.Close()
		if err != nil || resp.StatusCode != 200 {
			return fmt.Errorf("anonymous upstream probe failed")
		}
		if path == "/api/me" {
			if enabled, ok := body["accounts_enabled"].(bool); !ok || enabled || body["authenticated"] != false || body["user"] != nil {
				return fmt.Errorf("Go backend refuses an accounts-enabled upstream")
			}
		} else {
			if body["content_hash"] != c.Manifest["content_hash"] || body["build_version"] != c.Manifest["build_version"] {
				return fmt.Errorf("Python upstream content differs from the embedded Go export")
			}
		}
	}
	return nil
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
