package main

import (
	"context"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

type client struct {
	cache, legacy, run, role, fetcher string
	cacheOnly                         bool
	http                              http.RoundTripper
	now                               func() time.Time
	sleep                             func(time.Duration)
	persist                           func(string, any) error
}

type hostClient struct {
	*client
	host  string
	file  string
	state hostState
	delay time.Duration
}

func (c *client) openHost(host string) (*hostClient, error) {
	h := &hostClient{
		client: c, host: host, delay: sources[host].delay,
		file: filepath.Join(c.cache, strings.ReplaceAll(host, ":", "-")+".v5-state.json"),
	}
	exists, err := readJSON(h.file, 256*1024, &h.state)
	if err != nil {
		return nil, err
	}
	if exists && (h.state.Reads < 0 || h.state.UTCDay != "" && len(h.state.UTCDay) != 10 ||
		h.state.Reads > 0 && h.state.UTCDay == "") {
		return nil, stop("cache_integrity", "invalid source host state")
	}
	for run, line := range h.state.Denials {
		if line.Host != host || line.Run != run || !identifier.MatchString(run) ||
			line.Code == "" || line.Reason == "" || line.At.IsZero() {
			return nil, stop("cache_integrity", "invalid owner queue entry")
		}
	}
	return h, h.recover()
}

func (c *client) store(path string, value any) error {
	if c.persist != nil {
		return c.persist(path, value)
	}
	return writeJSON(path, value)
}

func (h *hostClient) recover() error {
	pending := h.state.Pending
	if pending == nil {
		return nil
	}
	target, err := admit(pending.URL, pending.Role)
	if err != nil || target.Host != h.host || target.String() != pending.URL ||
		!identifier.MatchString(pending.Run) || !identifier.MatchString(pending.Fetcher) ||
		!roles[pending.Role] || pending.Role == "legacy" || !pending.Started.Equal(h.state.LastStart) {
		return stop("cache_integrity", "invalid pending source request")
	}
	rec, body, found, err := loadNamedReceipt(h.cache, pending.filename(), pending.URL, "v5")
	if err != nil {
		return err
	}
	if !found {
		return stop("source_recovery_required", "an interrupted source request has no verifiable response receipt")
	}
	if rec.AttemptRole != pending.Role || rec.AttemptID != pending.Fetcher ||
		rec.FetchedAt > epoch(pending.Started) || rec.ReceivedAt < epoch(pending.Started) {
		return stop("cache_integrity", "response does not bind to the pending source request")
	}
	_, err = h.commitResponse(target, rec, body)
	return err
}

func (h *hostClient) commitResponse(target *url.URL, rec receipt, body []byte) (refusal, error) {
	pending := h.state.Pending
	why := responseRefusal(target, rec, body)
	if why.Code != "" {
		h.addDenial(pending.Run, why, timeFromEpoch(rec.ReceivedAt))
	}
	if retryStatus(rec.Status) {
		until := retryUntil(rec.Headers["retry-after"], timeFromEpoch(rec.ReceivedAt))
		h.state.Breaker = maxTime(h.state.Breaker, until)
	}
	if err := h.store(filepath.Join(h.cache, receiptName(rec.URL)), rec); err != nil {
		return refusal{}, err
	}
	h.state.Pending = nil
	return why, h.store(h.file, h.state)
}

func (h *hostClient) addDenial(run string, why refusal, at time.Time) {
	if _, exists := h.state.Denials[run]; exists {
		return
	}
	if h.state.Denials == nil {
		h.state.Denials = make(map[string]denial)
	}
	h.state.Denials[run] = denial{h.host, run, why.Code, why.Message, at}
}

func (h *hostClient) record(why refusal) (refusal, error) {
	if prior, ok := h.state.Denials[h.run]; ok {
		return stop(prior.Code, prior.Reason), nil
	}
	h.addDenial(h.run, why, h.now().UTC())
	return why, h.store(h.file, h.state)
}

func (h *hostClient) deny(why refusal) error {
	refused, err := h.record(why)
	if err != nil {
		return err
	}
	return refused
}

func (c *client) get(raw string) (receipt, error) {
	target, err := admit(raw, c.role)
	if target == nil {
		return receipt{}, err
	}
	h, stateErr := c.openHost(target.Host)
	if stateErr != nil {
		return receipt{}, stateErr
	}
	if err != nil {
		var why refusal
		if errors.As(err, &why) && why.Code == "localhost_protocol_conflict" {
			return receipt{}, h.deny(why)
		}
		return receipt{}, err
	}
	if prior, ok := h.state.Denials[h.run]; ok {
		return receipt{}, stop(prior.Code, prior.Reason)
	}
	robotsURL := &url.URL{Scheme: "https", Host: target.Host, Path: "/robots.txt"}
	robots, body, err := h.request(robotsURL, "policy")
	if err != nil {
		return receipt{}, err
	}
	rules, err := inspectRobots(robots, body)
	if err != nil {
		return receipt{}, err
	}
	if target.String() == robotsURL.String() {
		return robots, nil
	}
	h.delay = max(h.delay, rules.delay)
	return h.fetch(target, rules)
}

func (h *hostClient) fetch(target *url.URL, rules robotRules) (receipt, error) {
	const maxRedirects = 5
	seen := map[string]bool{}
	for {
		if !rules.permits(target) {
			return receipt{}, stop("robots_path_disallowed", "robots.txt disallows the requested path")
		}
		if seen[target.String()] || len(seen) > maxRedirects {
			return receipt{}, stop("redirect_denied", "redirect loop or redirect limit")
		}
		seen[target.String()] = true
		isTerms := termsPath(target)
		if isTerms && h.role != "policy" {
			return receipt{}, h.deny(stop("terms_page", "requested URL is a terms page"))
		}
		rec, _, err := h.request(target, h.role)
		if err != nil {
			return receipt{}, err
		}
		switch rec.Status {
		case 200:

			return rec, nil
		case 301, 302, 303, 307, 308:
			location := rec.Headers["location"]
			if location == "" {
				return receipt{}, stop("redirect_denied", "cached redirect has no usable Location")
			}
			if strings.ContainsAny(location, "\r\n\t\\#") || strings.HasPrefix(location, "///") {
				return receipt{}, stop("redirect_denied", "unsafe redirect location")
			}
			ref, err := url.Parse(location)
			if err != nil || ref.Host != "" && !strings.EqualFold(ref.Host, h.host) {
				return receipt{}, stop("redirect_denied", "redirect leaves the original approved host")
			}
			next, err := admit(target.ResolveReference(ref).String(), h.role)
			if err != nil || next.Host != h.host {
				return receipt{}, stop("redirect_denied", "redirect leaves the original approved HTTPS source scope")
			}
			target = next
		default:
			return receipt{}, stop("http_status", fmt.Sprintf("cached source response returned HTTP %d", rec.Status))
		}
	}
}

func (h *hostClient) cached(target *url.URL) (receipt, []byte, bool, error) {
	address := target.String()
	rec, body, found, err := loadReceipt(h.cache, address, "v5")
	if found || err != nil || h.legacy == "" {
		return rec, body, found, err
	}
	return loadReceipt(h.legacy, address, "legacy")
}

func (h *hostClient) request(target *url.URL, role string) (receipt, []byte, error) {
	now := h.now().UTC()
	if h.state.Breaker.After(now) {
		return receipt{}, nil, refusal{"host_parked", "source breaker is open", &h.state.Breaker}
	}
	prior, body, found, err := h.cached(target)
	if err != nil {
		return receipt{}, nil, err
	}
	if found && !retryStatus(prior.Status) {
		return prior, body, h.inspect(target, role, prior, body)
	}
	if found && retryStatus(prior.Status) {
		if why := responseRefusal(target, prior, body); why.Code != "" {
			return receipt{}, nil, h.deny(why)
		}
		received := timeFromEpoch(max(prior.ReceivedAt, prior.FetchedAt))
		until := retryUntil(prior.Headers["retry-after"], received)
		if until.After(now) {
			h.state.Breaker = until
			if err := h.store(h.file, h.state); err != nil {
				return receipt{}, nil, err
			}
			return receipt{}, nil, refusal{"host_parked", "cached response opens the source breaker", &until}
		}
	}
	if h.cacheOnly {
		return receipt{}, nil, stop("cache_miss", "no reusable receipt for the requested URL")
	}
	if err := h.reserve(target.String(), role); err != nil {
		return receipt{}, nil, err
	}
	ctx, cancel := context.WithTimeout(context.Background(), 30*time.Second)
	defer cancel()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, target.String(), nil)
	if err != nil {
		return receipt{}, nil, h.finishWithoutResponse(stop("url_denied", "unable to construct a GET"))
	}
	req.Header.Set("User-Agent", userAgent)
	res, err := h.http.RoundTrip(req)
	if err != nil {
		if h.host == "localhost:8077" {
			why := stop("localhost_protocol_conflict", "local port 8077 did not complete verified HTTPS; the documented endpoint uses HTTP")
			h.addDenial(h.run, why, h.now().UTC())
			return receipt{}, nil, h.finishWithoutResponse(why)
		}
		return receipt{}, nil, h.finishWithoutResponse(stop("transport_error", "HTTPS GET did not produce a response"))
	}
	defer res.Body.Close()
	body, bodyErr := io.ReadAll(io.LimitReader(res.Body, maxBody+1))
	bodyProblem := ""
	if len(body) > maxBody {
		body = body[:maxBody]
		bodyProblem = "response exceeds the retained body limit"
	}
	if bodyErr != nil {
		bodyProblem = "response body could not be read completely"
	}
	headers := map[string]string{
		"content-type": res.Header.Get("Content-Type"), "content-signal": strings.Join(res.Header.Values("Content-Signal"), ", "),
		"retry-after": res.Header.Get("Retry-After"), "x-robots-tag": strings.Join(res.Header.Values("X-Robots-Tag"), ", "),
		"location":               res.Header.Get("Location"),
		"content-signal-present": strconv.FormatBool(len(res.Header.Values("Content-Signal")) > 0),
	}
	received := h.now().UTC()
	rec := receipt{
		URL: target.String(), SHA256: hash(body), Status: res.StatusCode, Bytes: len(body), Headers: headers,
		FetchedAt: epoch(h.state.LastStart), FetchedByRole: role, FirstFetcher: h.fetcher,
		Origin: "v5", FirstOrigin: "v5", ReceivedAt: epoch(maxTime(received, h.state.LastStart)),
		AttemptRole: role, AttemptID: h.fetcher, BodyProblem: bodyProblem,
	}
	if found {
		rec.FetchedAt, rec.FetchedByRole = prior.FetchedAt, prior.FetchedByRole
		rec.FirstOrigin, rec.FirstFetcher = prior.FirstOrigin, prior.FirstFetcher
	}
	if err := saveResponse(h.cache, h.state.Pending.filename(), rec, body); err != nil {
		return receipt{}, nil, err
	}
	why, err := h.commitResponse(target, rec, body)
	if err != nil {
		return receipt{}, nil, err
	}
	if why.Code != "" && !returnTermsReceipt(why, role, target) {
		return receipt{}, nil, why
	}
	if retryStatus(rec.Status) {
		return receipt{}, nil, refusal{"host_parked", fmt.Sprintf("HTTP %d parks this source", rec.Status), &h.state.Breaker}
	}
	if rec.BodyProblem != "" {
		return receipt{}, nil, stop("incomplete_body", rec.BodyProblem)
	}
	return rec, body, nil
}

