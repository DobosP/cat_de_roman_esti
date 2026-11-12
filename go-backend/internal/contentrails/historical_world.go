// Explicit immutable Source5/Source4 World reconstruction only. No CLI route,
// install authority, current validator fallback, global state or mutable profile.
package contentrails

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentbuild"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/graph"
)

type HistoricalWorldProfile uint8

const (
	HistoricalSource5World HistoricalWorldProfile = iota + 1
	HistoricalSource4WorldOnSource5KG
)

// HistoricalWorldContext is a read-only capability for one exact immutable
// reconstruction fixture closure. Its unexported fields cannot be author-set.
// It has no install, export, Check or native audit/qualification method.
type HistoricalWorldContext struct {
	root    string
	profile HistoricalWorldProfile
	files   map[string][]byte // private pinned snapshot; never exposed or modified
}

type historicalWorldMember struct {
	bytes int64
	sha   string
}

// Twelve base members are pinned by genuine immutable manifest SHA256
// 47d93bbae6a5a6f5eec031a09568c20e2f81887598cff9fff9120c9eeff2a48c,
// archive ffffa21ccf11f79d817c529123f2583824c62fefaabd17a5887e7ce809507e48,
// baseline 6a2332795dc5fa2db3eb61e196ab7ab820e76caa. The other fifteen
// members are its exact original source5, World archive closure and test mirrors.
// No caller-supplied manifest, SHA, rubric or arbitrary old source is accepted.
func source5HistoricalWorldMembers() map[string]historicalWorldMember {
	return map[string]historicalWorldMember{
		"cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json":                                 {887711, "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086"},
		"cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json":                               {480000, "1dd346c1786ea39d241f534e6a411c1297160771d3fbfa7f89a47fd22f586fb7"},
		"cat_de_roman_esti/fixtures/board_rankings_v37.json":                                           {164784, "58fa3d6b02b983cdfed05c9383057acfaccbd200612d3eb97e8279318b1f55ef"},
		"cat_de_roman_esti/fixtures/derived_catalog_v38.json":                                          {249190, "25059439b5c46a04263c229a8a3b9b4fc285240af60e15b7f1fdffa1a98f0c01"},
		"cat_de_roman_esti/fixtures/games_pack.json":                                                   {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
		"cat_de_roman_esti/fixtures/kg_sample.json":                                                    {3674915, "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6"},
		"cat_de_roman_esti/fixtures/quick_games_v92.json":                                              {381504, "a21b3c6e50be6947ea8b9ac181f337566db9e4809dd5165a203338fff20d8609"},
		"cat_de_roman_esti/fixtures/release_reserve_v1.json":                                           {5156, "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"},
		"docs/CRITIQUE_RUBRIC.md":                                                                      {17595, "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"},
		"docs/reviews/v1-4-time-links-and-predicates/native/world/candidate.json":                      {808897, "4ad8ff7ec767ca21ea57888e323355a2f08fc039e436518eb314ab2ed76c04dc"},
		"docs/reviews/v1-4-time-links-and-predicates/native/world/factual-review.json":                 {1706838, "48a6cfcd0ad80a82f248b3cc532b724dba88da8059fdab763c5a5a61f4ac63a1"},
		"docs/reviews/v1-4-time-links-and-predicates/native/world/proposal.json":                       {819093, "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"},
		"docs/reviews/v1-4-time-links-and-predicates/native/world/quality-review.json":                 {363761, "32f65cc95cd9d169bba1019d85ab545eaa70be6e17decca0d1fce0d80f3a2240"},
		"docs/reviews/v1-5-hot-chocolate/native/world/candidate.json":                                  {877515, "2a30f2acbaa217a8c6c5dbcaab16acab7513491fbd094066bb49325b0d3e3e04"},
		"docs/reviews/v1-5-hot-chocolate/native/world/factual-review.json":                             {1630305, "f8e3f12d8ae85f20f060fc50b8e70d920b747ea3c07926345f517c7bd0e96945"},
		"docs/reviews/v1-5-hot-chocolate/native/world/proposal.json":                                   {887711, "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086"},
		"docs/reviews/v1-5-hot-chocolate/native/world/quality-review.json":                             {413785, "f19205e9ef18803e3e7c81f1245cf858b16ef5df553e704532d470d271883e69"},
		"docs/reviews/v96-words-and-input-clarity/integration/alchimie/candidate.json":                 {738858, "6de6b98871c43e539402fff9680474cc31afe22f5b4923c13dbafa9bd5465496"},
		"docs/reviews/v97-discovery-continuity-and-new-words/integration/alchimie/candidate.json":      {808760, "e6d4dc8b071e7f4977c81abdcd007120b8bffd5ac9d4803f62f35b8d3a2339d4"},
		"docs/reviews/v97-discovery-continuity-and-new-words/integration/alchimie/factual-review.json": {311146, "501e4ea97ce564e9fb1e764978d7c8a628c7f5774cc2531b7ee117555f5e6e1f"},
		"docs/reviews/v97-discovery-continuity-and-new-words/integration/alchimie/quality-review.json": {346270, "37ed31a2bda9e9a32494736a81f2c51d901e44195852a28b9da26976ba7d38c1"},
		"go-backend/internal/content/bundled.json":                                                     {7272295, "c1fff429992c69926aafb07f5b015f890a82c7c01cc5230107bdaf481bca5993"},
		"go-backend/internal/content/digest.go":                                                        {170, "35f33cfeb67f234ceeee6e2a6ec08dabc036a383e46bbd48bf6d8b4287061ea2"},
		"go-backend/internal/contentrails/sources/authored-v5.json":                                    {2411909, "22b7853e3f93c8a0093066d17f36194bef94e5b1156cf83381671ef23b3cb585"},
		"tests/fixtures/games_pack.json":                                                               {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
		"tests/fixtures/kg_sample.json":                                                                {3674915, "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6"},
		"tests/fixtures/release_reserve_v1.json":                                                       {5156, "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"},
	}
}

func OpenHistoricalWorldContext(root string, profile HistoricalWorldProfile) (*HistoricalWorldContext, error) {
	absolute, err := filepath.Abs(root)
	if err != nil || absolute != root || filepath.Clean(root) != root {
		return nil, fmt.Errorf("historical World requires canonical absolute root")
	}
	physical, err := filepath.EvalSymlinks(root)
	if err != nil || physical != root {
		return nil, fmt.Errorf("historical World root symlink refused")
	}
	c := &HistoricalWorldContext{root: root, profile: profile}
	files, err := c.readRoot()
	if err != nil {
		return nil, err
	}
	c.files = files
	return c, nil
}

func (c *HistoricalWorldContext) verify() error {
	_, err := c.readRoot()
	return err
}

// readRoot is the sole historical filesystem reader. Every captured byte must
// match the immutable profile; later reconstruction reads only the private copy.
func (c *HistoricalWorldContext) readRoot() (map[string][]byte, error) {
	if c == nil || c.root == "" || (c.profile != HistoricalSource5World && c.profile != HistoricalSource4WorldOnSource5KG) {
		return nil, fmt.Errorf("unknown historical World profile")
	}
	seen := map[string]bool{}
	files := map[string][]byte{}
	var total int64
	err := filepath.WalkDir(c.root, func(path string, entry fs.DirEntry, err error) error {
		if err != nil {
			return err
		}
		if entry.Type()&fs.ModeSymlink != 0 || !entry.IsDir() && !entry.Type().IsRegular() {
			return fmt.Errorf("historical World special/symlink member refused")
		}
		if entry.IsDir() {
			return nil
		}
		relative, err := filepath.Rel(c.root, path)
		if err != nil {
			return err
		}
		relative = filepath.ToSlash(relative)
		want, known := source5HistoricalWorldMembers()[relative]
		if !known || seen[relative] {
			return fmt.Errorf("unknown historical World root member: %s", relative)
		}
		if c.profile == HistoricalSource4WorldOnSource5KG && relative == "cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json" {
			want = historicalWorldMember{819093, "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"}
		}
		b, err := contentbuild.ReadPendingInput(path, 16<<20)
		if err != nil || int64(len(b)) != want.bytes || digestBytes(b) != want.sha {
			if relative == "cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json" {
				return fmt.Errorf("installed world differs from immutable historical profile")
			}
			return fmt.Errorf("historical World member differs from immutable profile: %s", relative)
		}
		total += int64(len(b))
		if total > 32<<20 {
			return fmt.Errorf("historical immutable closure aggregate byte cap")
		}
		files[relative] = append([]byte(nil), b...)
		seen[relative] = true
		return nil
	})
	if err != nil {
		return nil, err
	}
	if len(seen) != len(source5HistoricalWorldMembers()) {
		return nil, fmt.Errorf("historical World immutable closure incomplete")
	}
	return files, nil
}

func (c *HistoricalWorldContext) snapshotBytes(relative string, max int64) ([]byte, error) {
	if c == nil || len(c.files) != 27 || (c.profile != HistoricalSource5World && c.profile != HistoricalSource4WorldOnSource5KG) {
		return nil, fmt.Errorf("historical frozen context missing")
	}
	want, known := source5HistoricalWorldMembers()[relative]
	if c.profile == HistoricalSource4WorldOnSource5KG && relative == "cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json" {
		want = historicalWorldMember{819093, "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"}
	}
	b, exists := c.files[relative]
	if !known || !exists || int64(len(b)) != want.bytes || int64(len(b)) > max || digestBytes(b) != want.sha {
		return nil, fmt.Errorf("historical frozen member bytes/hash/cap differs: %s", relative)
	}
	return append([]byte(nil), b...), nil
}

func (c *HistoricalWorldContext) absoluteBytes(path string, max int64) ([]byte, error) {
	if c == nil || !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return nil, fmt.Errorf("historical frozen absolute path refused")
	}
	relative, err := filepath.Rel(c.root, path)
	if err != nil || strings.HasPrefix(relative, "..") {
		return nil, fmt.Errorf("historical frozen path outside context")
	}
	return c.snapshotBytes(filepath.ToSlash(relative), max)
}

func (c *HistoricalWorldContext) selectedSource(s *Source) (*Source, error) {
	if s == nil {
		return nil, fmt.Errorf("historical World source missing")
	}
	var raw []byte
	switch {
	case s.Version == 1 && s.SHA256 == AuthoredSHA256:
		raw = append([]byte(nil), authoredSource...)
	case s.Version == 5 && s.SHA256 == "22b7853e3f93c8a0093066d17f36194bef94e5b1156cf83381671ef23b3cb585":
		var err error
		raw, err = c.snapshotBytes("go-backend/internal/contentrails/sources/authored-v5.json", MaxBytes)
		if err != nil {
			return nil, err
		}
	default:
		return nil, fmt.Errorf("historical World accepts only exact original authored source1/source5")
	}
	approved, err := decodeSource(raw, "", -1)
	if err != nil || digestBytes(raw) != s.SHA256 || approved.Version != s.Version || !same(approved.Raw, s.Raw) {
		return nil, fmt.Errorf("historical World authored source bytes/semantics differ")
	}
	// Return a new decoded approved source, never the caller-owned mutable map.
	return approved, nil
}

func (c *HistoricalWorldContext) source(s *Source) error {
	if err := c.verify(); err != nil {
		return err
	}
	_, err := c.selectedSource(s)
	return err
}

func (c *HistoricalWorldContext) bindings(root string) (map[string]any, error) {
	if c == nil || c.root != root {
		return nil, fmt.Errorf("historical World context/root mismatch")
	}
	out := map[string]any{}
	for _, name := range contentbuild.SourceNames {
		b, err := c.snapshotBytes("cat_de_roman_esti/fixtures/"+name, 16<<20)
		if err != nil {
			return nil, err
		}
		out[name] = contentbuild.TextSHA256(b)
	}
	b, err := c.snapshotBytes("docs/CRITIQUE_RUBRIC.md", MaxBytes)
	if err != nil {
		return nil, err
	}
	out["rubric"] = contentbuild.TextSHA256(b)
	return out, nil
}

// These helpers have no implicit historical Root detection: nil retains the
// exact current reader/validator. A non-nil context never reopens working bytes.
func worldReadBytes(path string, historical *HistoricalWorldContext) ([]byte, error) {
	if historical == nil {
		return os.ReadFile(path)
	}
	return historical.absoluteBytes(path, MaxBytes)
}

func worldReadObject(path string, historical *HistoricalWorldContext) (map[string]any, error) {
	if historical == nil {
		return Read(path)
	}
	b, err := historical.absoluteBytes(path, MaxBytes)
	if err != nil {
		return nil, err
	}
	return contentbuild.DecodeObject(b)
}

func worldSourceGraph(root string, historical *HistoricalWorldContext) (*graph.Service, error) {
	if historical == nil {
		return sourceGraph(root)
	}
	if historical.root != root {
		return nil, fmt.Errorf("historical graph context/root mismatch")
	}
	b, err := historical.snapshotBytes("cat_de_roman_esti/fixtures/kg_sample.json", 16<<20)
	if err != nil {
		return nil, err
	}
	raw, err := contentbuild.DecodeObject(b)
	if err != nil {
		return nil, err
	}
	return contentbuild.QuickGraphSnapshot(raw)
}

func worldArchive(root string, s *Source, name string, historical *HistoricalWorldContext) (map[string]any, error) {
	if historical == nil {
		return archive(root, s, name)
	}
	if historical.root != root {
		return nil, fmt.Errorf("historical archive context/root mismatch")
	}
	d := object(object(s.Raw["archives"])[name])
	if !authorityDescriptor(d) {
		return nil, fmt.Errorf("historical archive descriptor refused")
	}
	b, err := historical.snapshotBytes(text(d["path"]), MaxBytes)
	if err != nil || digestBytes(b) != d["sha256"] {
		return nil, fmt.Errorf("historical archive frozen digest differs")
	}
	return contentbuild.DecodeObject(b)
}

func worldFixture(root, name string, historical *HistoricalWorldContext) (map[string]any, error) {
	if historical == nil {
		return fixture(root, name)
	}
	if historical.root != root {
		return nil, fmt.Errorf("historical fixture context/root mismatch")
	}
	b, err := historical.snapshotBytes("cat_de_roman_esti/fixtures/"+name, MaxBytes)
	if err != nil {
		return nil, err
	}
	return contentbuild.DecodeObject(b)
}

func worldScopedBindings(root string, historical *HistoricalWorldContext) (map[string]any, error) {
	if historical == nil {
		return bindings(root)
	}
	return historical.bindings(root)
}

func (c *HistoricalWorldContext) Candidate(s *Source) (map[string]any, error) {
	if err := c.source(s); err != nil {
		return nil, err
	}
	selected, err := c.selectedSource(s)
	if err != nil {
		return nil, err
	}
	out, err := worldCandidateForContext(c.root, selected, false, false, c)
	if err != nil {
		return nil, err
	}
	if err := c.source(s); err != nil {
		return nil, err
	}
	return out, nil
}

// ReconstructProposal returns private data only. It grants no installation or
// current-rail authority. The original staging predecessor check stays active;
// installed=true selects only the original installed reconstruction contract.
func (c *HistoricalWorldContext) ReconstructProposal(s *Source, candidate, factual, quality string, installed bool) (map[string]any, error) {
	if err := c.source(s); err != nil {
		return nil, err
	}
	// Only original pinned candidate/F/Q members of this same genuine root
	// may enter reconstruction. A sibling or caller-authored file is refused.
	for _, path := range []string{candidate, factual, quality} {
		matched := false
		for relative, want := range source5HistoricalWorldMembers() {
			if !strings.HasPrefix(relative, "docs/reviews/") || (!strings.HasSuffix(relative, "/candidate.json") && !strings.HasSuffix(relative, "/factual-review.json") && !strings.HasSuffix(relative, "/quality-review.json")) {
				continue
			}
			if filepath.ToSlash(path) == filepath.ToSlash(filepath.Join(c.root, relative)) {
				b, err := c.absoluteBytes(path, MaxBytes)
				matched = err == nil && int64(len(b)) == want.bytes && digestBytes(b) == want.sha
				break
			}
		}
		if !matched {
			return nil, fmt.Errorf("historical World proposal inputs must be original pinned context members")
		}
	}
	selected, err := c.selectedSource(s)
	if err != nil {
		return nil, err
	}
	out, err := buildProposalForContext(c.root, selected, "world", candidate, factual, quality, installed, c)
	if err != nil {
		return nil, err
	}
	if err := c.source(s); err != nil {
		return nil, err
	}
	return out, nil
}
