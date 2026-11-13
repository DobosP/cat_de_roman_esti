package main

import (
	"bufio"
	"bytes"
	"context"
	"crypto/sha1"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"strconv"
	"strings"
	"time"
)

const (
	dumpHost                = "dumps.wikimedia.org"
	maxDumpBytes            = 256 * 1024 * 1024
	maxManifestBytes        = 1024 * 1024
	dumpPreviewBytes        = 32 * 1024
	legacyManifestDuplicate = "published SHA-1 manifest repeats a filename"
)

var dumpDirectory = regexp.MustCompile(`^/(rowiktionary|rowiki)/([0-9]{8})/([^/]+)$`)
var manifestEntry = regexp.MustCompile(`^([0-9a-fA-F]{40})[ \t]+\*?([A-Za-z0-9][A-Za-z0-9._-]*)$`)

type dumpFile struct {
	name     string
	manifest *url.URL
	limit    int
	magic    string
}

func datedDump(target *url.URL) (dumpFile, bool) {
	parts := dumpDirectory.FindStringSubmatch(target.Path)
	if target.Host != dumpHost || len(parts) == 0 {
		return dumpFile{}, false
	}
	project, date, name := parts[1], parts[2], parts[3]
	day, err := time.Parse("20060102", date)
	if err != nil || day.Year() < 2001 {
		return dumpFile{}, false
	}
	prefix := project + "-" + date + "-"
	manifest := &url.URL{
		Scheme: "https", Host: dumpHost,
		Path: "/" + project + "/" + date + "/" + prefix + "sha1sums.txt",
	}
	switch {
	case name == prefix+"sha1sums.txt":
		return dumpFile{name: name, limit: maxManifestBytes}, true
	case project == "rowiktionary" && name == prefix+"pages-articles.xml.bz2":
		return dumpFile{name, manifest, maxDumpBytes, "BZh"}, true
	case project == "rowiki" && (name == prefix+"all-titles-in-ns0.gz" || name == prefix+"redirect.sql.gz"):
		return dumpFile{name, manifest, maxDumpBytes, "\x1f\x8b\x08"}, true
	}
	return dumpFile{}, false
}

func (file dumpFile) suffix() string {
	if file.manifest == nil {
		return ".body"
	}
	return ".dump"
}

type dumpChecksum struct {
	URL                    string `json:"url"`
	SHA256                 string `json:"sha256"`
	SHA1                   string `json:"sha1"`
	RecoveredOutcomeSHA256 string `json:"recovered_outcome_sha256,omitempty"`
}

type dumpAttempt struct {
	Started       time.Time `json:"started"`
	OutcomeSHA256 string    `json:"outcome_sha256,omitempty"`
}

type dumpOutcome struct {
	receipt
	Failure *refusal `json:"dump_failure,omitempty"`
}

func (outcome dumpOutcome) digest() (string, error) {
	data, err := json.Marshal(outcome)
	if err != nil {
		return "", err
	}
	return hash(data), nil
}

type dumpMaterial struct {
	receipt
	entries map[string]string
}

func parseManifest(body []byte) (map[string]string, error) {
	entries := map[string]string{}
	for line := range bytes.SplitSeq(bytes.TrimRight(body, "\r\n"), []byte("\n")) {
		match := manifestEntry.FindSubmatch(bytes.TrimSuffix(line, []byte("\r")))
		if match == nil {
			return nil, stop("dump_checksum_invalid", "published SHA-1 manifest has a malformed entry")
		}
		name := string(match[2])
		if _, exists := entries[name]; exists {
			// An empty digest marks an ambiguous basename, even if all
			// occurrences list the same hash.
			entries[name] = ""
			continue
		}
		entries[name] = strings.ToLower(string(match[1]))
	}
	return entries, nil
}