func (h *hostClient) finishWithoutResponse(why refusal) error {
	h.state.Pending = nil
	if err := h.store(h.file, h.state); err != nil {
		return err
	}
	return why
}

func (h *hostClient) reserve(address, role string) error {
	now := h.now().UTC()
	if next := h.state.LastStart.Add(h.delay); next.After(now) {
		wait := next.Sub(now)
		if wait > 30*time.Second {
			return refusal{"crawl_delay", "source spacing requires waiting until retry_at", &next}
		}
		h.sleep(wait)
		now = h.now().UTC()
		if next.After(now) {
			return refusal{"crawl_delay", "source spacing requires waiting until retry_at", &next}
		}
	}
	day := now.Format(time.DateOnly)
	// A wall-clock correction cannot reset the cap early.
	if h.state.UTCDay < day {
		h.state.UTCDay, h.state.Reads = day, 0
	}
	if limit := sources[h.host].dailyLimit; limit > 0 && h.state.Reads >= limit {
		previous, err := time.Parse(time.DateOnly, h.state.UTCDay)
		if err != nil {
			return stop("cache_integrity", "source read counter has an invalid UTC date")
		}
		next := previous.Add(24 * time.Hour)
		return refusal{"daily_read_cap", "source reached its daily new-read cap", &next}
	}
	h.state.LastStart = now
	h.state.Reads++
	h.state.Pending = &pendingRead{h.run, address, now, role, h.fetcher}
	return h.store(h.file, h.state)
}

