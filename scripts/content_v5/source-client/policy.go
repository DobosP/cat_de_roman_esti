package main

import (
	"fmt"
	"net/url"
	"regexp"
	"strconv"
	"strings"
	"time"
	"unicode/utf8"
)

const userAgent = "cat-de-roman-esti-content-research/5 (+https://github.com/DobosP/cat_de_roman_esti)"
const product = "cat-de-roman-esti-content-research"

type source struct {
	delay      time.Duration
	dailyLimit int
	policyOnly bool
}

var sources = map[string]source{
	dumpHost:                    {10 * time.Second, 20, false},
	"ro.wikipedia.org":          {10 * time.Second, 20, false},
	"ro.wiktionary.org":         {10 * time.Second, 20, false},
	"www.wikidata.org":          {10 * time.Second, 20, false},
	"raw.githubusercontent.com": {2 * time.Second, 0, false},
	"localhost:8077":            {2 * time.Second, 0, false},
	"foundation.wikimedia.org":  {10 * time.Second, 20, true},
	"creativecommons.org":       {2 * time.Second, 0, true},
	"docs.github.com":           {2 * time.Second, 0, true},
}

var githubPolicyPath = regexp.MustCompile(`^/[a-z]{2}(?:-[a-z]{2})?/site-policy/(?:acceptable-use-policies|github-terms|privacy-policies)/[^/]+`)
var hostRefusalTitle = regexp.MustCompile(`(?is)<title\b[^>]*>\s*(?:just a moment|access denied|request blocked|automated access denied|crawler access denied)(?:\.{3}|!|\s|\s*<)`)
var termsTitle = regexp.MustCompile(`(?is)<title\b[^>]*>\s*(?:(?:policy\s*:\s*)?terms of (?:use|service)|(?:[^<>:\n]+:\s*)?termeni(?:i)? (?:de utilizare|și condiții))(?:\s|<)`)
var noAI = regexp.MustCompile(`(?i)(?:^|[\s,:;])(?:noai|noimageai)(?:$|[\s,;])`)

func admit(raw string, role string) (*url.URL, error) {
	if raw == "" || len(raw) > 4096 || strings.ContainsAny(raw, "#\\") {
		return nil, stop("url_denied", "use an approved absolute URL without a fragment")
	}
	for _, c := range raw {
		if c < 33 || c > 126 {
			return nil, stop("url_denied", "use printable ASCII and percent-encode non-ASCII URL bytes")
		}
	}
	target, err := url.Parse(raw)
	if err != nil || target.User != nil || target.Opaque != "" {
		return nil, stop("url_denied", "malformed URL or URL credentials")
	}
	target.Host = strings.ToLower(target.Host)
	if target.Host == "wikidata.org" {
		// ADR-0230 identifies www as canonical. No request goes to the bare hostname.
		target.Host = "www.wikidata.org"
	}
	policy, exists := sources[target.Host]
	if !exists {
		return nil, stop("url_denied", "host is outside the V5 source grant")
	}
	if target.Scheme == "http" && target.Host == "localhost:8077" {
		return target, stop("localhost_protocol_conflict", "port 8077 is documented as HTTP and V5 requires HTTPS")
	}
	if target.Scheme != "https" {
		return nil, stop("url_denied", "the V5 source grant requires HTTPS")
	}
	if target.Path == "" {
		target.Path = "/"
	}
	escaped := strings.ToUpper(target.EscapedPath())
	if !utf8.ValidString(target.Path) || strings.Contains(target.Path, "//") ||
		strings.Contains(escaped, "%2F") || strings.Contains(escaped, "%5C") ||
		strings.Contains(escaped, "%25") {
		return nil, stop("url_denied", "ambiguous URL path")
	}
	for _, r := range target.Path {
		if r < 32 || r == 127 {
			return nil, stop("url_denied", "control character in URL path")
		}
	}
	for _, segment := range strings.Split(target.Path, "/") {
		if segment == "." || segment == ".." {
			return nil, stop("url_denied", "URL path contains a dot segment")
		}
	}
	if _, err := url.QueryUnescape(target.RawQuery); err != nil {
		return nil, stop("url_denied", "malformed URL query")
	}
	if target.Host == dumpHost {
		_, fileAllowed := datedDump(target)
		if (target.Path != "/robots.txt" && !fileAllowed) || strings.Contains(escaped, "%") ||
			target.RawQuery != "" || target.ForceQuery {
			return nil, stop("url_denied", "Wikimedia dump reads require an approved, literally dated file or robots.txt")
		}
	}
	target.RawPath = normalizeOctets(target.EscapedPath())
	target.RawQuery = normalizeOctets(target.RawQuery)
	target.ForceQuery = false
	if target.Path == "/robots.txt" && target.RawQuery != "" {
		return nil, stop("url_denied", "robots.txt does not take a query")
	}
	if policy.policyOnly {
		if role != "policy" {
			return nil, stop("policy_only", "this host is approved for policy inspection only")
		}
		if target.Path != "/robots.txt" && !policyPath(target) {
			return nil, stop("policy_only", "this path is outside the primary terms and licence grant")
		}
	}
	if target.Host == "raw.githubusercontent.com" && target.Path != "/robots.txt" {
		parts := strings.Split(target.EscapedPath(), "/")
		if len(parts) < 5 || parts[1] != "hermitdave" || parts[2] != "FrequencyWords" ||
			parts[len(parts)-1] == "" || strings.Contains(escaped, "%") || target.RawQuery != "" {
			return nil, stop("url_denied", "GitHub raw reads are limited to hermitdave/FrequencyWords")
		}
	}
	return target, nil
}

