package main

import (
	"bufio"
	"bytes"
	"crypto/sha1"
	"errors"
	"fmt"
	"io"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"testing"
	"testing/iotest"
	"time"
)

const (
	dumpBase        = "https://dumps.wikimedia.org"
	dumpDir         = "/rowiktionary/20261101/"
	testDumpName    = "rowiktionary-20261101-pages-articles.xml.bz2"
	testArchive     = "BZh9test compressed bytes"
	testArchiveURL  = dumpBase + dumpDir + testDumpName
	testManifestURL = dumpBase + dumpDir + "rowiktionary-20261101-sha1sums.txt"
)

func manifestLine(name, data string) string {
	return fmt.Sprintf("%x  %s\n", sha1.Sum([]byte(data)), name)
}

func mockDump(t *testing.T, archive fakeTransport) (*client, *[]requestLog, *time.Time) {
	t.Helper()
	c, sent, now := setup(t, func(req *http.Request) (*http.Response, error) {
		switch req.URL.String() {
		case dumpBase + "/robots.txt":
			return response(200, "User-Agent: *\nCrawl-delay: 11\n")
		case testManifestURL:
			body := manifestLine(testDumpName, testArchive)
			r, err := response(200, body, "Content-Type", "text/plain")
			r.ContentLength = int64(len(body))
			return r, err
		case testArchiveURL:
			if req.Header.Get("Accept-Encoding") != "identity" {
				t.Fatal("archive GET did not request identity encoding")
			}
			return archive(req)
		default:
			t.Fatalf("unexpected dump request: %s", req.URL)
			return nil, nil
		}
	})
	c.role, c.fetcher = "script", "dump-source"
	return c, sent, now
}

func goodDump(*http.Request) (*http.Response, error) {
	r, err := response(200, testArchive, "Content-Type", "application/x-bzip2")
	r.ContentLength = int64(len(testArchive))
	return r, err
}

func TestDatedDumpURLScope(t *testing.T) {
	for _, target := range []string{
		testArchiveURL, testManifestURL, dumpBase + "/robots.txt",
		dumpBase + "/rowiki/20261101/rowiki-20261101-all-titles-in-ns0.gz",
		dumpBase + "/rowiki/20261101/rowiki-20261101-redirect.sql.gz",
		dumpBase + "/rowiki/20261101/rowiki-20261101-sha1sums.txt",
	} {
		if _, err := admit(target, "script"); err != nil {
			t.Errorf("approved target %s: %v", target, err)
		}
	}
	for _, target := range []string{
		dumpBase, testArchiveURL + "?", testManifestURL + "?x=y",
		dumpBase + "/rowiki/latest/rowiki-latest-redirect.sql.gz",
		dumpBase + "/rowiki/20260230/rowiki-20260230-redirect.sql.gz",
		dumpBase + "/rowiki/20261101/rowiki-20261102-redirect.sql.gz",
		dumpBase + "/rowiki/20261101/rowiktionary-20261101-sha1sums.txt",
		dumpBase + "/rowiki/20261101/rowiki-20261101-pages-articles.xml.bz2",
		dumpBase + "/rowiki/20261101/rowiki-20261101-md5sums.txt",
		dumpBase + "/enwiki/20261101/enwiki-20261101-sha1sums.txt",
		dumpBase + "/rowiktionary/20261101/%72owiktionary-20261101-pages-articles.xml.bz2",
		dumpBase + "/rowiki//20261101/rowiki-20261101-redirect.sql.gz",
		dumpBase + "/rowiki/20261101/../20261101/rowiki-20261101-redirect.sql.gz",
		dumpBase + "/rowiki%2F20261101/rowiki-20261101-redirect.sql.gz",
		dumpBase + "/legal",
	} {
		_, err := admit(target, "script")
		code(t, err, "url_denied")
	}
}

