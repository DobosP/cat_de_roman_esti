package main

import (
	"bytes"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"time"
)

const wiki = "https://ro.wiktionary.org"
const rawGit = "https://raw.githubusercontent.com"
const policy = "https://foundation.wikimedia.org"

type fakeTransport func(*http.Request) (*http.Response, error)

func (f fakeTransport) RoundTrip(req *http.Request) (*http.Response, error) { return f(req) }

type requestLog struct {
	url, method, agent string
	at                 time.Time
}

func setup(t *testing.T, reply fakeTransport) (*client, *[]requestLog, *time.Time) {
	t.Helper()
	now := time.Date(2026, 11, 13, 12, 0, 0, 0, time.UTC)
	var sent []requestLog
	httpClient := fakeTransport(func(req *http.Request) (*http.Response, error) {
		sent = append(sent, requestLog{req.URL.String(), req.Method, req.UserAgent(), now})
		return reply(req)
	})
	return &client{
		cache: t.TempDir(), run: "pilot", role: "factual", fetcher: "review-thread-1",
		http: httpClient, now: func() time.Time { return now },
		sleep: func(delay time.Duration) { now = now.Add(delay) },
	}, &sent, &now
}

func response(status int, body string, headers ...string) (*http.Response, error) {
	result := &http.Response{StatusCode: status, Header: http.Header{}, Body: io.NopCloser(strings.NewReader(body))}
	for i := 0; i < len(headers); i += 2 {
		result.Header.Add(headers[i], headers[i+1])
	}
	return result, nil
}

func code(t *testing.T, err error, expected string) refusal {
	t.Helper()
	var problem refusal
	if !errors.As(err, &problem) || problem.Code != expected {
		t.Fatalf("error = %#v, want code %q", err, expected)
	}
	return problem
}

func TestCachePreservesFirstFetcherAndChecksIntegrity(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		if req.URL.Path == "/robots.txt" {
			return response(200, "User-Agent: *\nCrawl-delay: 17.5\n")
		}
		return response(200, "inflection table")
	})
	address := wiki + "/wiki/mas%C4%83"
	got, err := c.get(address)
	if err != nil {
		t.Fatal(err)
	}
	if got.FetchedByRole != "factual" || got.FirstFetcher != "review-thread-1" || got.SHA256 != hash([]byte("inflection table")) {
		t.Fatalf("receipt = %+v", got)
	}
	if len(*sent) != 2 || (*sent)[1].at.Sub((*sent)[0].at) != 17500*time.Millisecond {
		t.Fatalf("requests = %+v", *sent)
	}
	for _, req := range *sent {
		if req.method != "GET" || req.agent != userAgent {
			t.Fatalf("request = %+v", req)
		}
	}
	c.role, c.fetcher, c.cacheOnly = "quality", "review-thread-2", true
	again, err := c.get(address)
	if err != nil || again.FetchedByRole != got.FetchedByRole || again.FirstFetcher != got.FirstFetcher ||
		again.FetchedAt != got.FetchedAt || len(*sent) != 2 {
		t.Fatalf("cached receipt = %+v, error %v, requests %+v", again, err, *sent)
	}
	if err := os.WriteFile(filepath.Join(c.cache, got.SHA256+".body"), []byte("different body"), 0600); err != nil {
		t.Fatal(err)
	}
	_, err = c.get(address)
	code(t, err, "cache_integrity")
	if len(*sent) != 2 {
		t.Fatalf("corruption was fetched again: %+v", *sent)
	}
}

func TestLegacyReceiptsKeepProvenanceAndCannotAddHosts(t *testing.T) {
	c, sent, _ := setup(t, func(*http.Request) (*http.Response, error) {
		t.Fatal("legacy cache test attempted a request")
		return nil, nil
	})
	c.legacy, c.cacheOnly = t.TempDir(), true
	for address, body := range map[string]string{
		wiki + "/robots.txt": "User-agent: *\n", wiki + "/wiki/mas%C4%83": "legacy content",
		"https://dexonline.ro/definitie/masa": "excluded legacy content",
	} {
		role := "factual"
		if strings.HasSuffix(address, "/robots.txt") {
			role = "policy"
		}
		digest := hash([]byte(body))
		legacyShape := map[string]any{
			"url": address, "sha256": digest, "fetched_by_role": role, "bytes": len(body),
			"status": 200, "fetched_at": 1794179871.5224624,
			"headers": map[string]string{"content-type": "text/plain", "content-signal": "", "retry-after": ""},
		}
		if err := os.WriteFile(filepath.Join(c.legacy, digest+".body"), []byte(body), 0600); err != nil {
			t.Fatal(err)
		}
		if err := writeJSON(filepath.Join(c.legacy, receiptName(address)), legacyShape); err != nil {
			t.Fatal(err)
		}
	}
	rec, err := c.get(wiki + "/wiki/mas%C4%83")
	if err != nil || rec.Origin != "legacy" || rec.FirstOrigin != "legacy" || rec.FetchedByRole != "factual" || rec.FirstFetcher != "" ||
		rec.FetchedAt != 1794179871.5224624 {
		t.Fatalf("legacy receipt = %+v, error %v", rec, err)
	}
	_, err = c.get("https://dexonline.ro/definitie/masa")
	code(t, err, "url_denied")
	if len(*sent) != 0 {
		t.Fatalf("requests = %+v", *sent)
	}
}

