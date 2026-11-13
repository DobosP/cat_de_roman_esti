package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net"
	"net/http"
	"os"
	"path/filepath"
	"regexp"
	"slices"
	"strings"
	"time"
)

type refusal struct {
	Code    string     `json:"code"`
	Message string     `json:"message"`
	RetryAt *time.Time `json:"retry_at,omitempty"`
}

func (r refusal) Error() string { return r.Message }

func stop(code, message string) refusal {
	return refusal{Code: code, Message: message}
}

var identifier = regexp.MustCompile(`^[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}$`)
var roles = map[string]bool{
	"author": true, "factual": true, "quality": true, "critic": true, "script": true,
	"policy": true, "legacy": true,
}

func transport() *http.Transport {
	return &http.Transport{
		DialContext:            dialSource,
		DisableKeepAlives:      true,
		DisableCompression:     true,
		MaxResponseHeaderBytes: 64 * 1024,
		TLSHandshakeTimeout:    10 * time.Second,
	}
}

func dialSource(ctx context.Context, network, address string) (net.Conn, error) {
	host, port, err := net.SplitHostPort(address)
	if err != nil {
		return nil, err
	}
	dialer := net.Dialer{Timeout: 10 * time.Second}
	if host == "localhost" && port == "8077" {
		return dialer.DialContext(ctx, network, "127.0.0.1:8077")
	}
	if _, ok := sources[host]; !ok || port != "443" {
		return nil, errors.New("dial target is outside the source grant")
	}
	ips, err := net.DefaultResolver.LookupIPAddr(ctx, host)
	if err != nil {
		return nil, err
	}
	for _, ip := range ips {
		if !ip.IP.IsGlobalUnicast() || ip.IP.IsPrivate() || ip.IP.IsLoopback() {
			continue
		}
		conn, err := dialer.DialContext(ctx, network, net.JoinHostPort(ip.IP.String(), port))
		if err == nil {
			return conn, nil
		}
	}
	return nil, errors.New("no public source endpoint could be reached")
}

func resolveCachePath(path string) (string, error) {
	path, err := filepath.Abs(path)
	if err != nil {
		return "", err
	}
	var suffix []string
	for {
		resolved, err := filepath.EvalSymlinks(path)
		if err == nil {
			slices.Reverse(suffix)
			return filepath.Join(append([]string{resolved}, suffix...)...), nil
		}
		if !errors.Is(err, os.ErrNotExist) {
			return "", err
		}
		if _, err := os.Lstat(path); !errors.Is(err, os.ErrNotExist) {
			return "", stop("usage", "cache path has a dangling link or inaccessible ancestor")
		}
		parent := filepath.Dir(path)
		if parent == path {
			return "", err
		}
		suffix = append(suffix, filepath.Base(path))
		path = parent
	}
}

func insideLegacyCache(fresh, legacy string) (bool, error) {
	legacyInfo, err := os.Stat(legacy)
	if err != nil {
		return false, err
	}
	for path := fresh; ; path = filepath.Dir(path) {
		info, err := os.Stat(path)
		switch {
		case err == nil && os.SameFile(info, legacyInfo):
			return true, nil
		case err != nil && !errors.Is(err, os.ErrNotExist):
			return false, err
		}
		if filepath.Dir(path) == path {
			return false, nil
		}
	}
}