func (material dumpMaterial) checksumFor(file dumpFile) (dumpChecksum, error) {
	digest, ok := material.entries[file.name]
	if !ok {
		return dumpChecksum{}, stop("dump_checksum_missing", "published SHA-1 manifest lacks the exact archive filename")
	}
	if digest == "" {
		return dumpChecksum{}, stop("dump_checksum_invalid", "published SHA-1 manifest repeats the exact archive filename")
	}
	return dumpChecksum{
		URL: material.URL, SHA256: material.SHA256, SHA1: digest,
		RecoveredOutcomeSHA256: material.DumpManifestRecoveredOutcomeSHA256,
	}, nil
}

func (h *hostClient) getDump(target *url.URL, rules robotRules) (dumpMaterial, error) {
	file, _ := datedDump(target)
	if h.state.Breaker.After(h.now()) {
		return dumpMaterial{}, refusal{"host_parked", "source breaker is open", &h.state.Breaker}
	}
	if !rules.permits(target) || file.manifest != nil && !rules.permits(file.manifest) {
		return dumpMaterial{}, stop("robots_path_disallowed", "robots.txt disallows the requested path or its checksum manifest")
	}
	prior, found, err := h.readDumpOutcome(target)
	if err != nil {
		return dumpMaterial{}, err
	}
	if found {
		if prior.Failure != nil && dumpPolicyRefusal(prior.Failure.Code) {
			return dumpMaterial{}, h.deny(*prior.Failure)
		}
		return h.verifyDumpOutcome(file, prior)
	}
	if h.cacheOnly {
		return dumpMaterial{}, stop("cache_miss", "no reusable receipt for the requested dump URL")
	}
	if h.role != "script" {
		return dumpMaterial{}, stop("dump_script_only", "the initial dump and checksum GETs require role script")
	}
	var checksum dumpChecksum
	if file.manifest != nil {
		manifest, err := h.getDump(file.manifest, rules)
		if err != nil {
			return dumpMaterial{}, err
		}
		checksum, err = manifest.checksumFor(file)
		if err != nil {
			return dumpMaterial{}, err
		}
	}
	if err := h.reserve(target.String(), h.role); err != nil {
		return dumpMaterial{}, err
	}
	outcome, entries, err := h.downloadDump(target, file, checksum)
	if err != nil {
		return dumpMaterial{}, err
	}
	if err := h.store(filepath.Join(h.cache, receiptName(target.String())), outcome); err != nil {
		return dumpMaterial{}, err
	}
	if err := h.commitDumpOutcome(outcome); err != nil {
		return dumpMaterial{}, err
	}
	if h.state.Breaker.After(h.now()) {
		return dumpMaterial{}, refusal{"host_parked", "dump response parks this source", &h.state.Breaker}
	}
	if outcome.Failure != nil {
		return dumpMaterial{}, *outcome.Failure
	}
	return dumpMaterial{outcome.receipt, entries}, nil
}