func TestScopeAndLocalConflict(t *testing.T) {
	c, sent, _ := setup(t, func(*http.Request) (*http.Response, error) {
		return nil, errors.New("TLS handshake could not be established")
	})
	for _, address := range []string{
		"http://ro.wikipedia.org/wiki/A", "https://ro.wikipedia.org:443/wiki/A",
		"https://user@ro.wikipedia.org/wiki/A", "https://ro.wikipedia.org.evil.test/wiki/A",
		"https://127.0.0.1:8077/api", "https://ro.wikipedia.org/wiki/A#part",
		"https://ro.wikipedia.org/wiki/%2e%2e/a", "https://ro.wikipedia.org/wiki/A%252FB",
		"https://ro.wikipedia.org/wiki/a%2fb", rawGit + "/other/FrequencyWords/master/ro.txt",
		rawGit + "/hermitdave/FrequencyWords/%2e%2e/ro.txt",
		rawGit + "/hermitdave/FrequencyWords/master/ro.txt?ignored=1",
	} {
		_, err := c.get(address)
		code(t, err, "url_denied")
	}
	_, err := c.get(policy + "/wiki/Policy:Terms_of_Use")
	code(t, err, "policy_only")
	c.role = "policy"
	_, err = c.get(policy + "/wiki/Random")
	code(t, err, "policy_only")
	_, err = c.get("http://localhost:8077/api")
	code(t, err, "localhost_protocol_conflict")
	_, err = c.get("https://localhost:8077/api")
	code(t, err, "localhost_protocol_conflict")
	if len(*sent) != 0 {
		t.Fatalf("denied URLs were requested: %+v", *sent)
	}
	c.run = "pilot-next"
	_, err = c.get("https://localhost:8077/api")
	code(t, err, "localhost_protocol_conflict")
	if len(*sent) != 1 || (*sent)[0].url != "https://localhost:8077/robots.txt" {
		t.Fatalf("local HTTPS failure attempted fallback: %+v", *sent)
	}
}

func TestRobotsPathRefusalDoesNotDropHost(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		if req.URL.Path == "/robots.txt" {
			return response(200, "User-agent: *\nDisallow: /priv*\nAllow: /private/read$\nDisallow: /wiki/%52omania\n")
		}
		return response(200, "ok")
	})
	for _, address := range []string{"/private", "/private/subpath", "/private/read?secret=1", "/wiki/Romania"} {
		_, err := c.get(wiki + address)
		code(t, err, "robots_path_disallowed")
	}
	for _, address := range []string{"/private/read", "/public"} {
		if _, err := c.get(wiki + address); err != nil {
			t.Fatal(err)
		}
	}
	h, err := c.openHost("ro.wiktionary.org")
	if err != nil || len(h.state.Denials) != 0 || len(*sent) != 3 {
		t.Fatalf("host state = %+v, error = %v, requests = %+v", h, err, *sent)
	}
}