func (h *hostClient) inspect(target *url.URL, role string, rec receipt, body []byte) error {
	if why := responseRefusal(target, rec, body); why.Code != "" {
		if !returnTermsReceipt(why, role, target) {
			return h.deny(why)
		}
		if _, err := h.record(why); err != nil {
			return err
		}
	}
	if rec.BodyProblem != "" {
		return stop("incomplete_body", rec.BodyProblem)
	}
	return nil
}

func returnTermsReceipt(why refusal, role string, target *url.URL) bool {
	return why.Code == "terms_page" && role == "policy" && target.Path != "/robots.txt"
}

func responseRefusal(target *url.URL, rec receipt, body []byte) refusal {
	switch {
	case strings.Contains(strings.ToLower(rec.Headers["content-type"]), "text/html") && hostRefusalTitle.Match(body),
		rec.Status == 401 || rec.Status == 403 || rec.Status == 451,
		noAI.MatchString(rec.Headers["x-robots-tag"]):
		return stop("crawler_block", "source returned a crawler or access block")
	case rec.Headers["content-signal"] != "" || rec.Headers["content-signal-present"] == "true":
		return stop("content_signal", "source returned a Content-Signal")
	case rec.Status == 200 && (termsPath(target) || termsTitle.Match(body)):
		return stop("terms_page", "source returned a terms page")
	case target.Path == "/robots.txt" && !retryStatus(rec.Status):
		_, err := inspectRobots(rec, body)
		var why refusal
		if errors.As(err, &why) {
			return why
		}
	}
	return refusal{}
}

