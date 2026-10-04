package contentbuild

import (
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/content"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

// RateQuick derives the reviewed V92 quick-board scores and identity from the
// source graph. Authored identity, references and catalog review gates are
// checked by ValidateQuickCatalog before any artifact is accepted.
func RateQuick(raw map[string]any, g *graph.Service) (map[string]any, error) {
	return rateQuick(raw, g)
}

// AssignQuickRanks applies historical stable competition ranks in place.
func AssignQuickRanks(rows []any) { assignRanks(rows) }

// ValidateQuickCatalog checks full native rating, source/hash provenance,
// independent factual/quality reviews, visible-board uniqueness and family caps.
func ValidateQuickCatalog(raw, derived map[string]any, g *graph.Service, digests map[string]any) error {
	return validateQuick(raw, derived, g, digests)
}

// ValidateDiscoveryWorld certifies the world and historical saved mechanics,
// returning the private normalized world object with native recipe fingerprint.
func ValidateDiscoveryWorld(raw map[string]any, g *graph.Service) (map[string]any, error) {
	return validateWorld(raw, g)
}

// NodeSnapshot and EdgeSnapshot retain every normalized graph field, including
// provenance, for source-bound offline review artifacts.
func NodeSnapshot(n *content.Node) map[string]any {
	if n == nil {
		return nil
	}
	return nodeMap(*n)
}
func EdgeSnapshot(e *content.Edge) map[string]any {
	if e == nil {
		return nil
	}
	return edgeMap(*e)
}

// Caption derives the reviewed orientation-independent phrase for an actual
// allowed source edge, using exact snapshot binding or neutral relation fallback.
func Caption(g *graph.Service, a, b string) string {
	e := g.Link(a, b)
	if e == nil {
		return ""
	}
	r, err := frozenRules()
	if err != nil {
		panic(err)
	}
	fallback := str(object(r["caption_fallbacks"])[e.Relation])
	if fallback == "" {
		fallback = "legătură directă"
	}
	if a > b {
		a, b = b, a
	}
	entry := array(object(r["reviewed_captions"])[a+"\x00"+b])
	if len(entry) == 2 && valueDigest(edgeMap(*e)) == str(entry[0]) {
		return str(entry[1])
	}
	return fallback
}

// ValidReference checks an offline provenance citation under the shared URL
// contract, including Python-compatible explicit port range validation.
func ValidReference(value string) bool { return validReference(value) }
