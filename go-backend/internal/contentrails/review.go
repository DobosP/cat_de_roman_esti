package contentrails

import (
	"fmt"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"os"
	"path/filepath"
	"strings"
)

type Review struct {
	Role            string
	Reviewer        string
	SHA256          string
	CandidateSHA256 string
	Raw             map[string]any
}

func validSources(sources []any) bool {
	if len(sources) > 32 {
		return false
	}
	for _, v := range sources {
		value, ok := v.(string)
		if !ok || !contentbuild.ValidReference(value) {
			return false
		}
	}
	return true
}
func reviewKind(rail string) string {
	switch rail {
	case "quick":
		return "quick-content-review-v1"
	case "world":
		return "alchimie-discovery-world-review-v1"
	case "extensions":
		return "alchimie-recipe-extension-review-v1"
	}
	return ""
}
func readReviews(root, rail, candidateSHA string, candidate map[string]any, paths []string) ([]Review, error) {
	if len(paths) != 2 {
		return nil, fmt.Errorf("two semantic reviews required")
	}
	field := "boards"
	if rail == "world" {
		field = "recipes"
	}
	if rail == "extensions" {
		field = "candidates"
	}
	wanted := map[string]bool{}
	for _, v := range rows(candidate[field]) {
		id := text(object(v)["id"])
		if id == "" || wanted[id] {
			return nil, fmt.Errorf("invalid or duplicate authored candidate")
		}
		wanted[id] = true
	}
	if len(wanted) == 0 || len(wanted) > 512 {
		return nil, fmt.Errorf("candidate count bound")
	}
	reviews := []Review{}
	roles := []string{"factual", "quality"}
	for i, path := range paths {
		raw, err := Read(path)
		if err != nil {
			return nil, err
		}
		blob, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		role := roles[i]
		reviewer := text(raw["reviewer"])
		if !allowedKeys(raw, "kind", "role", "reviewer", "candidate_sha256", "items", "concepts", "world_verdict", "world_rationale", "baseline_evidence", "evidence_sha256", "inherited_review_sha256") || raw["kind"] != reviewKind(rail) || raw["role"] != role || raw["candidate_sha256"] != candidateSHA || strings.TrimSpace(reviewer) == "" || reviewer != strings.TrimSpace(reviewer) {
			return nil, fmt.Errorf("semantic role/identity/candidate binding differs")
		}
		judged := map[string]bool{}
		for _, v := range rows(raw["items"]) {
			row := object(v)
			id := text(row["id"])
			verdict := text(row["verdict"])
			if !allowedKeys(row, "id", "verdict", "rationale", "sources", "inherited", "evidence_basis") || !wanted[id] || judged[id] || !strings.Contains("|accept|reject|hold|", "|"+verdict+"|") || strings.TrimSpace(text(row["rationale"])) == "" || !sourcesValue(row["sources"]) {
				return nil, fmt.Errorf("semantic judgment incomplete/invalid/duplicate")
			}
			if role == "factual" && verdict == "accept" && len(rows(row["sources"])) == 0 {
				return nil, fmt.Errorf("accepted facts require source references")
			}
			judged[id] = true
		}
		if len(judged) != len(wanted) {
			return nil, fmt.Errorf("incomplete exact semantic coverage")
		}
		reviews = append(reviews, Review{role, reviewer, digestBytes(blob), candidateSHA, raw})
	}
	g, err := sourceGraph(root)
	if err != nil {
		return nil, err
	}
	if g.Casefold(reviews[0].Reviewer) == g.Casefold(reviews[1].Reviewer) {
		return nil, fmt.Errorf("semantic reviewers must be independent")
	}
	return reviews, nil
}
func digestBytes(b []byte) string { return contentbuild.SHA256(b) }
func acceptedIDs(reviews []Review) map[string]bool {
	accepted := map[string]bool{}
	if len(reviews) != 2 {
		return accepted
	}
	for _, v := range rows(reviews[0].Raw["items"]) {
		r := object(v)
		if r["verdict"] == "accept" {
			accepted[text(r["id"])] = true
		}
	}
	for _, v := range rows(reviews[1].Raw["items"]) {
		r := object(v)
		if r["verdict"] != "accept" {
			delete(accepted, text(r["id"]))
		}
	}
	return accepted
}
func reviewDescriptors(reviews []Review, withCandidate bool) []any {
	out := []any{}
	for _, r := range reviews {
		m := map[string]any{"role": r.Role, "reviewer": r.Reviewer, "sha256": r.SHA256}
		if withCandidate {
			m["candidate_sha256"] = r.CandidateSHA256
		}
		out = append(out, m)
	}
	return out
}
func baselineReviewPaths(root string, s *Source, rail string) ([]string, error) {
	names := []string{rail + "_factual", rail + "_quality"}
	paths := []string{}
	for _, name := range names {
		if _, err := archive(root, s, name); err != nil {
			return nil, err
		}
		paths = append(paths, filepath.Join(root, text(object(object(s.Raw["archives"])[name])["path"])))
	}
	return paths, nil
}

func allowedKeys(raw map[string]any, allowed ...string) bool {
	seen := map[string]bool{}
	for _, k := range allowed {
		seen[k] = true
	}
	for k := range raw {
		if !seen[k] {
			return false
		}
	}
	return true
}
func sourcesValue(v any) bool { sources, ok := v.([]any); return ok && validSources(sources) }