func inspectRobots(rec receipt, body []byte) (robotRules, error) {
	switch rec.Status {
	case 200:
		if rec.BodyProblem != "" || strings.Contains(strings.ToLower(rec.Headers["content-type"]), "text/html") ||
			strings.HasPrefix(strings.TrimSpace(string(body)), "<") {
			return robotRules{}, stop("robots_invalid", "robots.txt returned markup or an incomplete body")
		}
		return readRobots(body)
	case 404, 410:
		return robotRules{}, nil
	default:
		return robotRules{}, stop("robots_unavailable", fmt.Sprintf("robots.txt returned HTTP %d", rec.Status))
	}
}

func retryStatus(status int) bool { return status == 429 || status >= 500 && status <= 599 }

func retryUntil(header string, at time.Time) time.Time {
	at = at.UTC()
	minimum := at.Add(time.Hour)
	value := strings.TrimSpace(header)
	if seconds, err := strconv.ParseUint(value, 10, 64); err == nil || errors.Is(err, strconv.ErrRange) {
		const maxDurationSeconds = uint64((1<<63 - 1) / time.Second)
		return maxTime(minimum, at.Add(time.Duration(min(seconds, maxDurationSeconds))*time.Second))
	}
	if until, err := http.ParseTime(value); err == nil {
		return maxTime(minimum, until)
	}
	return minimum
}

func maxTime(a, b time.Time) time.Time {
	if a.After(b) {
		return a
	}
	return b
}

func timeFromEpoch(value float64) time.Time {
	seconds := int64(value)
	return time.Unix(seconds, int64((value-float64(seconds))*1e9)).UTC()
}

func epoch(at time.Time) float64 {
	return float64(at.Unix()) + float64(at.Nanosecond())/1e9
}