func (h *hostClient) readDumpOutcome(target *url.URL) (dumpOutcome, bool, error) {
	var outcome dumpOutcome
	attempt, attempted := h.state.DumpAttempts[hash([]byte(target.String()))]
	path := filepath.Join(h.cache, receiptName(target.String()))
	info, err := os.Lstat(path)
	if errors.Is(err, os.ErrNotExist) {
		if attempted && (h.state.Pending == nil || h.state.Pending.URL != target.String()) {
			return dumpOutcome{}, false, stop("cache_integrity", "a previously attempted dump is missing its outcome")
		}
		return dumpOutcome{}, false, nil
	}
	if err != nil || !info.Mode().IsRegular() {
		return dumpOutcome{}, false, stop("cache_integrity", "dump outcome must be a readable regular file")
	}
	found, err := readJSON(path, 512*1024, &outcome)
	if err != nil {
		return dumpOutcome{}, false, err
	}
	if !found || !attempted {
		return dumpOutcome{}, false, stop("cache_integrity", "dump outcome does not have a matching reserved GET")
	}
	if attempt.OutcomeSHA256 != "" {
		digest, err := outcome.digest()
		if err != nil || digest != attempt.OutcomeSHA256 {
			return dumpOutcome{}, false, stop("cache_integrity", "dump outcome metadata differs from the recorded outcome")
		}
	} else if h.state.Pending == nil || h.state.Pending.URL != target.String() {
		return dumpOutcome{}, false, stop("cache_integrity", "dump attempt is neither completed nor pending")
	}
	rec := outcome.receipt
	file, _ := datedDump(target)
	valid := rec.URL == target.String() && rec.Origin == "v5" && rec.FirstOrigin == "v5" &&
		identifier.MatchString(rec.FirstFetcher) && rec.FirstFetcher == rec.AttemptID &&
		rec.FetchedByRole == "script" && rec.FetchedByRole == rec.AttemptRole &&
		rec.FetchedAt > 0 && rec.FetchedAt == epoch(attempt.Started) && rec.ReceivedAt >= rec.FetchedAt && rec.ReceivedAt < 253402300800 &&
		rec.Headers != nil && rec.DumpManifestRecoveredOutcomeSHA256 == ""
	if outcome.Failure == nil {
		valid = valid && rec.Status == http.StatusOK && validSHA(rec.SHA256) && rec.BodyProblem == "" &&
			rec.Bytes > 0 && rec.Bytes <= file.limit && (rec.DumpChecksum == nil) == (file.manifest == nil)
	} else {
		valid = valid && rec.DumpChecksum == nil &&
			outcome.Failure.Code != "" && outcome.Failure.Message != "" && outcome.Failure.RetryAt == nil
		if rec.Status == 0 {
			valid = valid && rec.SHA256 == "" && rec.Bytes == 0 && rec.BodyProblem == ""
		} else {
			valid = valid && rec.Status >= 100 && rec.Status <= 599 &&
				validSHA(rec.SHA256) && rec.Bytes >= 0 && rec.Bytes <= dumpPreviewBytes
		}
	}
	if !valid {
		return dumpOutcome{}, false, stop("cache_integrity", "invalid dump outcome or provenance")
	}
	if outcome.Failure != nil && rec.Status != 0 {
		if _, err := h.readDumpDiagnostic(rec); err != nil {
			return dumpOutcome{}, false, err
		}
	}
	return outcome, true, nil
}

func (h *hostClient) verifyDumpOutcome(file dumpFile, outcome dumpOutcome) (dumpMaterial, error) {
	if outcome.Failure != nil {
		if file.manifest == nil && *outcome.Failure == stop("dump_checksum_invalid", legacyManifestDuplicate) {
			return h.recheckRejectedManifest(file, outcome)
		}
		return dumpMaterial{}, *outcome.Failure
	}
	rec := outcome.receipt
	var expected dumpChecksum
	if file.manifest != nil {
		manifestFile, _ := datedDump(file.manifest)
		saved, found, err := h.readDumpOutcome(file.manifest)
		if err != nil {
			return dumpMaterial{}, err
		}
		if !found {
			return dumpMaterial{}, stop("cache_integrity", "cached archive lacks its checksum receipt")
		}
		manifest, err := h.verifyDumpOutcome(manifestFile, saved)
		if err != nil {
			if saved.Failure != nil {
				return dumpMaterial{}, stop("cache_integrity", "cached archive lacks a verified checksum manifest")
			}
			return dumpMaterial{}, err
		}
		expected, err = manifest.checksumFor(file)
		if err != nil || expected != *rec.DumpChecksum {
			return dumpMaterial{}, stop("cache_integrity", "cached archive receipt disagrees with its published checksum manifest")
		}
	}
	if why := responseRefusal(&url.URL{Host: dumpHost}, rec, nil); why.Code != "" {
		return dumpMaterial{}, stop("cache_integrity", "successful dump outcome contains a policy refusal")
	}
	entries, err := h.verifyDumpFile(file, rec.SHA256, rec.Bytes, expected.SHA1)
	if err != nil {
		return dumpMaterial{}, err
	}
	return dumpMaterial{rec, entries}, nil
}