func policyPath(target *url.URL) bool {
	path := strings.ToLower(target.Path)
	if target.RawQuery != "" {
		return false
	}
	switch target.Host {
	case "foundation.wikimedia.org":
		for _, title := range []string{"terms_of_use", "privacy_policy", "licensing_policy", "copyright_policy"} {
			base := "/wiki/policy:" + title
			if path == base || strings.HasPrefix(path, base+"/") {
				return true
			}
		}
	case "creativecommons.org":
		return strings.HasPrefix(path, "/licenses/") || strings.HasPrefix(path, "/publicdomain/")
	case "docs.github.com":
		return githubPolicyPath.MatchString(path)
	}
	return false
}

func termsPath(target *url.URL) bool {
	p := strings.ToLower(target.Path)
	if target.Host == "foundation.wikimedia.org" && strings.HasPrefix(p, "/wiki/policy:terms_of_use") {
		return true
	}
	if target.Host == "docs.github.com" && strings.Contains(p, "/site-policy/github-terms/github-terms-") {
		return true
	}
	return strings.HasPrefix(p, "/wiki/wikipedia:termeni") ||
		strings.HasPrefix(p, "/wiki/wikționar:termeni") ||
		strings.HasPrefix(p, "/wiki/wikidata:terms_of_use") ||
		p == "/terms" || p == "/terms-of-service" || p == "/terms-of-use"
}

func normalizeOctets(path string) string {
	var result strings.Builder
	for i := 0; i < len(path); i++ {
		c := path[i]
		if c == '%' && i+2 < len(path) {
			if code, err := strconv.ParseUint(path[i+1:i+3], 16, 8); err == nil {
				c = byte(code)
				if !strings.ContainsRune("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~", rune(c)) {
					fmt.Fprintf(&result, "%%%02X", c)
					i += 2
					continue
				}
				i += 2
			}
		}
		if c >= 128 || c <= 32 || c == 127 {
			fmt.Fprintf(&result, "%%%02X", c)
		} else {
			result.WriteByte(c)
		}
	}
	return result.String()
}

type robotRules struct {
	rules []robotRule
	delay time.Duration
}

type robotRule struct {
	pattern *regexp.Regexp
	length  int
	allow   bool
}

