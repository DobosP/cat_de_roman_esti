package httpgolden

import (
	"context"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"net/url"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/browserplan"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

func same(a, b any) bool {
	x, _ := json.Marshal(a)
	y, _ := json.Marshal(b)
	return string(x) == string(y)
}
func require(ok bool, message string) error {
	if !ok {
		return fmt.Errorf("%s", message)
	}
	return nil
}
func queryFor(game string) string {
	q := url.Values{"seed": {"38"}, "difficulty": {"usor"}}
	if game == "intrusul" || game == "perechi" {
		q.Set("starter", "1")
	}
	return q.Encode()
}
func checked(ctx context.Context, c *Client, r Request, status int, runtime bool) (Response, error) {
	res, err := c.Do(ctx, r)
	if err != nil {
		return Response{}, err
	}
	if res.Status != status {
		return Response{}, fmt.Errorf("%s %s: wanted HTTP %d, got %d", r.Method, strings.Split(r.Path, "?")[0], status, res.Status)
	}
	if runtime && res.Headers.Get("X-Cat-Runtime") != "go" && !(status == 413 && strings.EqualFold(res.Headers.Get("Server"), "caddy")) {
		return Response{}, fmt.Errorf("response lacks Go runtime header")
	}
	return res, nil
}
func obj(ctx context.Context, c *Client, method, path string, body any, status int, runtime bool) (map[string]any, error) {
	res, err := checked(ctx, c, JSONRequest(method, path, body), status, runtime)
	if err != nil {
		return nil, err
	}
	return res.Object()
}
func score(v any) bool {
	n, ok := v.(json.Number)
	if !ok {
		return false
	}
	_, err := n.Int64()
	return err == nil
}
func final(state map[string]any) error {
	return require(state["won"] == true && score(state["score"]), "seeded winning journey or integer score failed")
}
func Smoke(ctx context.Context, client *Client, data *content.Content, staticRoot string) (Report, error) {
	start := time.Now()
	report := Report{Mode: "smoke", LegalSHA256: map[string]string{}}
	health, err := obj(ctx, client, "GET", "/api/health", nil, 200, true)
	if err != nil {
		return report, err
	}
	if !same(health["concepts"], len(data.Nodes)) || health["ok"] != true || health["version"] != data.AppVersion {
		return report, fmt.Errorf("health inventory or version drift")
	}
	manifest, err := obj(ctx, client, "GET", "/api/manifest", nil, 200, true)
	if err != nil {
		return report, err
	}
	if !same(manifest, data.Manifest) {
		return report, fmt.Errorf("served manifest differs from reviewed release")
	}
	report.ContentHash = manifest["content_hash"].(string)
	categories, err := obj(ctx, client, "GET", "/api/categories", nil, 200, true)
	if err != nil {
		return report, err
	}
	rows, ok := categories["categories"].([]any)
	if !ok || len(rows) != len(data.CategoryOrder) {
		return report, fmt.Errorf("category inventory drift")
	}
	me, err := obj(ctx, client, "GET", "/api/me", nil, 200, true)
	if err != nil {
		return report, err
	}
	if me["accounts_enabled"] != false || me["authenticated"] != false || me["user"] != nil {
		return report, fmt.Errorf("anonymous account gate failed")
	}
	shell, err := checked(ctx, client, JSONRequest("GET", "/", nil), 200, true)
	if err != nil {
		return report, err
	}
	expected, err := os.ReadFile(filepath.Join(staticRoot, "index.html"))
	if err != nil {
		return report, err
	}
	if string(expected) != string(shell.Raw) {
		return report, fmt.Errorf("HTML shell differs from release build")
	}
	cache := strings.ToLower(shell.Headers.Get("Cache-Control"))
	if !strings.Contains(cache, "no-cache") && !strings.Contains(cache, "max-age=0") {
		return report, fmt.Errorf("HTML shell must revalidate")
	}
	head, err := checked(ctx, client, JSONRequest("HEAD", "/", nil), 200, true)
	if err != nil {
		return report, err
	}
	if len(head.Raw) != 0 || head.Headers.Get("Cache-Control") != shell.Headers.Get("Cache-Control") {
		return report, fmt.Errorf("HEAD shell/cache mismatch")
	}
	assets := map[string]bool{}
	for _, row := range regexp.MustCompile(`(?:src|href)="(/assets/[^"]+)"`).FindAllSubmatch(shell.Raw, -1) {
		assets[string(row[1])] = true
	}
	raw, err := os.ReadFile(filepath.Join(staticRoot, ".vite", "manifest.json"))
	if err != nil {
		return report, err
	}
	var chunks map[string]struct {
		File   string   `json:"file"`
		CSS    []string `json:"css"`
		Assets []string `json:"assets"`
	}
	if err = json.Unmarshal(raw, &chunks); err != nil {
		return report, err
	}
	for _, chunk := range chunks {
		for _, name := range append(append([]string{chunk.File}, chunk.CSS...), chunk.Assets...) {
			if strings.HasPrefix(name, "assets/") {
				assets["/"+name] = true
			}
		}
	}
	if len(assets) == 0 || len(assets) > 128 {
		return report, fmt.Errorf("static asset inventory empty or exceeds 128")
	}
	paths := []string{}
	for path := range assets {
		paths = append(paths, path)
	}
	sort.Strings(paths)
	for _, path := range paths {
		if strings.Contains(path, "..") || strings.ContainsAny(path, "\\?#") {
			return report, fmt.Errorf("invalid built asset path")
		}
		res, err := checked(ctx, client, JSONRequest("GET", path, nil), 200, true)
		if err != nil {
			return report, err
		}
		expected, err := os.ReadFile(filepath.Join(staticRoot, strings.TrimPrefix(path, "/")))
		if err != nil {
			return report, err
		}
		if string(expected) != string(res.Raw) || !strings.Contains(res.Headers.Get("Cache-Control"), "immutable") {
			return report, fmt.Errorf("asset bytes or immutable cache drift")
		}
		head, err := checked(ctx, client, JSONRequest("HEAD", path, nil), 200, true)
		if err != nil {
			return report, err
		}
		if len(head.Raw) != 0 {
			return report, fmt.Errorf("HEAD asset returned body")
		}
		if etag := res.Headers.Get("ETag"); etag != "" {
			conditional, err := checked(ctx, client, Request{Method: "GET", Path: path, Headers: map[string]string{"If-None-Match": etag}}, 304, true)
			if err != nil {
				return report, err
			}
			if len(conditional.Raw) != 0 {
				return report, fmt.Errorf("conditional asset returned body")
			}
		}
	}
	report.AssetsVerified = len(paths)
	for _, path := range []string{"/legal/privacy", "/legal/terms"} {
		res, err := checked(ctx, client, JSONRequest("GET", path, nil), 200, true)
		if err != nil {
			return report, err
		}
		lower := strings.ToLower(string(res.Raw))
		if !strings.Contains(lower, "<!doctype html>") || strings.Contains(string(res.Raw), "[[PLACEHOLDER") {
			return report, fmt.Errorf("legal notice unconfigured or not HTML")
		}
		if path == "/legal/privacy" && (!strings.Contains(lower, "mailto:") || !strings.Contains(string(res.Raw), "Operatorul serviciului este")) {
			return report, fmt.Errorf("legal operator/contact unconfigured")
		}
		report.LegalSHA256[path] = fmt.Sprintf("%x", sha256.Sum256(res.Raw))
	}
	submissions, err := obj(ctx, client, "POST", "/api/submissions", map[string]any{}, 503, true)
	if err != nil {
		return report, err
	}
	if submissions["detail"] == nil {
		return report, fmt.Errorf("submissions gate failed")
	}
	if _, err = checked(ctx, client, JSONRequest("GET", "/api/release-smoke-not-found", nil), 404, true); err != nil {
		return report, err
	}
	if _, err = checked(ctx, client, Request{Method: "POST", Path: "/api/wordgames/intrusul/games", Body: strings.Repeat(" ", 65537)}, 413, true); err != nil {
		return report, err
	}
	for _, game := range browserplan.Games {
		fixture, err := browserplan.Solution(data, game, "", "")
		if err != nil {
			return report, err
		}
		base := "/api/wordgames/" + game + "/games"
		state, err := obj(ctx, client, "POST", base+"?"+queryFor(game), nil, 200, true)
		if err != nil {
			return report, err
		}
		id, ok := state["game_id"].(string)
		if !ok || id == "" || state["won"] == true || state["score"] != nil || state["solution"] != nil {
			return report, fmt.Errorf("new game leaked terminal/private state")
		}
		path := base + "/" + id
		resumed, err := obj(ctx, client, "GET", path, nil, 200, true)
		if err != nil {
			return report, err
		}
		if !same(state, resumed) {
			return report, fmt.Errorf("game resume drift")
		}
		if game == "alchimie" {
			for _, pair := range fixture.HintSetup[:3] {
				if _, err = obj(ctx, client, "POST", path+"/combine", pair, 200, true); err != nil {
					return report, err
				}
			}
			_, err = obj(ctx, client, "POST", path+"/hint", map[string]any{}, 200, true)
		} else if game == "lant" {
			_, err = obj(ctx, client, "POST", path+"/hint", map[string]any{}, 200, true)
		} else {
			state, err = obj(ctx, client, "POST", path+"/"+fixture.Practice.Action, fixture.Practice.Payload, 200, true)
			if err != nil {
				return report, err
			}
			if game == "perechi" {
				ids := tileIDs(state["tiles"])
				played := fixture.Practice.Payload["ids"].([]string)
				solved := map[string]bool{}
				for _, step := range fixture.Steps {
					solved[pairKey(step.Payload["ids"].([]string))] = true
				}
				var wrong []string
				for i, a := range ids {
					for _, b := range ids[i+1:] {
						p := []string{a, b}
						if !solved[pairKey(p)] && pairKey(p) != pairKey(played) {
							wrong = p
							break
						}
					}
					if wrong != nil {
						break
					}
				}
				if wrong == nil {
					return report, fmt.Errorf("Perechi has no second wrong pair")
				}
				state, err = obj(ctx, client, "POST", path+"/match", map[string]any{"ids": wrong}, 200, true)
			}
			if err != nil {
				return report, err
			}
			if game == "conexiuni" {
				a := fixture.Steps[0].Payload["ids"].([]string)
				b := fixture.Steps[1].Payload["ids"].([]string)
				state, err = obj(ctx, client, "POST", path+"/guess", map[string]any{"ids": append(append([]string{}, a[:2]...), b[:2]...)}, 200, true)
			}
			if err != nil {
				return report, err
			}
			if game == "contexto" {
				g := graph.New(data)
				target := g.Resolve(fixture.Steps[0].Payload["text"].(string))
				for _, node := range g.AllIDs() {
					attempts, _ := state["attempts"].(json.Number)
					if n, _ := attempts.Int64(); n >= 3 {
						break
					}
					if node != target {
						state, err = obj(ctx, client, "POST", path+"/guess", map[string]any{"text": node}, 200, true)
						if err != nil {
							return report, err
						}
					}
				}
				_, err = obj(ctx, client, "POST", path+"/clue", map[string]any{}, 200, true)
			} else {
				action := "hint"
				if game == "conexiuni" {
					action = "clue"
				}
				_, err = obj(ctx, client, "POST", path+"/"+action, map[string]any{}, 200, true)
			}
		}
		if err != nil {
			return report, err
		}
		for _, step := range fixture.Steps {
			state, err = obj(ctx, client, "POST", path+"/"+step.Action, step.Payload, 200, true)
			if err != nil {
				return report, err
			}
		}
		if err = final(state); err != nil {
			return report, err
		}
		terminal, err := obj(ctx, client, "GET", path, nil, 200, true)
		if err != nil {
			return report, err
		}
		if terminal["won"] != true || !same(terminal["score"], state["score"]) {
			return report, fmt.Errorf("terminal resume drift")
		}
		report.GamesCompleted++
	}
	base := "/api/alchimie/explore"
	state, err := obj(ctx, client, "POST", base, map[string]any{}, 200, true)
	if err != nil {
		return report, err
	}
	path := base + "/" + state["game_id"].(string)
	resumed, err := obj(ctx, client, "GET", path, nil, 200, true)
	if err != nil {
		return report, err
	}
	if !same(resumed, state) {
		return report, fmt.Errorf("exploration resume drift")
	}
	if _, err = obj(ctx, client, "POST", path+"/hint", map[string]any{}, 200, true); err != nil {
		return report, err
	}
	hinted, err := obj(ctx, client, "POST", path+"/hint", map[string]any{}, 200, true)
	if err != nil {
		return report, err
	}
	hint, ok := hinted["hint"].(map[string]any)
	if !ok {
		return report, fmt.Errorf("exploration hint missing")
	}
	pair, ok := hint["pair"].([]any)
	if !ok || len(pair) != 2 {
		return report, fmt.Errorf("exploration hint pair missing")
	}
	state, err = obj(ctx, client, "POST", path+"/combine", map[string]any{"a": pair[0].(map[string]any)["id"], "b": pair[1].(map[string]any)["id"]}, 200, true)
	if err != nil {
		return report, err
	}
	if len(state["discovered"].([]any)) != 1 {
		return report, fmt.Errorf("exploration craft failed")
	}
	resumed, err = obj(ctx, client, "GET", path, nil, 200, true)
	if err != nil {
		return report, err
	}
	if !same(resumed["progress"], state["progress"]) {
		return report, fmt.Errorf("checkpoint drift")
	}
	restored, err := obj(ctx, client, "POST", base, map[string]any{"progress": state["progress"], "goal_id": state["goal_id"]}, 200, true)
	if err != nil {
		return report, err
	}
	if restored["game_id"] == state["game_id"] || !same(restored["progress"], state["progress"]) || !same(restored["inventory"], resumed["inventory"]) {
		return report, fmt.Errorf("exploration restore drift")
	}
	report.OK = true
	report.ExplorationRestore = true
	report.Requests = client.Count()
	report.ElapsedSeconds = time.Since(start).Seconds()
	return report, nil
}
func tileIDs(raw any) []string {
	ids := []string{}
	for _, row := range raw.([]any) {
		ids = append(ids, row.(map[string]any)["id"].(string))
	}
	return ids
}
func pairKey(ids []string) string {
	a := append([]string{}, ids...)
	sort.Strings(a)
	return strings.Join(a, "\x00")
}

// Capture records an explicit reference origin. The caller must name that
// reference; capturing the candidate itself is not independent parity evidence.
func Capture(ctx context.Context, client *Client, data *content.Content, reference string) (*Corpus, error) {
	if reference == "" {
		return nil, fmt.Errorf("capture requires a reference description")
	}
	c := &Corpus{SchemaVersion: 1, Reference: reference, Sources: data.Sources, Cases: []Case{}}
	aliases := map[string]string{}
	record := func(r Request) (map[string]any, error) {
		res, err := client.Do(ctx, r)
		if err != nil {
			return nil, err
		}
		body, _ := res.Body.(map[string]any)
		if body != nil {
			if sid, ok := body["game_id"].(string); ok {
				if _, known := aliases[sid]; !known {
					aliases[sid] = fmt.Sprintf("session-%d", len(aliases))
				}
			}
		}
		r.Path = replace(r.Path, aliases)
		r.Body = replace(r.Body, aliases)
		c.Cases = append(c.Cases, Case{r, res.Status, normalized(res.Body, aliases)})
		return body, nil
	}
	for _, path := range []string{"/api/health", "/api/manifest", "/api/categories", "/api/me", "/openapi.json", "/api/nope"} {
		if _, err := record(JSONRequest("GET", path, nil)); err != nil {
			return nil, err
		}
	}
	for _, game := range browserplan.Games {
		plan, err := browserplan.Solution(data, game, "", "")
		if err != nil {
			return nil, err
		}
		base := "/api/wordgames/" + game + "/games"
		state, err := record(JSONRequest("POST", base+"?"+queryFor(game), nil))
		if err != nil {
			return nil, err
		}
		id, ok := state["game_id"].(string)
		if !ok {
			return nil, fmt.Errorf("reference create failed")
		}
		path := base + "/" + id
		for _, r := range []Request{JSONRequest("GET", path, nil), JSONRequest("GET", base+"/missing", nil), {Method: "POST", Path: base + "?seed=bad"}} {
			if _, err = record(r); err != nil {
				return nil, err
			}
		}
		for _, raw := range []string{"", "null", "[]", "{}", "{malformed"} {
			if _, err = record(Request{Method: "POST", Path: path + "/" + plan.Steps[0].Action, Body: raw}); err != nil {
				return nil, err
			}
		}
		for _, step := range plan.Steps {
			if _, err = record(JSONRequest("POST", path+"/"+step.Action, step.Payload)); err != nil {
				return nil, err
			}
		}
		if _, err = record(JSONRequest("GET", path, nil)); err != nil {
			return nil, err
		}
	}
	for _, raw := range []string{"null", "[]", "{\"extra\":1}", "{}"} {
		if _, err := record(Request{Method: "POST", Path: "/api/alchimie/explore", Body: raw}); err != nil {
			return nil, err
		}
	}
	return c, nil
}