func TestHostRefusalsDeduplicatePerRun(t *testing.T) {
	for _, test := range []struct {
		name, robots, reason string
		status               int
		headers              []string
	}{
		{"signal in robots", "User-agent: *\nContent-Signal: ai-input=yes", "content_signal", 200, nil},
		{"AI group", "User-agent: GPTBot\nDisallow: /training", "ai_crawler_group", 200, nil},
		{"crawler block", "", "crawler_block", 403, nil},
		{"signal header", "", "content_signal", 200, []string{"Content-Signal", ""}},
		{"AI header", "", "crawler_block", 200, []string{"X-Robots-Tag", "noai"}},
	} {
		t.Run(test.name, func(t *testing.T) {
			c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
				if req.URL.Path == "/robots.txt" {
					return response(200, test.robots)
				}
				if req.URL.Host == "ro.wikipedia.org" {
					return response(200, "ok")
				}
				return response(test.status, "unavailable", test.headers...)
			})
			_, err := c.get(wiki + "/wiki/A")
			code(t, err, test.reason)
			count := len(*sent)
			_, err = c.get(wiki + "/wiki/B")
			code(t, err, test.reason)
			h, err := c.openHost("ro.wiktionary.org")
			if err != nil || len(h.state.Denials) != 1 || len(*sent) != count ||
				h.state.Denials[c.run].Code != test.reason {
				t.Fatalf("host state = %+v, error = %v, requests = %+v", h, err, *sent)
			}
			if test.robots == "" {
				if _, err := c.get("https://ro.wikipedia.org/wiki/A"); err != nil {
					t.Fatal(err)
				}
				c.run = "next"
				if _, err := c.get(wiki + "/robots.txt"); err != nil {
					t.Fatal(err)
				}
			}
		})
	}
}

func TestPolicyTermsReceiptParksHost(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		if req.URL.Path == "/robots.txt" {
			return response(404, "not found")
		}
		return response(200, "<title>Terms of Use</title>")
	})
	c.role = "policy"
	rec, err := c.get(policy + "/wiki/Policy:Terms_of_Use/ro")
	if err != nil || rec.FetchedByRole != "policy" || len(*sent) != 2 {
		t.Fatalf("receipt = %+v, error %v, requests %+v", rec, err, *sent)
	}
	_, err = c.get(policy + "/wiki/Policy:Privacy_Policy")
	code(t, err, "terms_page")
	c.role = "factual"
	_, err = c.get("https://ro.wikipedia.org/wiki/Romania")
	code(t, err, "terms_page")
}

func TestRedirectsCacheEachResponseAndStayOnExactHost(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		switch req.URL.Path {
		case "/robots.txt":
			return response(200, "User-agent: *\nDisallow: /private\n")
		case "/wiki/inside":
			return response(302, "redirect", "Location", "/wiki/dest")
		case "/wiki/outside":
			return response(302, "redirect", "Location", "https://ro.wikipedia.org/wiki/dest")
		case "/wiki/plaintext":
			return response(302, "redirect", "Location", "http://ro.wiktionary.org/wiki/dest")
		case "/wiki/malformed":
			return response(302, "redirect", "Location", "%z")
		case "/wiki/robot":
			return response(302, "redirect", "Location", "/private/info")
		default:
			return response(200, "destination")
		}
	})
	rec, err := c.get(wiki + "/wiki/inside")
	if err != nil || rec.URL != wiki+"/wiki/dest" || len(*sent) != 3 {
		t.Fatalf("receipt = %+v, error %v, requests %+v", rec, err, *sent)
	}
	for path, reason := range map[string]string{
		"/wiki/outside": "redirect_denied", "/wiki/plaintext": "redirect_denied", "/wiki/malformed": "redirect_denied", "/wiki/robot": "robots_path_disallowed",
	} {
		before := len(*sent)
		_, err := c.get(wiki + path)
		code(t, err, reason)
		_, err = c.get(wiki + path)
		code(t, err, reason)
		if len(*sent) != before+1 {
			t.Fatalf("unexpected redirect request: %+v", *sent)
		}
	}
	c.cacheOnly = true
	if _, err := c.get(wiki + "/wiki/inside"); err != nil {
		t.Fatal(err)
	}
}

func TestWikimediaDailyLimitAndBareWikidata(t *testing.T) {
	c, sent, now := setup(t, func(req *http.Request) (*http.Response, error) {
		return response(200, "")
	})
	for i := range 19 {
		if _, err := c.get(fmt.Sprintf("https://wikidata.org/wiki/Q%d", i)); err != nil {
			t.Fatal(err)
		}
	}
	_, err := c.get("https://www.wikidata.org/wiki/Q21")
	p := code(t, err, "daily_read_cap")
	if len(*sent) != 20 || p.RetryAt == nil || p.RetryAt.Hour() != 0 {
		t.Fatalf("requests = %+v, cap = %+v", *sent, p)
	}
	for i, req := range *sent {
		if !strings.HasPrefix(req.url, "https://www.wikidata.org/") ||
			i > 0 && req.at.Sub((*sent)[i-1].at) != 10*time.Second {
			t.Fatalf("request = %+v", req)
		}
	}
	if _, err := c.get("https://www.wikidata.org/wiki/Q0"); err != nil {
		t.Fatal(err)
	}
	*now = *p.RetryAt
	if _, err := c.get("https://www.wikidata.org/wiki/Q21"); err != nil {
		t.Fatal(err)
	}
}