func TestDumpReceiptRevalidatesAcrossRuns(t *testing.T) {
	c, sent, _ := mockDump(t, goodDump)
	manifest := manifestLine(testDumpName, testArchive)
	rec, err := c.get(testArchiveURL)
	if err != nil {
		t.Fatal(err)
	}
	expected := dumpChecksum{URL: testManifestURL, SHA256: hash([]byte(manifest)), SHA1: fmt.Sprintf("%x", sha1.Sum([]byte(testArchive)))}
	if rec.DumpChecksum == nil || *rec.DumpChecksum != expected || rec.SHA256 != hash([]byte(testArchive)) ||
		rec.FetchedByRole != "script" || rec.FirstFetcher != "dump-source" || rec.Bytes != len(testArchive) {
		t.Fatalf("archive receipt: %+v", rec)
	}
	path := filepath.Join(c.cache, rec.SHA256+".dump")
	raw, err := os.ReadFile(path)
	if err != nil || string(raw) != testArchive {
		t.Fatalf("archive body %q: %v", raw, err)
	}
	if len(*sent) != 3 || (*sent)[0].url != dumpBase+"/robots.txt" ||
		(*sent)[1].url != testManifestURL || (*sent)[2].url != testArchiveURL {
		t.Fatalf("request order: %+v", *sent)
	}
	for i, req := range *sent {
		if req.method != "GET" || req.agent != userAgent || i > 0 && req.at.Sub((*sent)[i-1].at) != 11*time.Second {
			t.Fatalf("requests: %+v", *sent)
		}
	}
	c.cacheOnly, c.role, c.fetcher, c.run = true, "factual", "reviewer", "next-run"
	again, err := c.get(testArchiveURL)
	if err != nil || again.FirstFetcher != rec.FirstFetcher || again.FetchedAt != rec.FetchedAt || len(*sent) != 3 {
		t.Fatalf("cache hit: %+v, %v, requests: %+v", again, err, *sent)
	}

	// Even when edited metadata points at a matching SHA-256 and size, the
	// bytes must agree with the real, separately cached manifest entry.
	rec.SHA256 = hash([]byte("BZh9different"))
	rec.Bytes = len("BZh9different")
	rec.DumpChecksum.SHA1 = fmt.Sprintf("%x", sha1.Sum([]byte("BZh9different")))
	if err := os.WriteFile(filepath.Join(c.cache, rec.SHA256+".dump"), []byte("BZh9different"), 0600); err != nil {
		t.Fatal(err)
	}
	receiptPath := filepath.Join(c.cache, receiptName(testArchiveURL))
	if err := writeJSON(receiptPath, rec); err != nil {
		t.Fatal(err)
	}
	_, err = c.get(testArchiveURL)
	code(t, err, "cache_integrity")
	rec.DumpChecksum.SHA1 = expected.SHA1
	if err := writeJSON(receiptPath, rec); err != nil {
		t.Fatal(err)
	}
	_, err = c.get(testArchiveURL)
	code(t, err, "cache_integrity")
	if len(*sent) != 3 {
		t.Fatalf("cache corruption retried the network: %+v", *sent)
	}
}

func TestCachedDumpRequiresManifestAndOriginalBytes(t *testing.T) {
	for _, entry := range []string{"archive", "archive receipt", "manifest body", "manifest receipt"} {
		t.Run(entry, func(t *testing.T) {
			c, sent, _ := mockDump(t, goodDump)
			rec, err := c.get(testArchiveURL)
			if err != nil {
				t.Fatal(err)
			}
			path := filepath.Join(c.cache, rec.SHA256+".dump")
			switch entry {
			case "archive receipt":
				path = filepath.Join(c.cache, receiptName(testArchiveURL))
			case "manifest body":
				path = filepath.Join(c.cache, rec.DumpChecksum.SHA256+".body")
			case "manifest receipt":
				path = filepath.Join(c.cache, receiptName(testManifestURL))
			}
			if err := os.Remove(path); err != nil {
				t.Fatal(err)
			}
			_, err = c.get(testArchiveURL)
			code(t, err, "cache_integrity")
			if len(*sent) != 3 {
				t.Fatalf("missing cache entry caused a new GET: %+v", *sent)
			}
		})
	}
}

func TestDumpRequiresExactManifestEntry(t *testing.T) {
	for _, tc := range []struct {
		name, body, failure string
	}{
		{"missing", manifestLine(testDumpName+".extra", testArchive), "dump_checksum_missing"},
		{"different repeat", manifestLine(testDumpName, testArchive) + manifestLine(testDumpName, "different"), "dump_checksum_invalid"},
		{"identical repeat", manifestLine(testDumpName, testArchive) + manifestLine(testDumpName, testArchive), "dump_checksum_invalid"},
		{"malformed", manifestLine(testDumpName, testArchive) + "malformed\n", "dump_checksum_invalid"},
		{"terms", "<title>Terms of Use</title>", "terms_page"},
	} {
		t.Run(tc.name, func(t *testing.T) {
			c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
				switch req.URL.String() {
				case dumpBase + "/robots.txt":
					return response(200, "User-Agent: *\n")
				case testManifestURL:
					r, err := response(200, tc.body)
					r.ContentLength = -1
					return r, err
				default:
					t.Fatalf("unverified dump was requested: %s", req.URL)
					return nil, nil
				}
			})
			c.role = "script"
			for range 2 {
				_, err := c.get(testArchiveURL)
				code(t, err, tc.failure)
			}
			if len(*sent) != 2 {
				t.Fatalf("requests: %+v", *sent)
			}
		})
	}
}