var aiCrawlers = map[string]bool{
	"gptbot": true, "chatgpt-user": true, "oai-searchbot": true, "claudebot": true,
	"claude-searchbot": true, "claude-user": true, "anthropic-ai": true, "google-extended": true,
	"ccbot": true, "perplexitybot": true, "perplexity-user": true, "meta-externalagent": true,
	"meta-externalfetcher": true, "bytespider": true, "amazonbot": true, "applebot-extended": true,
	"cohere-ai": true, "duckassistbot": true, "youbot": true,
}

func readRobots(body []byte) (robotRules, error) {
	if !utf8.Valid(body) || strings.ContainsRune(string(body), 0) {
		return robotRules{}, stop("robots_invalid", "robots.txt is malformed")
	}
	var own, wildcard robotRules
	var agents []string
	hasRules, hasOwnGroup := false, false
	for _, line := range strings.Split(strings.TrimPrefix(string(body), "\uFEFF"), "\n") {
		line, _, _ = strings.Cut(line, "#")
		key, value, ok := strings.Cut(line, ":")
		if !ok {
			continue
		}
		value = strings.TrimSpace(value)
		switch strings.ToLower(strings.TrimSpace(key)) {
		case "content-signal":
			return robotRules{}, stop("content_signal", "robots.txt declares a Content-Signal")
		case "user-agent":
			if hasRules {
				agents = nil
				hasRules = false
			}
			agent := strings.ToLower(value)
			if aiCrawlers[agent] {
				return robotRules{}, stop("ai_crawler_group", "robots.txt declares an AI-crawler group")
			}
			if agent == product {
				hasOwnGroup = true
			}
			if agent != "" {
				agents = append(agents, agent)
			}
		case "allow", "disallow", "crawl-delay":
			if len(agents) == 0 {
				continue
			}
			hasRules = true
			for _, agent := range agents {
				if agent == "*" {
					if err := wildcard.add(key, value); err != nil {
						return robotRules{}, err
					}
				}
				if agent == product {
					if err := own.add(key, value); err != nil {
						return robotRules{}, err
					}
				}
			}
		}
	}
	// Specific rules apply when present. A stricter wildcard delay still bounds this client.
	if hasOwnGroup {
		own.delay = max(own.delay, wildcard.delay)
		return own, nil
	}
	wildcard.delay = max(wildcard.delay, own.delay)
	return wildcard, nil
}

func (rules *robotRules) add(key, value string) error {
	key = strings.ToLower(strings.TrimSpace(key))
	if value == "" {
		return nil
	}
	if key == "crawl-delay" {
		delay, err := time.ParseDuration(value + "s")
		if err != nil || delay < 0 {
			return stop("robots_invalid", "robots.txt declares an invalid crawl delay")
		}
		rules.delay = max(rules.delay, delay)
		return nil
	}
	if !strings.HasPrefix(value, "/") {
		return nil
	}
	normalized := normalizeOctets(value)
	if len(normalized) > 4096 || len(rules.rules) >= 8192 {
		return stop("robots_invalid", "robots.txt exceeds the supported rule bounds")
	}
	path, anchored := strings.CutSuffix(normalized, "$")
	parts := strings.Split(path, "*")
	for i, part := range parts {
		parts[i] = regexp.QuoteMeta(part)
	}
	pattern := "^" + strings.Join(parts, ".*")
	if anchored {
		pattern += "$"
	}
	matcher, err := regexp.Compile(pattern)
	if err != nil {
		return stop("robots_invalid", "robots.txt contains an unsupported path pattern")
	}
	rules.rules = append(rules.rules, robotRule{matcher, len(strings.ReplaceAll(path, "*", "")), key == "allow"})
	return nil
}

func (rules robotRules) permits(target *url.URL) bool {
	path := target.RequestURI()
	longest, allow := -1, true
	for _, rule := range rules.rules {
		if rule.pattern.MatchString(path) && (rule.length > longest || rule.length == longest && rule.allow) {
			longest, allow = rule.length, rule.allow
		}
	}
	return allow
}