func TestBreakerRetryPreservesFirstFetcher(t *testing.T) {
	for _, status := range []int{429, 503} {
		t.Run(fmt.Sprint(status), func(t *testing.T) {
			count := 0
			c, sent, now := setup(t, func(req *http.Request) (*http.Response, error) {
				if req.URL.Path == "/robots.txt" {
					return response(404, "absent")
				}
				count++
				if count == 1 {
					return response(status, "temporary", "Retry-After", "7200")
				}
				return response(200, "ready")
			})
			address := rawGit + "/hermitdave/FrequencyWords/master/LICENSE"
			_, err := c.get(address)
			problem := code(t, err, "host_parked")
			if problem.RetryAt == nil || problem.RetryAt.Sub(*now) != 2*time.Hour {
				t.Fatalf("breaker = %+v", problem)
			}
			c.run, c.role, c.fetcher = "next", "quality", "review-thread-2"
			*now = now.Add(time.Hour)
			_, err = c.get(address)
			code(t, err, "host_parked")
			if len(*sent) != 2 {
				t.Fatalf("request made during breaker: %+v", *sent)
			}
			*now = *problem.RetryAt
			rec, err := c.get(address)
			if err != nil || rec.FetchedByRole != "factual" || rec.FirstFetcher != "review-thread-1" ||
				rec.AttemptRole != "quality" || rec.AttemptID != "review-thread-2" || rec.Status != 200 {
				t.Fatalf("receipt = %+v, error %v", rec, err)
			}
			attempts, err := filepath.Glob(filepath.Join(c.cache, "*.response.json"))
			if err != nil || len(attempts) != 3 {
				t.Fatalf("retained attempts = %v, error %v", attempts, err)
			}
		})
	}
}

func TestRetryAfterFloorAndHTTPDate(t *testing.T) {
	at := time.Date(2026, 11, 13, 0, 0, 0, 0, time.UTC)
	for header, want := range map[string]time.Duration{
		"": time.Hour, "12": time.Hour, "garbage": time.Hour, "-12": time.Hour,
		at.Add(2 * time.Hour).Format(http.TimeFormat): 2 * time.Hour,
		"18446744073709551616":                        time.Duration(1<<63-1) / time.Second * time.Second,
	} {
		if got := retryUntil(header, at).Sub(at); got != want {
			t.Fatalf("Retry-After %q delay = %v, want %v", header, got, want)
		}
	}
}

func TestBoundedBodyAndExclusiveCacheLock(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		if req.URL.Path == "/robots.txt" {
			return response(410, "")
		}
		return &http.Response{
			StatusCode: 200, Body: io.NopCloser(bytes.NewReader(make([]byte, maxBody+1))), Header: http.Header{},
		}, nil
	})
	unlock, err := lockCache(c.cache)
	if err != nil {
		t.Fatal(err)
	}
	_, err = lockCache(c.cache)
	code(t, err, "cache_busy")
	if err := unlock(); err != nil {
		t.Fatal(err)
	}
	_, err = c.get(wiki + "/wiki/A")
	code(t, err, "incomplete_body")
	_, err = c.get(wiki + "/wiki/A")
	code(t, err, "incomplete_body")
	if len(*sent) != 2 {
		t.Fatalf("truncated response requested again: %+v", *sent)
	}
}

func TestLegacyTransientCannotBecomeReviewerFirst(t *testing.T) {
	c, _, now := setup(t, func(req *http.Request) (*http.Response, error) {
		if req.URL.Path == "/robots.txt" {
			return response(404, "absent")
		}
		return response(200, "ready")
	})
	c.legacy = t.TempDir()
	address := wiki + "/wiki/First"
	body := []byte("legacy rate limit")
	old := receipt{
		URL: address, FetchedByRole: "author", FetchedAt: epoch(now.Add(-2 * time.Hour)),
		SHA256: hash(body), Bytes: len(body), Status: 429, Headers: map[string]string{},
	}
	if err := os.WriteFile(filepath.Join(c.legacy, old.SHA256+".body"), body, 0600); err != nil {
		t.Fatal(err)
	}
	if err := writeJSON(filepath.Join(c.legacy, receiptName(address)), old); err != nil {
		t.Fatal(err)
	}
	for range 2 {
		rec, err := c.get(address)
		if err != nil || rec.Origin != "v5" || rec.FirstOrigin != "legacy" ||
			rec.FetchedByRole != "author" || rec.FetchedAt != old.FetchedAt ||
			rec.AttemptRole != "factual" || rec.FirstFetcher != "" {
			t.Fatalf("receipt = %+v, error %v", rec, err)
		}
	}
}

