// Package doccheck ports the fleet tracked-Markdown governance gate locally.
// History remains report-only; checks do not rewrite documentation.
package doccheck

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"unicode"
)

var history = regexp.MustCompile(`(?i)(^|/)(docs/adr|decisions|adr|handoffs|handover|reviews|sessions|tasks|log|logs|runs|archive|_archive|app-sessions|fixtures)(/|$)|(^|/)(WORKLOG\.md|CHANGELOG\.md)$|(^|/)[^/]*\d{4}-\d{2}(-\d{2})?[^/]*\.md$`)
var links = regexp.MustCompile(`\[[^\]]*\]\(([^)\s#]+)(#[^)]*)?\)`)
var scheme = regexp.MustCompile(`^[a-z]+:`)
var stale = regexp.MustCompile(`(?i)\b(opus 4(\.\d)?|sonnet 4(\.\d)?|claude 3(\.\d)?|claude-3|claude-opus-4|claude-sonnet-4|gpt-4o?\b|gpt-5(?:\.[0-5])?|gpt-6|o3(-mini|-pro)?\b|o4-mini|haiku 3(\.\d)?|claude-fable-5|fable 5\b|claude 5\.0)`)
var retired = regexp.MustCompile(`(?i)ops(?:\.ps1)?\s+(resume|pickup|transfer|takeover|host|coordinator|canary|tabs|tasks|status|list|new|open|reopen|close|scope|checkpoint|snapshot|stop|park|update|provider-update|pin|ui)|\bsync\s+--handoff\b`)
var staleGuard = regexp.MustCompile(`(?i)\bnever\b|\bno longer\b|\bretired\b|\bstale\b`)
var retiredGuard = regexp.MustCompile(`(?i)retired|exit 2|ops halt`)

type Report struct {
	Files        int      `json:"files"`
	DeadLinks    []string `json:"dead_links"`
	StaleTerms   []string `json:"stale_terms"`
	RetiredVerbs []string `json:"retired_verbs"`
	Orphans      []string `json:"orphans"`
	Budgets      []string `json:"budgets"`
}