func run(args []string) (retErr error) {
	flags := flag.NewFlagSet("content-source", flag.ContinueOnError)
	cache := flags.String("cache", "", "shared campaign cache directory")
	legacy := flags.String("legacy-cache", "", "read-only V4 cache directory")
	runID := flags.String("run", "", "stable campaign identifier")
	role := flags.String("role", "", "source role: script, author, factual, quality, critic or policy")
	fetcher := flags.String("fetcher", "", "identifier of the fetching thread or script")
	cacheOnly := flags.Bool("cache-only", false, "verify receipts without making new requests")
	refuseHost := flags.String("refuse-host", "", "record a host-wide refusal found during policy inspection")
	reason := flags.String("reason", "", "reason for an inspected host refusal")
	queue := flags.Bool("owner-queue", false, "print this run’s host refusals as JSON")
	flags.Usage = func() {
		fmt.Fprintln(flags.Output(), "Usage: content-source --cache DIR --run ID --role ROLE --fetcher ID [options] URL")
		fmt.Fprintln(flags.Output(), "   or: content-source --cache DIR --run ID --role policy --fetcher ID --refuse-host HOST --reason REASON")
		fmt.Fprintln(flags.Output(), "   or: content-source --cache DIR --run ID --role script --fetcher ID --owner-queue")
		flags.PrintDefaults()
	}
	if err := flags.Parse(args); err != nil {
		return err
	}
	if *cache == "" || !identifier.MatchString(*runID) || !identifier.MatchString(*fetcher) ||
		!roles[*role] || *role == "legacy" {
		return stop("usage", "valid --cache, --run, --role and --fetcher are required")
	}
	fresh, err := resolveCachePath(*cache)
	if err != nil {
		return err
	}
	*cache = fresh
	if *legacy != "" {
		old, err := filepath.Abs(*legacy)
		if err == nil {
			old, err = filepath.EvalSymlinks(old)
		}
		if err != nil {
			return stop("usage", "legacy cache directory is unavailable")
		}
		inside, err := insideLegacyCache(fresh, old)
		if err != nil {
			return err
		}
		if inside {
			return stop("usage", "V5 cache must be outside the read-only legacy cache")
		}
		*legacy = old
	}
	if *queue {
		if *refuseHost != "" || *reason != "" || flags.NArg() != 0 {
			return stop("usage", "owner queue mode takes no URL or refusal")
		}
	} else if *refuseHost != "" {
		if _, ok := sources[*refuseHost]; !ok || *role != "policy" || flags.NArg() != 0 ||
			*reason == "" || len(*reason) > 512 || strings.ContainsAny(*reason, "\r\n") {
			return stop("usage", "host refusal requires a granted host, role policy and a one-line reason")
		}
	} else if flags.NArg() != 1 || *reason != "" {
		return stop("usage", "exactly one URL is required")
	}
	unlock, err := lockCache(*cache)
	if err != nil {
		return err
	}
	defer func() { retErr = errors.Join(retErr, unlock()) }()
	c := client{
		cache: *cache, legacy: *legacy, run: *runID, role: *role, fetcher: *fetcher,
		cacheOnly: *cacheOnly, http: transport(), now: time.Now, sleep: time.Sleep,
	}
	if *queue {
		lines, err := c.ownerQueue()
		if err != nil {
			return err
		}
		return json.NewEncoder(os.Stdout).Encode(lines)
	}
	if *refuseHost != "" {
		host, err := c.openHost(*refuseHost)
		if err != nil {
			return err
		}
		_, err = host.record(stop("policy_refusal", *reason))
		return err
	}
	result, err := c.get(flags.Arg(0))
	if err != nil {
		return err
	}
	return json.NewEncoder(os.Stdout).Encode(result)
}

func (c *client) ownerQueue() ([]denial, error) {
	var hosts []string
	for name := range sources {
		hosts = append(hosts, name)
	}
	slices.Sort(hosts)
	lines := make([]denial, 0, len(hosts))
	for _, name := range hosts {
		host, err := c.openHost(name)
		if err != nil {
			var why refusal
			if !errors.As(err, &why) || why.Code != "source_recovery_required" {
				return nil, err
			}
			// Pending reads park the host across runs. Keep one visible entry
			// in this run's queue with the original interruption timestamp.
			lines = append(lines, denial{name, c.run, why.Code, why.Message, host.state.Pending.Started})
			continue
		}
		if line, ok := host.state.Denials[c.run]; ok {
			lines = append(lines, line)
		}
	}
	return lines, nil
}

func main() {
	if err := run(os.Args[1:]); err != nil && !errors.Is(err, flag.ErrHelp) {
		var why refusal
		if !errors.As(err, &why) {
			why = stop("tool_error", err.Error())
		}
		_ = json.NewEncoder(os.Stderr).Encode(why)
		os.Exit(1)
	}
}