func interruptCommit(c *client, address string, afterPointer bool) error {
	injected := errors.New("injected storage interruption")
	c.persist = func(path string, value any) error {
		if !afterPointer && filepath.Base(path) == receiptName(address) {
			return injected
		}
		if state, ok := value.(hostState); afterPointer && ok && state.Pending == nil {
			return injected
		}
		return writeJSON(path, value)
	}
	return injected
}

func TestInterruptedPointerRecoveryPreservesOriginalReceipt(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		return response(200, req.URL.Path)
	})
	if _, err := c.get(wiki + "/robots.txt"); err != nil {
		t.Fatal(err)
	}
	c.role, c.fetcher = "author", "author-1"
	address := wiki + "/wiki/A"
	injected := interruptCommit(c, address, false)
	if _, err := c.get(address); !errors.Is(err, injected) {
		t.Fatalf("error = %v, want injected interruption", err)
	}
	_, _, exists, err := loadReceipt(c.cache, address, "v5")
	if err != nil || exists {
		t.Fatalf("URL pointer must be absent after interruption: exists %v, error %v", exists, err)
	}
	c.persist = nil
	c.role, c.fetcher = "factual", "reviewer-2"
	got, err := c.get(address)
	if err != nil || got.FetchedByRole != "author" || got.FirstFetcher != "author-1" || len(*sent) != 2 {
		t.Fatalf("receipt = %+v, error %v, sent %+v", got, err, *sent)
	}
}

func TestInterruptedHostRefusalsRecoverBeforeOtherURLs(t *testing.T) {
	for _, test := range []struct {
		name, path, body, reason string
		headers                  []string
	}{
		{"signal", "/wiki/A", "", "content_signal", []string{"Content-Signal", "ai-input=no"}},
		{"terms", "/wiki/A", "<title>Terms of Use</title>", "terms_page", nil},
		{"AI robots", "/robots.txt", "User-agent: GPTBot\nDisallow: /training\n", "ai_crawler_group", nil},
	} {
		t.Run(test.name, func(t *testing.T) {
			c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
				if req.URL.Path == test.path {
					return response(200, test.body, test.headers...)
				}
				return response(200, "")
			})
			if test.path != "/robots.txt" {
				if _, err := c.get(wiki + "/robots.txt"); err != nil {
					t.Fatal(err)
				}
			}
			injected := interruptCommit(c, wiki+test.path, true)
			if _, err := c.get(wiki + test.path); !errors.Is(err, injected) {
				t.Fatalf("error = %v, want injected interruption", err)
			}
			c.persist = nil
			before := len(*sent)
			_, err := c.get(wiki + "/wiki/Other")
			code(t, err, test.reason)
			if len(*sent) != before {
				t.Fatalf("host refused only after another request: %+v", *sent)
			}
			h, err := c.openHost("ro.wiktionary.org")
			if err != nil || h.state.Pending != nil || h.state.Denials[c.run].Code != test.reason {
				t.Fatalf("host state = %+v, error %v", h, err)
			}
		})
	}
}

func TestInterruptedRetryParksCacheHits(t *testing.T) {
	c, sent, now := setup(t, func(req *http.Request) (*http.Response, error) {
		if req.URL.Path == "/wiki/Slow" {
			return response(429, "", "Retry-After", "7200")
		}
		return response(200, "")
	})
	if _, err := c.get(wiki + "/wiki/Cached"); err != nil {
		t.Fatal(err)
	}
	injected := interruptCommit(c, wiki+"/wiki/Slow", false)
	if _, err := c.get(wiki + "/wiki/Slow"); !errors.Is(err, injected) {
		t.Fatalf("error = %v, want injected interruption", err)
	}
	c.persist = nil
	c.cacheOnly = true
	_, err := c.get(wiki + "/wiki/Cached")
	why := code(t, err, "host_parked")
	if why.RetryAt == nil || why.RetryAt.Sub(*now) != 2*time.Hour || len(*sent) != 3 {
		t.Fatalf("retry = %+v, sent %+v", why, *sent)
	}
	*now = *why.RetryAt
	if _, err := c.get(wiki + "/wiki/Cached"); err != nil || len(*sent) != 3 {
		t.Fatalf("cached read error = %v, sent %+v", err, *sent)
	}
}