func (h *hostClient) recheckRejectedManifest(file dumpFile, outcome dumpOutcome) (dumpMaterial, error) {
	rec := outcome.receipt
	original := h.state.DumpAttempts[hash([]byte(rec.URL))].OutcomeSHA256
	encoding := rec.Headers["content-encoding"]
	declared, err := strconv.ParseInt(rec.Headers["content-length"], 10, 64)
	if !validSHA(original) || rec.Status != http.StatusOK || rec.BodyProblem != "" || rec.Bytes <= 0 ||
		err != nil || (declared != -1 && declared != int64(rec.Bytes)) ||
		(encoding != "" && !strings.EqualFold(encoding, "identity")) || rec.Headers["content-range"] != "" ||
		strings.Contains(strings.ToLower(rec.Headers["content-type"]), "text/html") {
		return dumpMaterial{}, *outcome.Failure
	}
	rawOutcome, err := readBounded(filepath.Join(h.cache, receiptName(rec.URL)), 512*1024)
	if err != nil || !bytes.HasSuffix(rawOutcome, []byte("\n")) ||
		hash(bytes.TrimSuffix(rawOutcome, []byte("\n"))) != original {
		return dumpMaterial{}, stop("cache_integrity", "original manifest outcome bytes do not match the recorded outcome")
	}
	body, err := h.readDumpDiagnostic(rec)
	if err != nil {
		return dumpMaterial{}, err
	}
	target, err := url.Parse(rec.URL)
	if err != nil {
		return dumpMaterial{}, stop("cache_integrity", "original manifest outcome URL is invalid")
	}
	if responseRefusal(target, rec, body).Code != "" || dumpResponseRefusal(rec, file, body).Code != "" {
		return dumpMaterial{}, *outcome.Failure
	}
	entries, err := parseManifest(body)
	if err != nil {
		return dumpMaterial{}, *outcome.Failure
	}
	for _, digest := range entries {
		if digest == "" {
			rec.DumpManifestRecoveredOutcomeSHA256 = original
			return dumpMaterial{rec, entries}, nil
		}
	}
	return dumpMaterial{}, *outcome.Failure
}

func (h *hostClient) verifyDumpFile(file dumpFile, digest string, size int, expectedSHA1 string) (map[string]string, error) {
	path := filepath.Join(h.cache, digest+file.suffix())
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() || info.Size() != int64(size) {
		return nil, stop("cache_integrity", "cached dump payload is missing or has the wrong size")
	}
	body, err := os.Open(path)
	if err != nil {
		return nil, stop("cache_integrity", "cached dump payload cannot be read")
	}
	defer body.Close()
	opened, err := body.Stat()
	if err != nil || !os.SameFile(info, opened) {
		return nil, stop("cache_integrity", "cached dump payload changed while opening")
	}
	if file.manifest == nil {
		data, err := io.ReadAll(io.LimitReader(body, int64(size)+1))
		if err != nil || len(data) != size || hash(data) != digest {
			return nil, stop("cache_integrity", "cached checksum manifest body does not match its receipt")
		}
		return parseManifest(data)
	}
	sha256Hash, sha1Hash := sha256.New(), sha1.New()
	n, err := io.Copy(io.MultiWriter(sha256Hash, sha1Hash), io.LimitReader(body, int64(size)+1))
	if err != nil || n != int64(size) || hex.EncodeToString(sha256Hash.Sum(nil)) != digest ||
		hex.EncodeToString(sha1Hash.Sum(nil)) != expectedSHA1 {
		return nil, stop("cache_integrity", "cached archive does not match its SHA-256 and published SHA-1")
	}
	return nil, nil
}