func repeatedSQLManifest() string {
	// Shape of the official 20261101 manifest, with fixture hashes and archive.
	const tag = "rowiktionary-20261101-change_tag.sql.gz"
	const definition = "rowiktionary-20261101-change_tag_def.sql.gz"
	return manifestLine(tag, "first tag") + manifestLine(definition, "first definition") +
		manifestLine(testDumpName, testArchive) +
		manifestLine(tag, "second tag") + manifestLine(definition, "second definition")
}

func TestDumpAllowsRepeatedUnrelatedManifestEntries(t *testing.T) {
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		switch req.URL.String() {
		case dumpBase + "/robots.txt":
			return response(200, "User-Agent: *\n")
		case testManifestURL:
			r, err := response(200, repeatedSQLManifest())
			r.ContentLength = -1
			return r, err
		case testArchiveURL:
			return goodDump(req)
		}
		t.Fatalf("unexpected request: %s", req.URL)
		return nil, nil
	})
	c.role = "script"
	rec, err := c.get(testArchiveURL)
	if err != nil || rec.DumpChecksum == nil || rec.DumpChecksum.SHA1 != fmt.Sprintf("%x", sha1.Sum([]byte(testArchive))) ||
		rec.DumpChecksum.RecoveredOutcomeSHA256 != "" || len(*sent) != 3 {
		t.Fatalf("archive receipt: %+v, requests %+v, error %v", rec, *sent, err)
	}
}

func seedRejectedManifest(t *testing.T, c *client, body string, edit func(*dumpOutcome)) (string, string) {
	t.Helper()
	if _, err := c.get(dumpBase + "/robots.txt"); err != nil {
		t.Fatal(err)
	}
	h, err := c.openHost(dumpHost)
	if err != nil {
		t.Fatal(err)
	}
	if err := h.reserve(testManifestURL, "script"); err != nil {
		t.Fatal(err)
	}
	why := stop("dump_checksum_invalid", legacyManifestDuplicate)
	outcome := dumpOutcome{receipt: receipt{
		URL: testManifestURL, Status: 200, Bytes: len(body), SHA256: hash([]byte(body)),
		FetchedAt: epoch(h.state.LastStart), ReceivedAt: epoch(h.state.LastStart), FetchedByRole: "script",
		Origin: "v5", FirstOrigin: "v5", FirstFetcher: c.fetcher, AttemptRole: "script", AttemptID: c.fetcher,
		Headers: map[string]string{"content-length": fmt.Sprint(len(body)), "content-type": "text/plain"},
	}, Failure: &why}
	if edit != nil {
		edit(&outcome)
	}
	if err := h.saveDumpDiagnostic(outcome.receipt, []byte(body)); err != nil {
		t.Fatal(err)
	}
	path := filepath.Join(c.cache, receiptName(testManifestURL))
	if err := h.store(path, outcome); err != nil {
		t.Fatal(err)
	}
	if err := h.commitDumpOutcome(outcome); err != nil {
		t.Fatal(err)
	}
	return path, h.file
}

func TestDumpReusesCompletedRejectedManifestWithoutAnotherGET(t *testing.T) {
	c, sent, _ := mockDump(t, goodDump)
	manifest := repeatedSQLManifest()
	path, state := seedRejectedManifest(t, c, manifest, nil)
	read := func(path string) []byte {
		t.Helper()
		body, err := os.ReadFile(path)
		if err != nil {
			t.Fatal(err)
		}
		return body
	}
	original, originalState := read(path), read(state)
	originalDigest := hash(bytes.TrimSuffix(original, []byte("\n")))
	c.cacheOnly, c.role, c.fetcher = true, "quality", "quality-reader"
	recovered, err := c.get(testManifestURL)
	if err != nil || recovered.DumpManifestRecoveredOutcomeSHA256 != originalDigest ||
		recovered.SHA256 != hash([]byte(manifest)) || recovered.FirstFetcher != "dump-source" {
		t.Fatalf("recovered manifest: %+v, error %v", recovered, err)
	}
	if !bytes.Equal(original, read(path)) || !bytes.Equal(originalState, read(state)) || len(*sent) != 1 {
		t.Fatalf("offline lookup changed the original history or sent a request: %+v", *sent)
	}
	if _, err := os.Stat(filepath.Join(c.cache, recovered.SHA256+".body")); !errors.Is(err, os.ErrNotExist) {
		t.Fatalf("offline recovery published a manifest body: %v", err)
	}

	c.cacheOnly, c.role = false, "script"
	c.fetcher = "new-archive-fetcher"
	got, err := c.get(testArchiveURL)
	if err != nil || got.DumpChecksum == nil || got.DumpChecksum.RecoveredOutcomeSHA256 != originalDigest {
		t.Fatalf("archive receipt: %+v, error %v", got, err)
	}
	c.cacheOnly, c.role = true, "factual"
	cached, err := c.get(testArchiveURL)
	if err != nil || cached.DumpChecksum == nil || *cached.DumpChecksum != *got.DumpChecksum ||
		len(*sent) != 2 || (*sent)[1].url != testArchiveURL || !bytes.Equal(original, read(path)) {
		t.Fatalf("archive reuse: %+v, requests %+v, error %v", cached, *sent, err)
	}
}

