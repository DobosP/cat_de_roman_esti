package hopcli

import (
	"context"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestHealthOnlyFallbackNeverSwallowsContentRefusal(t *testing.T) {
	for _, unhealthy := range []bool{true, false} {
		t.Run(map[bool]string{true: "health-fallback", false: "content-refusal"}[unhealthy], func(t *testing.T) {
			s := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
				if r.URL.Path == "/v1/health" {
					if unhealthy {
						w.WriteHeader(503)
					} else {
						w.Write([]byte(`{"ok":true}`))
					}
					return
				}
				w.Write([]byte(`{"available":false,"records":[]}`))
			}))
			defer s.Close()
			c, _ := roeduclient.New(s.URL, "", roeduclient.DefaultLimits())
			b, fallback, err := LoadOnline(context.Background(), c, "../../../cat_de_roman_esti/fixtures/kg_sample.json", "", "easy")
			if unhealthy {
				if err != nil || !fallback || len(b.Puzzles) != 180 {
					t.Fatal("health fallback lost", err)
				}
			} else if err == nil || fallback || b != nil {
				t.Fatal("content refusal swallowed")
			}
		})
	}
}