func (h *hostClient) recoverDump(target *url.URL, pending *pendingRead) error {
	outcome, found, err := h.readDumpOutcome(target)
	if err != nil {
		return err
	}
	if !found {
		return stop("source_recovery_required", "an interrupted dump request has no verifiable response receipt")
	}
	if outcome.AttemptRole != pending.Role || outcome.AttemptID != pending.Fetcher ||
		outcome.FetchedAt != epoch(pending.Started) {
		return stop("cache_integrity", "dump outcome does not bind to the pending request")
	}
	if outcome.Failure == nil {
		file, _ := datedDump(target)
		if _, err := h.verifyDumpOutcome(file, outcome); err != nil {
			return err
		}
	}
	return h.commitDumpOutcome(outcome)
}

func (h *hostClient) commitDumpOutcome(outcome dumpOutcome) error {
	digest, err := outcome.digest()
	if err != nil {
		return err
	}
	key := hash([]byte(outcome.URL))
	attempt := h.state.DumpAttempts[key]
	attempt.OutcomeSHA256 = digest
	h.state.DumpAttempts[key] = attempt
	at := timeFromEpoch(outcome.ReceivedAt)
	if outcome.Failure != nil && dumpPolicyRefusal(outcome.Failure.Code) {
		h.addDenial(h.state.Pending.Run, *outcome.Failure, at)
	}
	if retryStatus(outcome.Status) {
		h.state.Breaker = maxTime(h.state.Breaker, retryUntil(outcome.Headers["retry-after"], at))
	}
	h.state.Pending = nil
	return h.store(h.file, h.state)
}

func dumpPolicyRefusal(code string) bool {
	return code == "crawler_block" || code == "content_signal" || code == "terms_page"
}