func TestDumpRejectedManifestRecoveryFailsClosed(t *testing.T) {
	for _, tc := range []struct {
		name, body, failure string
		edit                func(*dumpOutcome)
		damageBody          bool
		damageOutcome       bool
	}{
		{name: "different prior failure", failure: "incomplete_body", edit: func(o *dumpOutcome) { o.Failure.Code = "incomplete_body" }},
		{name: "wrong prior message", edit: func(o *dumpOutcome) { o.Failure.Message = "malformed" }},
		{name: "partial diagnostic", edit: func(o *dumpOutcome) { o.BodyProblem = "response body exceeds the retained diagnostic byte limit" }},
		{name: "non-200 response", edit: func(o *dumpOutcome) { o.Status = 206 }},
		{name: "encoded", edit: func(o *dumpOutcome) { o.Headers["content-encoding"] = "gzip" }},
		{name: "range", edit: func(o *dumpOutcome) { o.Headers["content-range"] = "bytes 0-12/24" }},
		{name: "wrong length", edit: func(o *dumpOutcome) { o.Headers["content-length"] = "0" }},
		{name: "policy header", edit: func(o *dumpOutcome) { o.Headers["content-signal-present"] = "true" }},
		{name: "no duplicates", body: manifestLine(testDumpName, testArchive)},
		{name: "malformed after duplicates", body: repeatedSQLManifest() + "malformed\n"},
		{name: "repeated target", body: repeatedSQLManifest() + manifestLine(testDumpName, testArchive)},
		{name: "damaged diagnostic", failure: "cache_integrity", damageBody: true},
		{name: "outcome no longer matches history", failure: "cache_integrity", damageOutcome: true},
	} {
		t.Run(tc.name, func(t *testing.T) {
			c, sent, _ := mockDump(t, goodDump)
			body := tc.body
			if body == "" {
				body = repeatedSQLManifest()
			}
			path, _ := seedRejectedManifest(t, c, body, tc.edit)
			if tc.damageBody {
				path := filepath.Join(c.cache, hash([]byte(body))+".diagnostic")
				if err := os.WriteFile(path, []byte("0"+body[1:]), 0600); err != nil {
					t.Fatal(err)
				}
			}
			if tc.damageOutcome {
				var outcome dumpOutcome
				if found, err := readJSON(path, 512*1024, &outcome); err != nil || !found {
					t.Fatalf("reading original outcome: %v", err)
				}
				outcome.Headers["content-type"] = "application/octet-stream"
				if err := writeJSON(path, outcome); err != nil {
					t.Fatal(err)
				}
			}
			want := tc.failure
			if want == "" {
				want = "dump_checksum_invalid"
			}
			_, err := c.get(testArchiveURL)
			code(t, err, want)
			if len(*sent) != 1 {
				t.Fatalf("invalid recovery triggered a request: %+v", *sent)
			}
		})
	}
}