func TestInterruptedRequestWithNoReceiptParksOnlyAffectedHost(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		return response(200, "")
	})
	h, err := c.openHost("ro.wiktionary.org")
	if err != nil {
		t.Fatal(err)
	}
	if err := h.reserve(wiki+"/wiki/Interrupted", "author"); err != nil {
		t.Fatal(err)
	}
	_, err = c.get(wiki + "/wiki/Other")
	code(t, err, "source_recovery_required")
	if _, err := c.get("https://ro.wikipedia.org/wiki/Other"); err != nil {
		t.Fatal(err)
	}
	for _, req := range *sent {
		if !strings.HasPrefix(req.url, "https://ro.wikipedia.org/") {
			t.Fatalf("interrupted host retried: %+v", *sent)
		}
	}
}

func TestCachePathRejectsNonexistentDescendantOfLegacyAlias(t *testing.T) {
	root := t.TempDir()
	legacy := filepath.Join(root, "legacy")
	if err := os.Mkdir(legacy, 0700); err != nil {
		t.Fatal(err)
	}
	alias := filepath.Join(root, "alias")
	if err := os.Symlink(legacy, alias); err != nil {
		t.Skipf("directory symlinks unavailable: %v", err)
	}
	err := run([]string{
		"--cache", filepath.Join(alias, "new", "subdir"), "--legacy-cache", legacy,
		"--run", "pilot", "--role", "script", "--fetcher", "test", "--owner-queue",
	})
	code(t, err, "usage")
	if _, err := os.Stat(filepath.Join(legacy, "new")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("legacy cache was modified: %v", err)
	}
}

func TestOwnerQueueIncludesRecoveryAndUnaffectedHosts(t *testing.T) {
	c, sent, _ := setup(t, func(*http.Request) (*http.Response, error) {
		t.Fatal("queue must not make network requests")
		return nil, nil
	})
	interrupted, err := c.openHost("ro.wikipedia.org")
	if err != nil {
		t.Fatal(err)
	}
	// An existing denial on this host should not duplicate its recovery entry.
	if _, err := interrupted.record(stop("policy_refusal", "earlier policy notice")); err != nil {
		t.Fatal(err)
	}
	if err := interrupted.reserve("https://ro.wikipedia.org/wiki/Interrupted", "author"); err != nil {
		t.Fatal(err)
	}
	unaffected, err := c.openHost("ro.wiktionary.org")
	if err != nil {
		t.Fatal(err)
	}
	if _, err := unaffected.record(stop("policy_refusal", "terms reviewed")); err != nil {
		t.Fatal(err)
	}
	for range 2 {
		lines, err := c.ownerQueue()
		if err != nil || len(lines) != 2 ||
			lines[0].Host != "ro.wikipedia.org" || lines[0].Run != c.run ||
			lines[0].Code != "source_recovery_required" || !lines[0].At.Equal(interrupted.state.Pending.Started) ||
			lines[1].Host != "ro.wiktionary.org" || lines[1].Code != "policy_refusal" {
			t.Fatalf("queue = %+v, error %v", lines, err)
		}
	}
	if len(*sent) != 0 {
		t.Fatalf("queue made requests: %+v", *sent)
	}
}

func TestCachePathRejectsCaseAliasOnCaseInsensitiveVolume(t *testing.T) {
	root := t.TempDir()
	legacy := filepath.Join(root, "Legacy")
	if err := os.Mkdir(legacy, 0700); err != nil {
		t.Fatal(err)
	}
	variant := filepath.Join(root, "legacy")
	if _, err := os.Stat(variant); errors.Is(err, os.ErrNotExist) {
		t.Skip("case-sensitive filesystem")
	} else if err != nil {
		t.Fatal(err)
	}
	err := run([]string{
		"--cache", filepath.Join(variant, "new"), "--legacy-cache", legacy,
		"--run", "pilot", "--role", "script", "--fetcher", "test", "--owner-queue",
	})
	code(t, err, "usage")
	if _, err := os.Stat(filepath.Join(legacy, "new")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("legacy cache was modified: %v", err)
	}
}
