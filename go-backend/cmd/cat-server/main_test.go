package main

import (
	"io"
	"net/http"
	"net/url"
	"strings"
	"testing"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
)

type transportFunc func(*http.Request) (*http.Response, error)

func (f transportFunc) RoundTrip(r *http.Request) (*http.Response, error) { return f(r) }

func TestUpstreamMustBeAnonymousAndContentEquivalent(t *testing.T) {
	c, err := content.Load()
	if err != nil {
		t.Fatal(err)
	}
	target, _ := url.Parse("http://127.0.0.1:8000")
	original := http.DefaultTransport
	defer func() { http.DefaultTransport = original }()
	for _, tc := range []struct {
		name, me, manifest string
		valid              bool
	}{
		{"valid", `{"accounts_enabled":false,"authenticated":false,"user":null}`, `{"content_hash":"` + c.Manifest["content_hash"].(string) + `","build_version":"` + c.Manifest["build_version"].(string) + `"}`, true},
		{"accounts", `{"accounts_enabled":true}`, `{}`, false},
		{"incomplete", `{"accounts_enabled":false}`, `{}`, false},
		{"drift", `{"accounts_enabled":false,"authenticated":false,"user":null}`, `{"content_hash":"other"}`, false},
	} {
		t.Run(tc.name, func(t *testing.T) {
			http.DefaultTransport = transportFunc(func(r *http.Request) (*http.Response, error) {
				body := tc.me
				if r.URL.Path == "/api/manifest" {
					body = tc.manifest
				}
				return &http.Response{StatusCode: 200, Header: make(http.Header), Body: io.NopCloser(strings.NewReader(body))}, nil
			})
			if err := checkUpstream(target, c); (err == nil) != tc.valid {
				t.Fatalf("upstream gate: %v", err)
			}
		})
	}
}
