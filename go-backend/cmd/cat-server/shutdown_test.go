package main

import (
	"context"
	"errors"
	"io"
	"net/http"
	"net/http/httptest"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/boardstats"
)

func TestShutdownFlushesStatsAfterHungRequest(t *testing.T) {
	dir := t.TempDir()
	now := func() time.Time { return time.Date(2026, 11, 17, 12, 0, 0, 0, time.UTC) }
	stats, err := boardstats.Open(dir, boardstats.Options{Now: now})
	if err != nil {
		t.Fatal(err)
	}
	t.Cleanup(func() { _ = stats.Close() })
	key := boardstats.Key{RulesVersion: 2, ContentDigest: strings.Repeat("a", 64),
		Day: now().Format(time.DateOnly), Game: "intrusul", BoardID: "shutdown-test"}
	if err := stats.Record(key, boardstats.Loss, 0); err != nil {
		t.Fatal(err)
	}
	entered := make(chan struct{})
	release := make(chan struct{})
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		close(entered)
		<-release // Deliberately ignore request cancellation.
		w.WriteHeader(http.StatusOK)
	}))
	t.Cleanup(server.Close)
	t.Cleanup(func() { close(release) })
	go func() {
		response, err := server.Client().Get(server.URL)
		if err == nil {
			_, _ = io.Copy(io.Discard, response.Body)
			_ = response.Body.Close()
		}
	}()
	select {
	case <-entered:
	case <-time.After(2 * time.Second):
		t.Fatal("test request never entered the handler")
	}
	finished := make(chan error, 1)
	go func() { finished <- shutdownServer(server.Config, stats) }()
	select {
	case err := <-finished:
		if !errors.Is(err, context.DeadlineExceeded) {
			t.Fatalf("hung HTTP request did not exhaust its drain deadline: %v", err)
		}
	case <-time.After(8 * time.Second):
		t.Fatal("HTTP drain consumed the time reserved for the final stats flush")
	}
	path := filepath.Join(dir, "boardstats-"+key.Day+".json")
	if _, err := os.Stat(path); err != nil {
		t.Fatalf("hung handler prevented the final snapshot: %v", err)
	}
	restored, err := boardstats.Open(dir, boardstats.Options{Now: now})
	if err != nil {
		t.Fatalf("shutdown did not release the stats directory: %v", err)
	}
	defer restored.Close()
	for range 99 {
		if err := restored.Record(key, boardstats.Loss, 0); err != nil {
			t.Fatal(err)
		}
	}
	if place, show := restored.Place(key, 0); !show || place.Rounds != 100 {
		t.Fatalf("snapshot lost the terminal round: %+v shown=%t", place, show)
	}
}
