// Package content loads the private, build-time export of reviewed Python content.
// The export is embedded in the server; it must never be served as a public asset.
package content

import (
	"bytes"
	"crypto/sha256"
	_ "embed"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"sync"
)

//go:embed bundled.json
var bundled []byte

type Board struct {
	Game         string         `json:"game"`
	CatalogID    string         `json:"catalog_id"`
	SourceID     string         `json:"source_id"`
	Category     string         `json:"category"`
	Difficulty   string         `json:"difficulty"`
	OverallScore int            `json:"overall_score"`
	StarterScore int            `json:"starter_score"`
	OverallRank  int            `json:"overall_rank"`
	StarterRank  *int           `json:"starter_rank"`
	StarterSafe  bool           `json:"starter_safe"`
	Payload      map[string]any `json:"payload"`
}

type Content struct {
	SchemaVersion          int               `json:"schema_version"`
	AppVersion             string            `json:"app_version"`
	Sources                map[string]string `json:"sources"`
	Labels                 map[string]string `json:"labels"`
	CategoryLabels         map[string]string `json:"category_labels"`
	Boards                 []Board           `json:"boards"`
	Manifest               map[string]any    `json:"manifest"`
	CategoryOrder          []string          `json:"category_order"`
	LetterRanges           [][2]uint32       `json:"letter_ranges"`
	LabelPatterns          map[string]string `json:"label_patterns"`
	Nodes                  []Node            `json:"nodes"`
	Edges                  []Edge            `json:"edges"`
	PackItems              []PackItem        `json:"pack_items"`
	PackRanked             bool              `json:"pack_ranked"`
	NormalizationMap       map[string]string `json:"normalization_map"`
	AccentNormalizationMap map[string]string `json:"accent_normalization_map"`
	CasefoldMap map[string]string `json:"casefold_map"`
	NormalizedIndex        map[string]string `json:"normalized_index"`
	ContextoData           map[string]any    `json:"contexto_data"`
	LantCaptions           map[string]string `json:"lant_captions"`
	DiscoveryWorld         map[string]any    `json:"discovery_world"`
	RecipeExtensions       map[string]any    `json:"recipe_extensions"`
	AlchimieProjections    map[string]any    `json:"alchimie_projections"`
	Metadata               map[string]any    `json:"metadata"`
	shared                 sync.Map
}

// Shared memoizes immutable startup services without retaining other Content instances.
func (c *Content) Shared(name string, build func() any) any {
	v, _ := c.shared.LoadOrStore(name, &sharedValue{})
	entry := v.(*sharedValue)
	entry.once.Do(func() { entry.value = build() })
	return entry.value
}

type sharedValue struct {
	once  sync.Once
	value any
}

type Node struct {
	ID              string         `json:"id"`
	NodeType        string         `json:"node_type"`
	LabelRO         string         `json:"label_ro"`
	Category        string         `json:"category"`
	Description     string         `json:"description"`
	Salience        float64        `json:"salience"`
	DifficultyTier  string         `json:"difficulty_tier"`
	Degree          int            `json:"degree"`
	Aliases         []string       `json:"aliases"`
	Tags            []string       `json:"tags"`
	Facets          map[string]any `json:"facets"`
	Source          string         `json:"source"`
	Redistributable bool           `json:"redistributable"`
}
type Edge struct {
	ID              string         `json:"id"`
	Src             string         `json:"src_id"`
	Dst             string         `json:"dst_id"`
	Relation        string         `json:"relation"`
	LabelRO         string         `json:"label_ro"`
	Strength        float64        `json:"strength"`
	IsDistractor    bool           `json:"is_distractor"`
	Bidirectional   bool           `json:"bidirectional"`
	Tags            []string       `json:"tags"`
	Facets          map[string]any `json:"facets"`
	Source          string         `json:"source"`
	Redistributable bool           `json:"redistributable"`
}
type PackItem struct {
	Game            string         `json:"game"`
	ID              string         `json:"id"`
	Category        string         `json:"category"`
	Difficulty      string         `json:"difficulty"`
	Payload         map[string]any `json:"payload"`
	Source          string         `json:"source"`
	Status          string         `json:"status"`
	PilotScore      int            `json:"pilot_score"`
	PilotEligible   bool           `json:"pilot_eligible"`
	SelectionWeight int            `json:"selection_weight"`
}