func TestFailedDumpIsNeverEvidenceOrRetried(t *testing.T) {
	for _, tc := range []struct {
		name, failure string
		reply         fakeTransport
	}{
		{"hash mismatch", "dump_checksum_mismatch", func(*http.Request) (*http.Response, error) {
			r, _ := response(200, "BZh9different")
			r.ContentLength = -1
			return r, nil
		}},
		{"short response", "incomplete_body", func(*http.Request) (*http.Response, error) {
			r, _ := goodDump(nil)
			r.ContentLength++
			return r, nil
		}},
		{"midstream failure", "incomplete_body", func(*http.Request) (*http.Response, error) {
			r, _ := goodDump(nil)
			r.Body = io.NopCloser(io.MultiReader(strings.NewReader("BZh9"), iotest.ErrReader(io.ErrUnexpectedEOF)))
			return r, nil
		}},
		{"oversized response", "incomplete_body", func(*http.Request) (*http.Response, error) {
			r, _ := goodDump(nil)
			r.ContentLength = maxDumpBytes + 1
			return r, nil
		}},
		{"redirect", "redirect_denied", func(*http.Request) (*http.Response, error) {
			return response(302, "", "Location", testArchiveURL)
		}},
		{"partial response", "http_status", func(*http.Request) (*http.Response, error) {
			return response(206, testArchive, "Content-Range", "bytes 0-23/4000")
		}},
		{"reencoded response", "dump_invalid_response", func(*http.Request) (*http.Response, error) {
			return response(200, testArchive, "Content-Encoding", "gzip")
		}},
		{"network failure", "transport_error", func(*http.Request) (*http.Response, error) {
			return nil, errors.New("network failure")
		}},
	} {
		t.Run(tc.name, func(t *testing.T) {
			c, sent, now := mockDump(t, tc.reply)
			_, err := c.get(testArchiveURL)
			code(t, err, tc.failure)
			*now = now.Add(25 * time.Hour)
			c.run = "different-run"
			_, err = c.get(testArchiveURL)
			code(t, err, tc.failure)
			files, err := filepath.Glob(filepath.Join(c.cache, "*.dump*"))
			if err != nil || len(files) != 0 || len(*sent) != 3 {
				t.Fatalf("failed archive files: %v, requests: %+v, error: %v", files, *sent, err)
			}
		})
	}
}

func TestDumpLimitsUnknownContentLengthWhileStreaming(t *testing.T) {
	c, _, _ := mockDump(t, goodDump)
	h := &hostClient{client: c}
	target, err := admit(testArchiveURL, "script")
	if err != nil {
		t.Fatal(err)
	}
	file, _ := datedDump(target)
	file.limit = 5
	_, _, _, why := h.storeDumpPayload(target, receipt{}, file, bufio.NewReader(strings.NewReader(testArchive)), -1, dumpChecksum{})
	code(t, why, "incomplete_body")
	files, err := os.ReadDir(c.cache)
	if err != nil || len(files) != 0 {
		t.Fatalf("oversized stream left files: %v, %v", files, err)
	}
}

func TestDumpRequiresScriptForNetworkAndRobotsForBothFiles(t *testing.T) {
	for _, blocked := range []string{"", testManifestURL, testArchiveURL} {
		t.Run(blocked, func(t *testing.T) {
			c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
				if req.URL.Path != "/robots.txt" {
					t.Fatalf("dump route made a prohibited request: %s", req.URL)
				}
				return response(200, "User-Agent: *\nDisallow: "+strings.TrimPrefix(blocked, dumpBase)+"\n")
			})
			if blocked == "" {
				_, err := c.get(testArchiveURL)
				code(t, err, "dump_script_only")
			} else {
				c.role = "script"
				_, err := c.get(testArchiveURL)
				code(t, err, "robots_path_disallowed")
			}
			if len(*sent) != 1 {
				t.Fatalf("requests: %+v", *sent)
			}
		})
	}
}

func TestDumpPolicyRefusalAndBreakerReuse(t *testing.T) {
	c, sent, now := mockDump(t, func(*http.Request) (*http.Response, error) {
		return response(429, "", "Retry-After", "7200")
	})
	_, err := c.get(testArchiveURL)
	why := code(t, err, "host_parked")
	if why.RetryAt == nil || !why.RetryAt.Equal(now.Add(2*time.Hour)) {
		t.Fatalf("retry time: %+v", why)
	}
	*now = now.Add(3 * time.Hour)
	_, err = c.get(testArchiveURL)
	code(t, err, "http_status")
	if len(*sent) != 3 {
		t.Fatalf("a 429 was retried: %+v", *sent)
	}

	c, sent, _ = mockDump(t, func(*http.Request) (*http.Response, error) {
		return response(200, "", "Content-Signal", "")
	})
	for _, run := range []string{"pilot", "next"} {
		c.run = run
		_, err := c.get(testArchiveURL)
		code(t, err, "content_signal")
		queue, err := c.ownerQueue()
		if err != nil || len(queue) != 1 || queue[0].Run != run || queue[0].Code != "content_signal" {
			t.Fatalf("queue: %+v, %v", queue, err)
		}
	}
	if len(*sent) != 3 {
		t.Fatalf("a refused dump was retried: %+v", *sent)
	}
}

func TestDumpRequestsCountAgainstSharedDailyLimit(t *testing.T) {
	c, sent, _ := mockDump(t, goodDump)
	if _, err := c.get(dumpBase + "/robots.txt"); err != nil {
		t.Fatal(err)
	}
	h, err := c.openHost(dumpHost)
	if err != nil {
		t.Fatal(err)
	}
	h.state.Reads = 19
	if err := h.store(h.file, h.state); err != nil {
		t.Fatal(err)
	}
	_, err = c.get(testArchiveURL)
	code(t, err, "daily_read_cap")
	if len(*sent) != 2 || (*sent)[1].url != testManifestURL {
		t.Fatalf("requests: %+v", *sent)
	}
}

