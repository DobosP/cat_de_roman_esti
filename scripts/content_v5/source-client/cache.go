package main

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math"
	"os"
	"path/filepath"
	"strings"
	"time"
)

const maxBody = 16 * 1024 * 1024

type receipt struct {
	URL           string            `json:"url"`
	SHA256        string            `json:"sha256"`
	Status        int               `json:"status"`
	Bytes         int               `json:"bytes"`
	FetchedByRole string            `json:"fetched_by_role"`
	FetchedAt     float64           `json:"fetched_at"`
	Headers       map[string]string `json:"headers"`
	Origin        string            `json:"origin"`
	FirstOrigin   string            `json:"first_fetch_origin"`
	FirstFetcher  string            `json:"first_fetcher,omitempty"`
	ReceivedAt    float64           `json:"received_at,omitempty"`
	AttemptRole   string            `json:"attempt_role,omitempty"`
	AttemptID     string            `json:"attempt_fetcher,omitempty"`
	BodyProblem   string            `json:"body_problem,omitempty"`
	DumpChecksum  *dumpChecksum     `json:"dump_checksum,omitempty"`
}

type hostState struct {
	LastStart    time.Time              `json:"last_start"`
	Breaker      time.Time              `json:"breaker_until"`
	UTCDay       string                 `json:"utc_day"`
	Reads        int                    `json:"reads"`
	Denials      map[string]denial      `json:"owner_queue,omitempty"`
	Pending      *pendingRead           `json:"pending_read,omitempty"`
	DumpAttempts map[string]dumpAttempt `json:"dump_attempts,omitempty"`
}

type pendingRead struct {
	Run     string    `json:"run"`
	URL     string    `json:"url"`
	Started time.Time `json:"started"`
	Role    string    `json:"role"`
	Fetcher string    `json:"fetcher"`
}

func (p pendingRead) filename() string {
	key := p.Run + "\n" + p.URL + "\n" + p.Started.Format(time.RFC3339Nano) + "\n" + p.Role + "\n" + p.Fetcher
	return hash([]byte(key)) + ".response.json"
}

type denial struct {
	Host   string    `json:"host"`
	Run    string    `json:"run"`
	Code   string    `json:"code"`
	Reason string    `json:"reason"`
	At     time.Time `json:"at"`
}

func hash(body []byte) string {
	return fmt.Sprintf("%x", sha256.Sum256(body))
}

func validSHA(value string) bool {
	decoded, err := hex.DecodeString(value)
	return err == nil && len(decoded) == sha256.Size && strings.ToLower(value) == value
}

func readBounded(path string, limit int) ([]byte, error) {
	f, err := os.Open(path)
	if err != nil {
		return nil, err
	}
	defer f.Close()
	info, err := f.Stat()
	if err != nil || !info.Mode().IsRegular() {
		return nil, fmt.Errorf("cache entry must be a regular file")
	}
	body, err := io.ReadAll(io.LimitReader(f, int64(limit)+1))
	if err == nil && len(body) > limit {
		return nil, fmt.Errorf("cache entry exceeds byte limit")
	}
	return body, err
}

func readJSON(path string, limit int, dest any) (bool, error) {
	body, err := readBounded(path, limit)
	if errors.Is(err, os.ErrNotExist) {
		return false, nil
	}
	if err != nil || json.Unmarshal(body, dest) != nil {
		return false, stop("cache_integrity", "unreadable or malformed cache entry: "+filepath.Base(path))
	}
	return true, nil
}

func atomicWrite(path string, data []byte) error {
	tmp, err := os.CreateTemp(filepath.Dir(path), ".next-")
	if err != nil {
		return err
	}
	defer os.Remove(tmp.Name())
	_, writeErr := tmp.Write(data)
	syncErr := tmp.Sync()
	closeErr := tmp.Close()
	if err := errors.Join(writeErr, syncErr, closeErr); err != nil {
		return err
	}
	return os.Rename(tmp.Name(), path)
}

func writeJSON(path string, value any) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return atomicWrite(path, append(data, '\n'))
}

func lockCache(cache string) (func() error, error) {
	if err := os.MkdirAll(cache, 0700); err != nil {
		return nil, err
	}
	lock := filepath.Join(cache, ".v5-lock")
	err := os.Mkdir(lock, 0700)
	if errors.Is(err, os.ErrExist) {
		return nil, stop("cache_busy", "the source cache already has a writer")
	}
	return func() error { return os.Remove(lock) }, err
}

func receiptName(address string) string {
	return hash([]byte(address)) + ".receipt.json"
}

func loadReceipt(root, address, origin string) (receipt, []byte, bool, error) {
	return loadNamedReceipt(root, receiptName(address), address, origin)
}

func loadNamedReceipt(root, name, address, origin string) (receipt, []byte, bool, error) {
	var rec receipt
	exists, err := readJSON(filepath.Join(root, name), 512*1024, &rec)
	if !exists || err != nil {
		return rec, nil, false, err
	}
	if rec.URL != address || !validSHA(rec.SHA256) || !roles[rec.FetchedByRole] ||
		math.IsNaN(rec.FetchedAt) || math.IsInf(rec.FetchedAt, 0) || rec.FetchedAt <= 0 || rec.FetchedAt >= 253402300800 ||
		rec.Bytes < 0 || rec.Bytes > maxBody || rec.Status < 100 || rec.Status > 599 || rec.Headers == nil {
		return rec, nil, false, stop("cache_integrity", "receipt has invalid fields or URL binding")
	}
	validFirst := rec.FirstOrigin == "v5" && identifier.MatchString(rec.FirstFetcher) ||
		rec.FirstOrigin == "legacy" && rec.FirstFetcher == ""
	if origin == "v5" && (rec.Origin != "v5" || !validFirst ||
		!identifier.MatchString(rec.AttemptID) || !roles[rec.AttemptRole] || rec.ReceivedAt < rec.FetchedAt ||
		math.IsNaN(rec.ReceivedAt) || math.IsInf(rec.ReceivedAt, 0) || rec.ReceivedAt >= 253402300800) {
		return rec, nil, false, stop("cache_integrity", "receipt has invalid V5 provenance")
	}
	if origin == "legacy" {
		rec.Origin, rec.FirstOrigin = origin, origin
		rec.FirstFetcher = ""
		rec.ReceivedAt = 0
		rec.AttemptRole = ""
		rec.AttemptID = ""
		rec.BodyProblem = ""
	}
	body, err := readBounded(filepath.Join(root, rec.SHA256+".body"), maxBody)
	if err != nil || len(body) != rec.Bytes || hash(body) != rec.SHA256 {
		return rec, nil, false, stop("cache_integrity", "cached body does not match its receipt")
	}
	return rec, body, true, nil
}

func saveResponse(cache, name string, rec receipt, body []byte) error {
	file := filepath.Join(cache, rec.SHA256+".body")
	have, err := readBounded(file, maxBody)
	if errors.Is(err, os.ErrNotExist) {
		if err := atomicWrite(file, body); err != nil {
			return err
		}
	} else if err != nil || hash(have) != rec.SHA256 {
		return stop("cache_integrity", "stored body does not match its content address")
	}
	// Keep each actual response, even when a transient response is replaced.
	return writeJSON(filepath.Join(cache, name), rec)
}