func word(b byte) bool {
	return b == '_' || b >= 'a' && b <= 'z' || b >= 'A' && b <= 'Z' || b >= '0' && b <= '9'
}
func StaleTerms(line string) []string {
	out := []string{}
	for _, at := range stale.FindAllStringIndex(line, -1) {
		term := strings.ToLower(line[at[0]:at[1]])
		suffix := line[at[1]:]
		if term == "gpt-4o" && strings.HasPrefix(suffix, "-mini-tts") {
			continue
		}
		if strings.HasPrefix(term, "gpt-5") && len(suffix) > 0 && (word(suffix[0]) || suffix[0] == '.') {
			continue
		}
		if term == "claude-fable-5" && strings.HasPrefix(suffix, "-1") {
			continue
		}
		if term == "fable 5" && strings.HasPrefix(suffix, ".") {
			continue
		}
		out = append(out, line[at[0]:at[1]])
	}
	return out
}
func RetiredVerbs(line string) []string {
	out := []string{}
	for _, at := range retired.FindAllStringIndex(line, -1) {
		if at[0] > 0 && (word(line[at[0]-1]) || line[at[0]-1] == '-') {
			continue
		}
		if at[1] < len(line) {
			next := rune(line[at[1]])
			if !unicode.IsSpace(next) && !strings.ContainsRune("`.,;:!?)", next) {
				continue
			}
		}
		out = append(out, line[at[0]:at[1]])
	}
	return out
}
func guarded(lines []string, i int, p *regexp.Regexp) bool {
	for _, n := range []int{i, i - 1} {
		if n >= 0 && p.MatchString(lines[n]) {
			return true
		}
	}
	return false
}
func Check(root string) (Report, error) {
	r := Report{DeadLinks: []string{}, StaleTerms: []string{}, RetiredVerbs: []string{}, Orphans: []string{}, Budgets: []string{}}
	root, err := filepath.Abs(root)
	if err != nil {
		return r, err
	}
	raw, err := exec.Command("git", "-C", root, "ls-files", "-z", "*.md", "**/*.md").Output()
	if err != nil {
		return r, fmt.Errorf("tracked Markdown inventory unavailable")
	}
	files := []string{}
	texts := map[string]string{}
	for _, f := range strings.Split(string(raw), "\x00") {
		if f == "" {
			continue
		}
		data, err := os.ReadFile(filepath.Join(root, f))
		if err != nil {
			return r, err
		}
		texts[f] = string(data)
		if !history.MatchString(f) {
			files = append(files, f)
		}
	}
	sort.Strings(files)
	r.Files = len(files)
	for _, f := range files {
		lines := strings.Split(strings.TrimSuffix(texts[f], "\n"), "\n")
		for i, line := range lines {
			for _, at := range links.FindAllStringSubmatchIndex(line, -1) {
				if at[0] > 0 && line[at[0]-1] == '!' {
					continue
				}
				target := line[at[2]:at[3]]
				if scheme.MatchString(target) || strings.HasPrefix(target, "mailto") {
					continue
				}
				path := filepath.Clean(filepath.Join(root, filepath.Dir(f), target))
				if _, err := os.Stat(path); err != nil {
					r.DeadLinks = append(r.DeadLinks, fmt.Sprintf("%s:%d: %s", f, i+1, target))
				}
			}
			if !guarded(lines, i, staleGuard) {
				for _, term := range StaleTerms(line) {
					r.StaleTerms = append(r.StaleTerms, fmt.Sprintf("%s:%d: %s", f, i+1, term))
				}
			}
			if !guarded(lines, i, retiredGuard) {
				for _, verb := range RetiredVerbs(line) {
					r.RetiredVerbs = append(r.RetiredVerbs, fmt.Sprintf("%s:%d: %s", f, i+1, verb))
				}
			}
		}
	}
	candidates := []string{}
	for _, f := range files {
		if strings.HasPrefix(f, "docs/") {
			candidates = append(candidates, f)
		}
	}
	frontier := []string{"README.md", "AGENTS.md", "docs/agent-map.md"}
	seen := map[string]bool{}
	reachable := map[string]bool{}
	for len(frontier) > 0 {
		text := ""
		for _, f := range frontier {
			text += texts[f]
			seen[f] = true
		}
		frontier = nil
		for _, f := range candidates {
			if reachable[f] {
				continue
			}
			match := strings.Contains(text, f) || strings.Contains(text, filepath.Base(f))
			for ancestor := filepath.Dir(f); ancestor != "."; ancestor = filepath.Dir(ancestor) {
				match = match || strings.Contains(text, ancestor)
			}
			if match {
				reachable[f] = true
				if !seen[f] {
					frontier = append(frontier, f)
				}
			}
		}
	}
	for _, f := range candidates {
		if !reachable[f] && f != "docs/agent-map.md" {
			r.Orphans = append(r.Orphans, f+":1: unreachable from README.md, AGENTS.md or docs/agent-map.md")
		}
	}
	for f, limit := range map[string]int{"AGENTS.md": 80, "CLAUDE.md": 12, "docs/STATUS.md": 120, "docs/agent-map.md": 60, "docs/agent-testing.md": 80} {
		data, err := os.ReadFile(filepath.Join(root, f))
		if os.IsNotExist(err) {
			continue
		}
		if err != nil {
			return r, err
		}
		lines := strings.Split(strings.TrimSuffix(string(data), "\n"), "\n")
		count := len(lines)
		if f == "CLAUDE.md" {
			count = 0
			for _, line := range lines {
				if strings.TrimSpace(line) != "" {
					count++
				}
			}
		}
		if count > limit {
			r.Budgets = append(r.Budgets, fmt.Sprintf("%s: %d lines exceeds %d", f, count, limit))
		}
	}
	sort.Strings(r.Budgets)
	return r, nil
}
func (r Report) Green() bool {
	return len(r.DeadLinks)+len(r.StaleTerms)+len(r.RetiredVerbs)+len(r.Orphans)+len(r.Budgets) == 0
}
