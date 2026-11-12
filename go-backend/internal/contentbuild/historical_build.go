package contentbuild

import (
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"strings"
)

// This path only replays four genuine immutable historical fixtures. It has no
// exported API, CLI route, install authority, root auto-detection or old-SHA input.
// Current Build/Load/Export/ValidateSources and operator validators pass nil.
// Capture uses the existing Linux no-symlink reader; other targets compile but
// historical replay there fails closed, without changing current portability.
type historicalBuildProfile uint8

const (
	historicalBuildSource4 historicalBuildProfile = iota + 1
	historicalBuildSource5
	historicalBuildOriginalSource6
	historicalBuildReviewedSource6
)

const historicalBuildRubricSHA256 = "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"

type historicalBuildMember struct {
	bytes int64
	sha   string
}

type historicalBuildContext struct {
	root    string
	profile historicalBuildProfile
	files   map[string][]byte // captured private bytes; every read returns a clone
}

// The Source5 literals are the existing 6a233279 context manifest 47d93bba…,
// archive ffffa21c…. Source4 substitutes only the genuine archived World from
// that same manifest and retains its original d1d3… bundle assertion. Source6
// literals are manifests 85060d2d… (59a9a568) and fd36c144… (4f36abf3).
// Existing archive helpers authenticate those complete manifests independently.
func historicalBuildMembers(profile historicalBuildProfile) (map[string]historicalBuildMember, error) {
	switch profile {
	case historicalBuildSource4:
		return map[string]historicalBuildMember{
			"cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json":           {819093, "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"},
			"cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json":         {480000, "1dd346c1786ea39d241f534e6a411c1297160771d3fbfa7f89a47fd22f586fb7"},
			"cat_de_roman_esti/fixtures/board_rankings_v37.json":                     {164784, "58fa3d6b02b983cdfed05c9383057acfaccbd200612d3eb97e8279318b1f55ef"},
			"cat_de_roman_esti/fixtures/derived_catalog_v38.json":                    {249190, "25059439b5c46a04263c229a8a3b9b4fc285240af60e15b7f1fdffa1a98f0c01"},
			"cat_de_roman_esti/fixtures/games_pack.json":                             {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"cat_de_roman_esti/fixtures/kg_sample.json":                              {3674915, "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6"},
			"cat_de_roman_esti/fixtures/quick_games_v92.json":                        {381504, "a21b3c6e50be6947ea8b9ac181f337566db9e4809dd5165a203338fff20d8609"},
			"cat_de_roman_esti/fixtures/release_reserve_v1.json":                     {5156, "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"},
			"docs/CRITIQUE_RUBRIC.md":                                                {17595, "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"},
			"docs/reviews/v1-4-time-links-and-predicates/native/world/proposal.json": {819093, "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"},
			"tests/fixtures/games_pack.json":                                         {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"tests/fixtures/kg_sample.json":                                          {3674915, "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6"},
		}, nil
	case historicalBuildSource5:
		return map[string]historicalBuildMember{
			"cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json":           {887711, "196e0b72310e6ec7b9b18254b4b95a307d9ae7a9ecb97f3670b66f24ff071086"},
			"cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json":         {480000, "1dd346c1786ea39d241f534e6a411c1297160771d3fbfa7f89a47fd22f586fb7"},
			"cat_de_roman_esti/fixtures/board_rankings_v37.json":                     {164784, "58fa3d6b02b983cdfed05c9383057acfaccbd200612d3eb97e8279318b1f55ef"},
			"cat_de_roman_esti/fixtures/derived_catalog_v38.json":                    {249190, "25059439b5c46a04263c229a8a3b9b4fc285240af60e15b7f1fdffa1a98f0c01"},
			"cat_de_roman_esti/fixtures/games_pack.json":                             {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"cat_de_roman_esti/fixtures/kg_sample.json":                              {3674915, "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6"},
			"cat_de_roman_esti/fixtures/quick_games_v92.json":                        {381504, "a21b3c6e50be6947ea8b9ac181f337566db9e4809dd5165a203338fff20d8609"},
			"cat_de_roman_esti/fixtures/release_reserve_v1.json":                     {5156, "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"},
			"docs/CRITIQUE_RUBRIC.md":                                                {17595, "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"},
			"docs/reviews/v1-4-time-links-and-predicates/native/world/proposal.json": {819093, "0d10180a3ad7cd88ba642cd1326fcbf78a2e398af8643a75f9e1b1d789909cef"},
			"go-backend/internal/content/bundled.json":                               {7272295, "c1fff429992c69926aafb07f5b015f890a82c7c01cc5230107bdaf481bca5993"},
			"go-backend/internal/content/digest.go":                                  {170, "35f33cfeb67f234ceeee6e2a6ec08dabc036a383e46bbd48bf6d8b4287061ea2"},
			"tests/fixtures/games_pack.json":                                         {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"tests/fixtures/kg_sample.json":                                          {3674915, "0cd40cc968d61ed197a0d41b8f5ccf54ad9216c967d044fbd74243fcb5c1e2d6"},
		}, nil
	case historicalBuildOriginalSource6:
		return map[string]historicalBuildMember{
			"cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json":   {887746, "8f013a8f6b54a97a768a34c42e669addc4f5ab9823302befbe15ad811cae77ad"},
			"cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json": {480012, "d94647e78f8c2bd375b961f0aab52f3f7207024e60bed745b78c4a3d052d0bfc"},
			"cat_de_roman_esti/fixtures/board_rankings_v37.json":             {164784, "036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31"},
			"cat_de_roman_esti/fixtures/derived_catalog_v38.json":            {249190, "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a"},
			"cat_de_roman_esti/fixtures/games_pack.json":                     {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"cat_de_roman_esti/fixtures/kg_sample.json":                      {3674955, "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf"},
			"cat_de_roman_esti/fixtures/quick_games_v92.json":                {381537, "0c79b9c5cb0f9602c2506ef384ac64d519731dd9add53acf602d2c4f51a3f345"},
			"cat_de_roman_esti/fixtures/release_reserve_v1.json":             {5156, "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"},
			"docs/CRITIQUE_RUBRIC.md":                                        {17595, "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"},
			"go-backend/internal/content/bundled.json":                       {7272424, "e0cfe93de076f14a782dc6377b2655d4ef10f86ada1560ae1202bb06dbfdf877"},
			"go-backend/internal/content/digest.go":                          {170, "c0bededc869ef4c719d55ab22b7c3fbf6fa973eb972b912860d8dddf92c34b4d"},
			"tests/fixtures/games_pack.json":                                 {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"tests/fixtures/kg_sample.json":                                  {3674955, "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf"},
		}, nil
	case historicalBuildReviewedSource6:
		return map[string]historicalBuildMember{
			"cat_de_roman_esti/fixtures/alchimie_discovery_world_v92.json":   {887736, "572882a77dbdd8bac63ca69c64c6990a1601a49551693cf1b1b5fcb7a81861de"},
			"cat_de_roman_esti/fixtures/alchimie_recipe_extensions_v92.json": {480002, "eeb7eede9009f09a7d9df012c7addb9f26b1b484040eb31c44ba2e6f7f35cee8"},
			"cat_de_roman_esti/fixtures/board_rankings_v37.json":             {164784, "036c8a00de347939d132ba25512da7cba53b12e9d11a9f86cecc07cc98293c31"},
			"cat_de_roman_esti/fixtures/derived_catalog_v38.json":            {249190, "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a"},
			"cat_de_roman_esti/fixtures/games_pack.json":                     {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"cat_de_roman_esti/fixtures/kg_sample.json":                      {3674955, "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf"},
			"cat_de_roman_esti/fixtures/quick_games_v92.json":                {381527, "234305a844033cff0914a5213f6c0b8dcd1b21918d57cc851780259c9e87ee59"},
			"cat_de_roman_esti/fixtures/release_reserve_v1.json":             {5156, "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7"},
			"docs/CRITIQUE_RUBRIC.md":                                        {17595, "3fc2d6db8f8607d0bb70a9f7b4f329a42102b57ed2134e0f6e02ae5fb6e8e101"},
			"go-backend/internal/content/bundled.json":                       {7272404, "a220c22ec948e0738fa34d614fa033d715aee10a9ebf18369691f1dbe1166a4a"},
			"go-backend/internal/content/digest.go":                          {170, "41295fbf205e586a4abb271cf77f0bb38ea35bd4109e965ffdbe8152fc602286"},
			"tests/fixtures/games_pack.json":                                 {410839, "e24eb3622c81f3bb0425f975bf74ec3b5a50f9cb719544794704541dc65ff5d8"},
			"tests/fixtures/kg_sample.json":                                  {3674955, "63f0dcd7992f0d1434eab49b9c1b7e97f0db30a22cd708b7b25c0199f39031bf"},
		}, nil
	default:
		return nil, fmt.Errorf("unknown historical build profile")
	}
}

func openHistoricalBuildContext(root string, profile historicalBuildProfile) (*historicalBuildContext, error) {
	c := &historicalBuildContext{root: root, profile: profile}
	files, err := c.readRoot()
	if err != nil {
		return nil, err
	}
	c.files = files
	return c, nil
}

func (c *historicalBuildContext) readRoot() (map[string][]byte, error) {
	if c == nil || !filepath.IsAbs(c.root) || filepath.Clean(c.root) != c.root {
		return nil, fmt.Errorf("historical build requires canonical absolute root")
	}
	physical, err := filepath.EvalSymlinks(c.root)
	if err != nil || physical != c.root {
		return nil, fmt.Errorf("historical build root symlink refused")
	}
	members, err := historicalBuildMembers(c.profile)
	if err != nil {
		return nil, err
	}
	directories := map[string]bool{".": true}
	for name := range members {
		for parent := filepath.Dir(filepath.FromSlash(name)); parent != "."; parent = filepath.Dir(parent) {
			directories[filepath.ToSlash(parent)] = true
		}
	}
	files := map[string][]byte{}
	var total int64
	err = filepath.WalkDir(c.root, func(path string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		relative, err := filepath.Rel(c.root, path)
		if err != nil {
			return err
		}
		relative = filepath.ToSlash(relative)
		if entry.Type()&fs.ModeSymlink != 0 || !entry.IsDir() && !entry.Type().IsRegular() {
			return fmt.Errorf("historical build special/symlink member refused: %s", relative)
		}
		if entry.IsDir() {
			if !directories[relative] {
				return fmt.Errorf("unknown historical build directory: %s", relative)
			}
			return nil
		}
		want, known := members[relative]
		if !known || files[relative] != nil {
			return fmt.Errorf("unknown historical build member: %s", relative)
		}
		b, err := ReadPendingInput(path, 16<<20)
		if err != nil {
			return err
		}
		if int64(len(b)) != want.bytes || SHA256(b) != want.sha {
			// Preserve the existing changed-quick regression's precise refusal.
			if relative == "cat_de_roman_esti/fixtures/quick_games_v92.json" {
				return fmt.Errorf("quick_games_v92.json: reviewed artifact digest drift")
			}
			return fmt.Errorf("historical build immutable member drift: %s", relative)
		}
		total += int64(len(b))
		if total > 24<<20 {
			return fmt.Errorf("historical build immutable closure aggregate byte cap")
		}
		files[relative] = append([]byte(nil), b...)
		return nil
	})
	if err != nil {
		return nil, err
	}
	if len(files) != len(members) {
		return nil, fmt.Errorf("historical build immutable closure incomplete")
	}
	return files, nil
}

func (c *historicalBuildContext) verify() error {
	_, err := c.readRoot()
	return err
}

func (c *historicalBuildContext) snapshotBytes(path string, max int64) ([]byte, error) {
	if c == nil || !filepath.IsAbs(path) || filepath.Clean(path) != path {
		return nil, fmt.Errorf("historical build frozen absolute path refused")
	}
	relative, err := filepath.Rel(c.root, path)
	if err != nil || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return nil, fmt.Errorf("historical build frozen path outside context")
	}
	members, err := historicalBuildMembers(c.profile)
	if err != nil || len(c.files) != len(members) {
		return nil, fmt.Errorf("historical build frozen context missing")
	}
	relative = filepath.ToSlash(relative)
	want, known := members[relative]
	b, exists := c.files[relative]
	if !known || !exists || int64(len(b)) != want.bytes || int64(len(b)) > max || SHA256(b) != want.sha {
		return nil, fmt.Errorf("historical build frozen member bytes/hash/cap differs: %s", relative)
	}
	return append([]byte(nil), b...), nil
}

func buildReadBytes(path string, max int64, historical *historicalBuildContext) ([]byte, error) {
	if historical == nil {
		return os.ReadFile(path)
	}
	return historical.snapshotBytes(path, max)
}

func buildReadObject(path string, max int64, historical *historicalBuildContext) (map[string]any, error) {
	if historical == nil {
		return ReadObject(path, max)
	}
	b, err := historical.snapshotBytes(path, max)
	if err != nil {
		return nil, err
	}
	return decodeObject(b)
}

func buildRubricSHA256(historical *historicalBuildContext) string {
	if historical == nil {
		return RubricSHA256
	}
	b, err := historical.snapshotBytes(filepath.Join(historical.root, "docs/CRITIQUE_RUBRIC.md"), 1<<20)
	if err != nil || TextSHA256(b) != historicalBuildRubricSHA256 {
		return "" // malformed internal contexts receive no validation authority
	}
	return historicalBuildRubricSHA256
}

func buildReviewedPin(name string, historical *historicalBuildContext) string {
	if historical == nil {
		return reviewedPins[name]
	}
	switch name {
	case "derived_catalog_v38.json", "quick_games_v92.json", "release_reserve_v1.json":
		members, err := historicalBuildMembers(historical.profile)
		if err != nil {
			return "invalid historical profile"
		}
		return members["cat_de_roman_esti/fixtures/"+name].sha
	default:
		return ""
	}
}

func (c *historicalBuildContext) build() ([]byte, error) {
	if c == nil {
		return nil, fmt.Errorf("historical build context missing")
	}
	// buildWithHistoricalContext performs the precheck. All builder reads after
	// it use private captured bytes, including source re-reads and test mirrors.
	m, err := buildWithHistoricalContext(c.root, true, c)
	if err != nil {
		return nil, err
	}
	b, err := Canonical(m)
	if err != nil {
		return nil, err
	}
	b = append(b, '\n')
	if err := c.verify(); err != nil {
		return nil, err
	}
	return b, nil
}

func buildHistorical(root string, profile historicalBuildProfile) ([]byte, error) {
	c, err := openHistoricalBuildContext(root, profile)
	if err != nil {
		return nil, err
	}
	return c.build()
}