func (h *hostClient) downloadDump(target *url.URL, file dumpFile, checksum dumpChecksum) (outcome dumpOutcome, entries map[string]string, err error) {
	outcome.receipt = receipt{
		URL: target.String(), Headers: map[string]string{}, Origin: "v5", FirstOrigin: "v5",
		FetchedAt: epoch(h.state.LastStart), FetchedByRole: h.role, FirstFetcher: h.fetcher,
		AttemptRole: h.role, AttemptID: h.fetcher,
	}
	defer func() { outcome.ReceivedAt = epoch(maxTime(h.now(), h.state.LastStart)) }()
	fail := func(why refusal) (dumpOutcome, map[string]string, error) {
		outcome.Failure = &why
		return outcome, nil, nil
	}

	timeout := 30 * time.Second
	if file.manifest != nil {
		timeout = 15 * time.Minute
	}
	ctx, cancel := context.WithTimeout(context.Background(), timeout)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target.String(), nil)
	if err != nil {
		return fail(stop("url_denied", "unable to construct a dump GET"))
	}
	req.Header.Set("User-Agent", userAgent)
	req.Header.Set("Accept-Encoding", "identity")
	res, err := h.http.RoundTrip(req)
	if err != nil {
		return fail(stop("transport_error", "dump GET did not produce a response"))
	}
	defer res.Body.Close()
	outcome.Status, outcome.Headers = res.StatusCode, sourceHeaders(res)

	headerRefusal := responseRefusal(target, outcome.receipt, nil)
	encoding := strings.Join(res.Header.Values("Content-Encoding"), ",")
	contentRange := strings.Join(res.Header.Values("Content-Range"), ",")
	outcome.Headers["content-encoding"] = encoding
	outcome.Headers["content-range"] = contentRange
	outcome.Headers["content-length"] = strconv.FormatInt(res.ContentLength, 10)
	// Bound early diagnostics independently of the full archive deadline.
	// A slow body must not delay a known header refusal for 15 minutes.
	prefixTimer := time.AfterFunc(30*time.Second, cancel)
	prefix, prefixErr := io.ReadAll(io.LimitReader(res.Body, dumpPreviewBytes+1))
	prefixTimer.Stop()
	failResponse := func(why refusal) (dumpOutcome, map[string]string, error) {
		outcome.BodyProblem = dumpDiagnosticProblem(res, len(prefix), prefixErr)
		diagnostic := prefix[:min(len(prefix), dumpPreviewBytes)]
		outcome.SHA256, outcome.Bytes = hash(diagnostic), len(diagnostic)
		if err := h.saveDumpDiagnostic(outcome.receipt, diagnostic); err != nil {
			return outcome, nil, err
		}
		return fail(why)
	}
	if headerRefusal.Code != "" {
		return failResponse(headerRefusal)
	}
	if why := dumpResponseRefusal(outcome.receipt, file, prefix[:min(len(prefix), dumpPreviewBytes)]); why.Code != "" {
		return failResponse(why)
	}
	if res.StatusCode >= 300 && res.StatusCode < 400 {
		return failResponse(stop("redirect_denied", "dated dump URLs must serve their files directly"))
	}
	if res.StatusCode != http.StatusOK {
		return failResponse(stop("http_status", fmt.Sprintf("dump response returned HTTP %d", res.StatusCode)))
	}
	isHTML := strings.Contains(strings.ToLower(res.Header.Get("Content-Type")), "text/html")
	if isHTML || res.Uncompressed || encoding != "" && !strings.EqualFold(encoding, "identity") ||
		len(res.Header.Values("Content-Range")) != 0 {
		return failResponse(stop("dump_invalid_response", "dump requires a complete, untransformed file response"))
	}
	if res.ContentLength > int64(file.limit) {
		return failResponse(stop("incomplete_body", "dump response exceeds the retained file limit"))
	}
	if prefixErr != nil {
		return failResponse(stop("incomplete_body", "dump response ended with a read error"))
	}
	// The prefix was read once for policy and diagnostics. Replay it for
	// checksum verification, then stream the remainder if there is one.
	var stream io.Reader = bytes.NewReader(prefix)
	if len(prefix) > dumpPreviewBytes {
		stream = io.MultiReader(stream, res.Body)
	}
	body := bufio.NewReader(stream)

	digest, size, entries, why := h.storeDumpPayload(target, outcome.receipt, file, body, res.ContentLength, checksum)
	if why.Code != "" {
		return failResponse(why)
	}
	outcome.SHA256, outcome.Bytes = digest, size
	if file.manifest != nil {
		outcome.DumpChecksum = &checksum
	}
	return outcome, entries, nil
}

func dumpResponseRefusal(rec receipt, file dumpFile, prefix []byte) refusal {
	isHTML := strings.Contains(strings.ToLower(rec.Headers["content-type"]), "text/html")
	if rec.Status == http.StatusOK && !isHTML && file.magic != "" && bytes.HasPrefix(prefix, []byte(file.magic)) {
		return refusal{}
	}
	if hostRefusalTitle.Match(prefix) {
		return stop("crawler_block", "source returned a crawler or access block")
	}
	if termsTitle.Match(prefix) {
		return stop("terms_page", "source returned a terms page")
	}
	return refusal{}
}

func dumpDiagnosticProblem(res *http.Response, size int, readErr error) string {
	switch {
	case res.Uncompressed:
		return "retained response bytes were decoded by the transport"
	case size > dumpPreviewBytes:
		return "response body exceeds the retained diagnostic byte limit"
	case readErr != nil:
		return "response body could not be read completely"
	case res.ContentLength >= 0 && int64(size) != res.ContentLength:
		return "response body length does not match its declared length"
	default:
		return ""
	}
}

func (h *hostClient) saveDumpDiagnostic(rec receipt, body []byte) error {
	path := filepath.Join(h.cache, rec.SHA256+".diagnostic")
	if _, err := os.Lstat(path); errors.Is(err, os.ErrNotExist) {
		return atomicWrite(path, body)
	}
	_, err := h.readDumpDiagnostic(rec)
	return err
}