func TestDumpJournalRecoversVerifiedArchiveOrParks(t *testing.T) {
	for _, persistOutcome := range []bool{true, false} {
		t.Run(fmt.Sprint(persistOutcome), func(t *testing.T) {
			c, sent, _ := mockDump(t, goodDump)
			injected := errors.New("interrupted write")
			c.persist = func(path string, value any) error {
				switch state := value.(type) {
				case hostState:
					if persistOutcome && state.Pending == nil && len(*sent) == 3 {
						return injected
					}
				case dumpOutcome:
					if !persistOutcome && state.URL == testArchiveURL {
						return injected
					}
				}
				return writeJSON(path, value)
			}
			if _, err := c.get(testArchiveURL); !errors.Is(err, injected) {
				t.Fatalf("interrupted get: %v", err)
			}
			c.persist = nil
			rec, err := c.get(testArchiveURL)
			if persistOutcome {
				if err != nil || rec.FirstFetcher != "dump-source" || rec.DumpChecksum == nil {
					t.Fatalf("recovered archive: %+v, %v", rec, err)
				}
			} else {
				code(t, err, "source_recovery_required")
			}
			if len(*sent) != 3 {
				t.Fatalf("recovery issued requests: %+v", *sent)
			}
		})
	}
}

func TestDumpRefusesMislabeledPolicyMarkup(t *testing.T) {
	for _, tc := range []struct {
		title, mime, refusal string
	}{
		{"Terms of Use", "", "terms_page"},
		{"Terms of Use", "application/x-bzip2", "terms_page"},
		{"Crawler Access Denied", "", "crawler_block"},
		{"Access Denied", "application/octet-stream", "crawler_block"},
		{"Just a Moment", "text/html", "crawler_block"},
	} {
		t.Run(tc.title+"/"+tc.mime, func(t *testing.T) {
			body := "<!doctype html><html><title>" + tc.title + "</title></html>"
			c, sent, _ := mockDump(t, func(*http.Request) (*http.Response, error) {
				r, err := response(200, body)
				r.ContentLength = int64(len(body))
				if tc.mime != "" {
					r.Header.Set("Content-Type", tc.mime)
				}
				return r, err
			})
			_, err := c.get(testArchiveURL)
			code(t, err, tc.refusal)
			queue, err := c.ownerQueue()
			if err != nil || len(queue) != 1 || queue[0].Code != tc.refusal || queue[0].Host != dumpHost {
				t.Fatalf("owner queue: %+v, %v", queue, err)
			}
			c.run, c.cacheOnly = "next-run", true
			_, err = c.get(testArchiveURL)
			code(t, err, tc.refusal)
			queue, err = c.ownerQueue()
			if err != nil || len(queue) != 1 || queue[0].Run != c.run || len(*sent) != 3 {
				t.Fatalf("cached refusal: queue %+v, requests %+v, error %v", queue, *sent, err)
			}
		})
	}
}

func TestDumpRetainsBoundedFailedHTTPBodies(t *testing.T) {
	huge := "BZh9" + strings.Repeat("x", dumpPreviewBytes)
	for _, tc := range []struct {
		name, body, failure, bodyProblem string
		status                           int
		length                           int64
		readErr                          error
	}{
		{"redirect body", "moving", "redirect_denied", "", 302, 6, nil},
		{"server error body", "unavailable", "host_parked", "", 503, 11, nil},
		{"full checksum mismatch", "BZh9wrong", "dump_checksum_mismatch", "", 200, 9, nil},
		{"oversized response", huge, "incomplete_body", "exceeds", 200, maxDumpBytes + 1, nil},
		{"unknown-length diagnostic beyond cap", huge, "http_status", "exceeds", 404, -1, nil},
		{"length mismatch", "BZh9short", "incomplete_body", "declared length", 200, 50, nil},
		{"transport interruption", "BZh9partial", "incomplete_body", "read completely", 200, -1, io.ErrUnexpectedEOF},
		{"empty actual response", "", "http_status", "", 404, 0, nil},
	} {
		t.Run(tc.name, func(t *testing.T) {
			c, sent, _ := mockDump(t, func(*http.Request) (*http.Response, error) {
				r, err := response(tc.status, tc.body, "Content-Type", "application/octet-stream")
				r.ContentLength = tc.length
				if tc.readErr != nil {
					r.Body = io.NopCloser(io.MultiReader(strings.NewReader(tc.body), iotest.ErrReader(tc.readErr)))
				}
				return r, err
			})
			_, err := c.get(testArchiveURL)
			code(t, err, tc.failure)
			var saved dumpOutcome
			found, err := readJSON(filepath.Join(c.cache, receiptName(testArchiveURL)), 512*1024, &saved)
			want := tc.body[:min(len(tc.body), dumpPreviewBytes)]
			if err != nil || !found || saved.Status != tc.status || saved.Failure == nil ||
				saved.SHA256 != hash([]byte(want)) || saved.Bytes != len(want) || saved.DumpChecksum != nil ||
				(saved.BodyProblem == "") != (tc.bodyProblem == "") || !strings.Contains(saved.BodyProblem, tc.bodyProblem) {
				t.Fatalf("diagnostic receipt: %+v, %v", saved, err)
			}
			if got := saved.Headers["content-type"]; got != "application/octet-stream" {
				t.Fatalf("diagnostic Content-Type: %q", got)
			}
			path := filepath.Join(c.cache, saved.SHA256+".diagnostic")
			body, err := os.ReadFile(path)
			if err != nil || string(body) != want {
				t.Fatalf("retained diagnostic: len=%d, want=%d, err=%v", len(body), len(want), err)
			}
			archives, err := filepath.Glob(filepath.Join(c.cache, "*.dump"))
			if err != nil || len(archives) != 0 || len(*sent) != 3 {
				t.Fatalf("archives=%v, requests=%+v, err=%v", archives, *sent, err)
			}
		})
	}
}