func Load() (*Content, error) {
	if fmt.Sprintf("%x", sha256.Sum256(bundled)) != bundledSHA256 {
		return nil, fmt.Errorf("private content: embedded export digest drift")
	}
	return Decode(bundled)
}

func Decode(data []byte) (*Content, error) {
	var c Content
	d := json.NewDecoder(bytes.NewReader(data))
	d.DisallowUnknownFields()
	if err := d.Decode(&c); err != nil {
		return nil, fmt.Errorf("private content: %w", err)
	}
	var trailing any
	if d.Decode(&trailing) != io.EOF {
		return nil, fmt.Errorf("private content: trailing JSON")
	}
	if c.SchemaVersion != 2 || c.AppVersion == "" || len(c.Labels) == 0 || len(c.Boards) == 0 {
		return nil, fmt.Errorf("private content: incomplete schema")
	}
	contentHash, ok := c.Manifest["content_hash"].(string)
	if !ok || len(contentHash) != 71 || contentHash[:7] != "sha256:" {
		return nil, fmt.Errorf("private content: invalid manifest hash")
	}
	if digest, err := hex.DecodeString(contentHash[7:]); err != nil || len(digest) != 32 {
		return nil, fmt.Errorf("private content: invalid manifest hash")
	}
	build, ok := c.Manifest["build_version"].(string)
	counts, okCounts := c.Manifest["counts"].(map[string]any)
	if !ok || build == "" || !okCounts || counts["nodes"] != float64(len(c.Labels)) || c.Manifest["app"] != "cat_de_roman_esti" || c.Manifest["manifest_version"] != float64(1) || c.Manifest["schema_version"] != float64(1) {
		return nil, fmt.Errorf("private content: invalid manifest identity")
	}
	for _, name := range []string{"kg_sample.json", "derived_catalog_v38.json", "quick_games_v92.json", "board_rankings_v37.json", "release_reserve_v1.json", "games_pack.json"} {
		digest, err := hex.DecodeString(c.Sources[name])
		if err != nil || len(digest) != 32 {
			return nil, fmt.Errorf("private content: missing source identity %s", name)
		}
	}
	seen := make(map[string]bool)
	for _, b := range c.Boards {
		if (b.Game != "intrusul" && b.Game != "perechi") || b.CatalogID == "" || seen[b.CatalogID] || b.SourceID == "" || c.CategoryLabels[b.Category] == "" || b.OverallScore < 0 || b.OverallScore > 100 || b.StarterScore < 0 || b.StarterScore > 100 {
			return nil, fmt.Errorf("private content: invalid board identity/rank")
		}
		seen[b.CatalogID] = true
		if b.Game == "perechi" {
			pairs, ok := b.Payload["pairs"].([]any)
			if !ok || len(pairs) != 4 {
				return nil, fmt.Errorf("private content: invalid Perechi pairs")
			}
			ids := map[string]bool{}
			for _, p := range pairs {
				pair, ok := p.(map[string]any)
				if !ok {
					return nil, fmt.Errorf("private content: invalid Perechi pair")
				}
				members, ok := pair["members"].([]any)
				if !ok || len(members) != 2 {
					return nil, fmt.Errorf("private content: invalid Perechi members")
				}
				for _, v := range members {
					id, ok := v.(string)
					if !ok || ids[id] || c.Labels[id] == "" {
						return nil, fmt.Errorf("private content: invalid Perechi ID")
					}
					ids[id] = true
				}
			}
			continue
		}
		members, ok := b.Payload["members"].([]any)
		intruder, okID := b.Payload["intruder"].(string)
		label, okLabel := b.Payload["group_label"].(string)
		if !ok || len(members) != 3 || !okID || c.Labels[intruder] == "" || !okLabel || label == "" {
			return nil, fmt.Errorf("private content: invalid Intrusul payload")
		}
		ids := map[string]bool{intruder: true}
		for _, value := range members {
			id, ok := value.(string)
			if !ok || c.Labels[id] == "" || ids[id] {
				return nil, fmt.Errorf("private content: invalid Intrusul members")
			}
			ids[id] = true
		}
	}
	return &c, nil
}