func (h *hostClient) readDumpDiagnostic(rec receipt) ([]byte, error) {
	path := filepath.Join(h.cache, rec.SHA256+".diagnostic")
	info, err := os.Lstat(path)
	if err != nil || !info.Mode().IsRegular() || info.Size() != int64(rec.Bytes) {
		return nil, stop("cache_integrity", "failed dump response body is missing or has the wrong size")
	}
	body, err := readBounded(path, dumpPreviewBytes)
	if err != nil || len(body) != rec.Bytes || hash(body) != rec.SHA256 {
		return nil, stop("cache_integrity", "failed dump response body does not match its receipt")
	}
	return body, nil
}

func (h *hostClient) storeDumpPayload(target *url.URL, rec receipt, file dumpFile, body *bufio.Reader, declared int64, checksum dumpChecksum) (string, int, map[string]string, refusal) {
	if file.manifest != nil {
		header, err := body.Peek(len(file.magic))
		if err != nil {
			return "", 0, nil, stop("incomplete_body", "archive ended before its compression header")
		}
		if string(header) != file.magic {
			return "", 0, nil, stop("dump_invalid_response", "archive is missing the expected compression header")
		}
	}
	tmp, err := os.CreateTemp(h.cache, ".dump-next-")
	if err != nil {
		return "", 0, nil, stop("dump_write_failed", "cannot create a temporary dump payload")
	}
	defer os.Remove(tmp.Name())
	defer tmp.Close()
	sha256Hash, sha1Hash := sha256.New(), sha1.New()
	n, copyErr := io.Copy(io.MultiWriter(tmp, sha256Hash, sha1Hash), io.LimitReader(body, int64(file.limit)))
	if copyErr == nil && n == int64(file.limit) {
		_, copyErr = body.ReadByte()
		if copyErr == nil {
			return "", 0, nil, stop("incomplete_body", "dump response exceeds the retained file limit")
		}
		if errors.Is(copyErr, io.EOF) {
			copyErr = nil
		}
	}
	syncErr, closeErr := tmp.Sync(), tmp.Close()
	if syncErr != nil || closeErr != nil {
		return "", 0, nil, stop("dump_write_failed", "cannot finish the temporary dump payload")
	}
	if copyErr != nil || n == 0 || declared >= 0 && n != declared {
		return "", 0, nil, stop("incomplete_body", "dump response was incomplete or exceeded the retained file limit")
	}
	digest := hex.EncodeToString(sha256Hash.Sum(nil))
	var entries map[string]string
	if file.manifest == nil {
		data, err := readBounded(tmp.Name(), file.limit)
		if err != nil {
			return "", 0, nil, stop("dump_write_failed", "cannot read the stored checksum manifest")
		}
		if why := responseRefusal(target, rec, data); why.Code != "" {
			return "", 0, nil, why
		}
		entries, err = parseManifest(data)
		if err != nil {
			return "", 0, nil, stop("dump_checksum_invalid", err.Error())
		}
	} else if hex.EncodeToString(sha1Hash.Sum(nil)) != checksum.SHA1 {
		return "", 0, nil, stop("dump_checksum_mismatch", "archive bytes do not match the published SHA-1")
	}
	path := filepath.Join(h.cache, digest+file.suffix())
	if _, err := os.Lstat(path); os.IsNotExist(err) {
		if err := os.Rename(tmp.Name(), path); err != nil {
			return "", 0, nil, stop("dump_write_failed", "cannot publish the verified dump payload")
		}
	} else if err != nil {
		return "", 0, nil, stop("dump_write_failed", "cannot inspect the dump payload path")
	} else if _, err := h.verifyDumpFile(file, digest, int(n), checksum.SHA1); err != nil {
		return "", 0, nil, stop("cache_integrity", "existing dump payload does not match its content address")
	}
	return digest, int(n), entries, refusal{}
}