func TestDumpCacheRejectsChangedFailureReceiptOrDiagnostic(t *testing.T) {
	for _, change := range []string{"status", "content type", "partial marker", "body hash", "missing body", "altered body"} {
		t.Run(change, func(t *testing.T) {
			c, sent, _ := mockDump(t, func(*http.Request) (*http.Response, error) {
				r, err := response(404, "missing", "Content-Type", "text/plain")
				r.ContentLength = 7
				return r, err
			})
			_, err := c.get(testArchiveURL)
			code(t, err, "http_status")
			path := filepath.Join(c.cache, receiptName(testArchiveURL))
			var saved dumpOutcome
			found, err := readJSON(path, 512*1024, &saved)
			if err != nil || !found {
				t.Fatalf("read failure receipt: %v, %v", found, err)
			}
			bodyPath := filepath.Join(c.cache, saved.SHA256+".diagnostic")
			switch change {
			case "status":
				saved.Status = 403
			case "content type":
				saved.Headers["content-type"] = "text/html"
			case "partial marker":
				saved.BodyProblem = "response body could not be read completely"
			case "body hash":
				saved.SHA256 = hash([]byte("changed"))
			case "missing body":
				err = os.Remove(bodyPath)
			case "altered body":
				err = os.WriteFile(bodyPath, []byte("changed"), 0600)
			}
			if err != nil {
				t.Fatal(err)
			}
			if change != "missing body" && change != "altered body" {
				if err := writeJSON(path, saved); err != nil {
					t.Fatal(err)
				}
			}
			c.run, c.cacheOnly = "next-run", true
			_, err = c.get(testArchiveURL)
			code(t, err, "cache_integrity")
			if len(*sent) != 3 {
				t.Fatalf("damaged diagnostic retried a request: %+v", *sent)
			}
		})
	}
}

func TestDumpRecoveryVerifiesFailedHTTPDiagnostic(t *testing.T) {
	for _, corrupt := range []bool{true, false} {
		t.Run(fmt.Sprint(corrupt), func(t *testing.T) {
			const markup = "<title>Terms of Use</title>"
			c, sent, _ := mockDump(t, func(*http.Request) (*http.Response, error) {
				r, err := response(200, markup)
				r.ContentLength = int64(len(markup))
				return r, err
			})
			injected := errors.New("interrupted final state write")
			c.persist = func(path string, value any) error {
				if state, ok := value.(hostState); ok && state.Pending == nil && len(*sent) == 3 {
					return injected
				}
				return writeJSON(path, value)
			}
			if _, err := c.get(testArchiveURL); !errors.Is(err, injected) {
				t.Fatalf("interrupted request: %v", err)
			}
			c.persist = nil
			if corrupt {
				if err := os.Remove(filepath.Join(c.cache, hash([]byte(markup))+".diagnostic")); err != nil {
					t.Fatal(err)
				}
			}
			_, err := c.get(testArchiveURL)
			if corrupt {
				code(t, err, "cache_integrity")
			} else {
				code(t, err, "terms_page")
				queue, err := c.ownerQueue()
				if err != nil || len(queue) != 1 || queue[0].Code != "terms_page" {
					t.Fatalf("recovered owner queue: %+v, %v", queue, err)
				}
			}
			if len(*sent) != 3 {
				t.Fatalf("interrupted refusal was requested again: %+v", *sent)
			}
		})
	}
}

func TestDumpStreamsBytesBeyondPolicyPreview(t *testing.T) {
	archive := "BZh9" + strings.Repeat("0123456789", dumpPreviewBytes)
	c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
		switch req.URL.String() {
		case dumpBase + "/robots.txt":
			return response(200, "User-Agent: *\n")
		case testManifestURL:
			r, err := response(200, manifestLine(testDumpName, archive))
			r.ContentLength = -1
			return r, err
		case testArchiveURL:
			r, err := response(200, archive, "Content-Type", "application/octet-stream")
			r.ContentLength = -1
			return r, err
		default:
			t.Fatalf("unexpected request: %s", req.URL)
			return nil, nil
		}
	})
	c.role = "script"
	rec, err := c.get(testArchiveURL)
	if err != nil || rec.Bytes != len(archive) || rec.SHA256 != hash([]byte(archive)) || rec.BodyProblem != "" {
		t.Fatalf("streamed archive receipt: %+v, %v", rec, err)
	}
	diagnostics, err := filepath.Glob(filepath.Join(c.cache, "*.diagnostic"))
	if err != nil || len(diagnostics) != 0 || len(*sent) != 3 {
		t.Fatalf("successful archive left diagnostics: %v, requests %+v, error %v", diagnostics, *sent, err)
	}
}

func TestDumpTermsPageWithErrorStatusParksOtherFiles(t *testing.T) {
	const terms = "<!doctype html><html><title>Terms of Use</title></html>"
	c, sent, _ := mockDump(t, func(*http.Request) (*http.Response, error) {
		r, err := response(404, terms, "Content-Type", "application/octet-stream")
		r.ContentLength = int64(len(terms))
		return r, err
	})
	_, err := c.get(testArchiveURL)
	code(t, err, "terms_page")
	queue, err := c.ownerQueue()
	if err != nil || len(queue) != 1 || queue[0].Host != dumpHost ||
		queue[0].Run != c.run || queue[0].Code != "terms_page" {
		t.Fatalf("owner queue: %+v, %v", queue, err)
	}
	_, err = c.get(dumpBase + "/rowiki/20261101/rowiki-20261101-redirect.sql.gz")
	code(t, err, "terms_page")
	if len(*sent) != 3 {
		t.Fatalf("host refusal allowed a later request: %+v", *sent)
	}
}

func TestDumpRobotsErrorPageParksHostBeforeFileReads(t *testing.T) {
	for _, tc := range []struct {
		title, mime, refusal string
	}{
		{"Terms of Use", "", "terms_page"},
		{"Terms of Use", "text/html", "terms_page"},
		{"Crawler Access Denied", "application/octet-stream", "crawler_block"},
	} {
		t.Run(tc.title+"/"+tc.mime, func(t *testing.T) {
			c, sent, _ := setup(t, func(req *http.Request) (*http.Response, error) {
				if req.URL.String() != dumpBase+"/robots.txt" {
					t.Fatalf("robots policy refusal allowed a file GET: %s", req.URL)
				}
				return response(404, "<html><title>"+tc.title+"</title></html>", "Content-Type", tc.mime)
			})
			c.role = "script"
			_, err := c.get(testArchiveURL)
			code(t, err, tc.refusal)
			_, err = c.get(testManifestURL)
			code(t, err, tc.refusal)
			queue, err := c.ownerQueue()
			if err != nil || len(queue) != 1 || queue[0].Host != dumpHost ||
				queue[0].Run != c.run || queue[0].Code != tc.refusal {
				t.Fatalf("owner queue: %+v, %v", queue, err)
			}
			c.run, c.cacheOnly = "next-run", true
			_, err = c.get(testManifestURL)
			code(t, err, tc.refusal)
			if len(*sent) != 1 {
				t.Fatalf("robots policy refusal triggered extra requests: %+v", *sent)
			}
		})
	}
}

func TestDumpCompressionMagicCannotHidePolicyError(t *testing.T) {
	const body = "BZh9<html><title>Terms of Use</title></html>"
	c, sent, _ := mockDump(t, func(*http.Request) (*http.Response, error) {
		r, err := response(404, body, "Content-Type", "application/octet-stream")
		r.ContentLength = int64(len(body))
		return r, err
	})
	_, err := c.get(testArchiveURL)
	code(t, err, "terms_page")
	_, err = c.get(testManifestURL)
	code(t, err, "terms_page")
	if len(*sent) != 3 {
		t.Fatalf("host refusal allowed a later request: %+v", *sent)
	}
}
