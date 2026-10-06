package contentrails

import (
	"bytes"
	_ "embed"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"

	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/contentops"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/strictjson"
)

const installedManifestPath = "go-backend/internal/contentrails/sources/installed-authorities.json"
const installedPinPath = "go-backend/internal/contentrails/installed_authorities_pin.go"

//go:embed sources/installed-authorities.json
var installedAuthorityBytes []byte

//go:embed installed_authorities_pin.go
var installedPinBytes []byte

type installedAuthorities struct{ raw map[string]any }

var installedDocumentKeys = []string{"candidate", "factual_review", "quality_review", "proposal", "audit", "final_factual_review", "final_quality_review"}

func authorityPath(relative string) bool {
	return relative != "" && !filepath.IsAbs(relative) && filepath.ToSlash(filepath.Clean(relative)) == relative &&
		!strings.Contains(relative, "\\") && !strings.Contains(relative, "..") &&
		(strings.HasPrefix(relative, "docs/reviews/") || strings.HasPrefix(relative, "go-backend/internal/contentrails/sources/"))
}

func authorityDigest(v any) bool {
	return validDigest(v) && text(v) == strings.ToLower(text(v))
}

func authorityDescriptor(raw map[string]any) bool {
	return len(raw) == 2 && allowedKeys(raw, "path", "sha256") && authorityPath(text(raw["path"])) && authorityDigest(raw["sha256"])
}

// PinBytesForInstalledAuthorities renders the only permitted Go source shape
// for the separately checked metadata pin. The digest is its sole variable;
// executable statements, imports, extra declarations or comment changes refuse.
func PinBytesForInstalledAuthorities(sha string) ([]byte, error) {
	if !authorityDigest(sha) {
		return nil, fmt.Errorf("installed authority pin digest refused")
	}
	return []byte(fmt.Sprintf(`package contentrails

// This authority metadata is checked separately from the runtime audit manifest:
// including its own review/audit descriptors in that manifest would be circular.
// A changed pin never grants approval; every registered rail is reconstructed
// from its exact independent judgments and current native audit by Check.
const InstalledAuthoritiesSHA256 = %q
`, sha)), nil
}

func validateInstalledPinBytes(source, embedded []byte, sha string) error {
	expected, err := PinBytesForInstalledAuthorities(sha)
	if err != nil || !bytes.Equal(source, expected) || !bytes.Equal(embedded, expected) {
		return fmt.Errorf("installed authority pin must match immutable metadata-only template")
	}
	return nil
}

func parseInstalledAuthorities(blob []byte, expectedSHA string) (*installedAuthorities, error) {
	fail := func() (*installedAuthorities, error) {
		return nil, fmt.Errorf("installed authority schema/pin/chain refused")
	}
	if len(blob) > MaxBytes || digestBytes(blob) != expectedSHA || strictjson.Validate(blob) != nil {
		return fail()
	}
	raw, err := contentops.Decode(blob)
	if err != nil || len(raw) != 4 || !allowedKeys(raw, "schema", "version", "source_chain", "rails") || raw["schema"] != "native-content-installed-authorities-v1" || integer(raw["version"]) != 1 {
		return fail()
	}
	chain, ok := raw["source_chain"].([]any)
	if !ok || len(chain) > 999 {
		return fail()
	}
	known := map[string]bool{}
	paths := map[string]bool{}
	parent := AuthoredSHA256
	for i, v := range chain {
		entry := object(v)
		if len(entry) != 4 || !allowedKeys(entry, "path", "sha256", "version", "parent_source_sha256") || !authorityPath(text(entry["path"])) || !authorityDigest(entry["sha256"]) || integer(entry["version"]) != i+2 || entry["parent_source_sha256"] != parent || known[text(entry["sha256"])] || paths[text(entry["path"])] || entry["sha256"] == AuthoredSHA256 {
			return fail()
		}
		parent = text(entry["sha256"])
		known[parent], paths[text(entry["path"])] = true, true
	}
	rails := object(raw["rails"])
	if rails == nil || len(rails) > 3 {
		return fail()
	}
	tipUsed := len(chain) == 0
	for rail, v := range rails {
		entry := object(v)
		if FinalKind(rail) == "" || len(entry) != 9 || !allowedKeys(entry, append([]string{"source_sha256", "artifact_sha256"}, installedDocumentKeys...)...) || !known[text(entry["source_sha256"])] || !authorityDigest(entry["artifact_sha256"]) {
			return fail()
		}
		for _, key := range installedDocumentKeys {
			if !authorityDescriptor(object(entry[key])) {
				return fail()
			}
		}
		if entry["source_sha256"] == parent {
			tipUsed = true
		}
	}
	if !tipUsed {
		return fail()
	}
	return &installedAuthorities{raw: raw}, nil
}

func regularAuthorityBytes(root, relative string) ([]byte, error) {
	if !authorityPath(relative) && relative != installedPinPath {
		return nil, fmt.Errorf("installed authority path escapes protected directories")
	}
	absoluteRoot, err := filepath.Abs(root)
	if err != nil {
		return nil, err
	}
	path := absoluteRoot
	parts := append([]string{""}, strings.Split(relative, "/")...)
	type pathIdentity struct {
		path string
		info os.FileInfo
	}
	identities := []pathIdentity{}
	for i, part := range parts {
		if part != "" {
			path = filepath.Join(path, part)
		}
		info, err := os.Lstat(path)
		if err != nil || info.Mode()&os.ModeSymlink != 0 || (i < len(parts)-1 && !info.IsDir()) || (i == len(parts)-1 && !info.Mode().IsRegular()) {
			return nil, fmt.Errorf("installed authority path must be regular and non-symlinked: %s", relative)
		}
		if i == len(parts)-1 && info.Size() > MaxBytes {
			return nil, fmt.Errorf("installed authority document exceeds byte bound")
		}
		identities = append(identities, pathIdentity{path, info})
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, fmt.Errorf("installed authority document read refused: %s", relative)
	}
	defer f.Close()
	opened, err := f.Stat()
	if err != nil || !opened.Mode().IsRegular() || !os.SameFile(opened, identities[len(identities)-1].info) {
		return nil, fmt.Errorf("installed authority opened file identity changed: %s", relative)
	}
	for _, expected := range identities {
		current, err := os.Lstat(expected.path)
		if err != nil || current.Mode()&os.ModeSymlink != 0 || !os.SameFile(current, expected.info) {
			return nil, fmt.Errorf("installed authority path identity changed: %s", relative)
		}
	}
	blob, err := io.ReadAll(io.LimitReader(f, MaxBytes+1))
	if err != nil || len(blob) > MaxBytes {
		return nil, fmt.Errorf("installed authority document read refused: %s", relative)
	}
	return blob, nil
}

func authorityDocument(root string, descriptor map[string]any) ([]byte, string, error) {
	if !authorityDescriptor(descriptor) {
		return nil, "", fmt.Errorf("installed authority descriptor refused")
	}
	relative := text(descriptor["path"])
	blob, err := regularAuthorityBytes(root, relative)
	if err != nil || digestBytes(blob) != descriptor["sha256"] {
		return nil, "", fmt.Errorf("installed authority document differs from reviewed descriptor: %s", relative)
	}
	return blob, filepath.Join(root, relative), nil
}

func loadInstalledAuthorities(root string) (*installedAuthorities, error) {
	a, err := parseInstalledAuthorities(installedAuthorityBytes, InstalledAuthoritiesSHA256)
	if err != nil {
		return nil, err
	}
	blob, err := regularAuthorityBytes(root, installedManifestPath)
	if err != nil || !bytes.Equal(blob, installedAuthorityBytes) {
		return nil, fmt.Errorf("installed authority source differs from compiled reviewed manifest")
	}
	pinBytes, err := regularAuthorityBytes(root, installedPinPath)
	if err != nil || validateInstalledPinBytes(pinBytes, installedPinBytes, InstalledAuthoritiesSHA256) != nil {
		return nil, fmt.Errorf("installed authority pin source differs from compiled reviewed authority")
	}
	return a, nil
}

func (a *installedAuthorities) sources(root string) (map[string]*Source, error) {
	result := map[string]*Source{}
	for _, v := range rows(a.raw["source_chain"]) {
		e := object(v)
		descriptor := map[string]any{"path": e["path"], "sha256": e["sha256"]}
		blob, _, err := authorityDocument(root, descriptor)
		if err != nil {
			return nil, err
		}
		s, err := decodeSource(blob, text(e["parent_source_sha256"]), integer(e["version"]))
		if err != nil || s.SHA256 != e["sha256"] {
			return nil, fmt.Errorf("installed authored parent chain differs from reviewed source")
		}
		for _, archived := range object(s.Raw["archives"]) {
			if _, _, err = authorityDocument(root, object(archived)); err != nil {
				return nil, fmt.Errorf("installed authored source archive refused: %w", err)
			}
		}
		result[s.SHA256] = s
	}
	return result, nil
}

func (a *installedAuthorities) registeredParent(version int, parentSHA string) bool {
	for _, v := range rows(a.raw["source_chain"]) {
		e := object(v)
		if integer(e["version"]) == version-1 && e["sha256"] == parentSHA {
			return true
		}
	}
	return false
}

func (a *installedAuthorities) rebuild(root string, selected *Source, rail string) (map[string]any, bool, error) {
	entry := object(object(a.raw["rails"])[rail])
	if entry == nil {
		return nil, false, nil
	}
	if _, err := loadInstalledAuthorities(root); err != nil {
		return nil, true, err
	}
	sources, err := a.sources(root)
	if err != nil {
		return nil, true, err
	}
	s := sources[text(entry["source_sha256"])]
	if s == nil || selected == nil || (selected.SHA256 != AuthoredSHA256 && selected.SHA256 != s.SHA256) {
		return nil, true, fmt.Errorf("installed authority does not authorize selected authored source")
	}
	beforeRuntime, err := RuntimeHashes(root)
	if err != nil {
		return nil, true, err
	}
	beforeSources, err := bindings(root)
	if err != nil {
		return nil, true, err
	}
	paths := map[string]string{}
	for _, key := range installedDocumentKeys {
		_, path, err := authorityDocument(root, object(entry[key]))
		if err != nil {
			return nil, true, err
		}
		paths[key] = path
	}
	catalog, err := buildInstalledProposal(root, s, rail, paths["candidate"], paths["factual_review"], paths["quality_review"])
	if err != nil {
		return nil, true, err
	}
	if err = ConfirmFinal(root, rail, catalog, paths["proposal"], paths["audit"], paths["final_factual_review"], paths["final_quality_review"], text(entry["artifact_sha256"])); err != nil {
		return nil, true, err
	}
	if err = validateInstalled(root, rail, catalog, text(entry["artifact_sha256"])); err != nil {
		return nil, true, err
	}
	if _, err = a.sources(root); err != nil {
		return nil, true, err
	}
	for _, key := range installedDocumentKeys {
		if _, _, err = authorityDocument(root, object(entry[key])); err != nil {
			return nil, true, err
		}
	}
	afterRuntime, err := RuntimeHashes(root)
	if err != nil {
		return nil, true, err
	}
	afterSources, err := bindings(root)
	if err != nil || !same(beforeRuntime, afterRuntime) || !same(beforeSources, afterSources) {
		return nil, true, fmt.Errorf("installed authority runtime/source inventory changed during check")
	}
	if _, err = loadInstalledAuthorities(root); err != nil {
		return nil, true, err
	}
	return catalog, true, nil
}

// BuildInstalledAuthorityEntry constructs metadata for an already installed,
// independently reviewed rail. It neither writes a pin nor grants approval.
// The audit/final judgments must bind the frozen current export and all current
// sources, rather than the pre-installation staging snapshot.
func BuildInstalledAuthorityEntry(root string, s *Source, rail, candidate, factual, quality, proposal, audit, finalFactual, finalQuality, expectedSHA string) (map[string]any, error) {
	if s == nil || s.Version <= 1 || FinalKind(rail) == "" {
		return nil, fmt.Errorf("installed authority requires a reviewed newer source and supported rail")
	}
	if _, err := loadInstalledAuthorities(root); err != nil {
		return nil, err
	}
	beforeRuntime, err := RuntimeHashes(root)
	if err != nil {
		return nil, err
	}
	beforeSources, err := bindings(root)
	if err != nil {
		return nil, err
	}
	files := []string{candidate, factual, quality, proposal, audit, finalFactual, finalQuality}
	entry := map[string]any{"source_sha256": s.SHA256, "artifact_sha256": expectedSHA}
	for i, path := range files {
		absolute, err := filepath.Abs(path)
		if err != nil {
			return nil, err
		}
		absoluteRoot, err := filepath.Abs(root)
		if err != nil {
			return nil, err
		}
		relative, err := filepath.Rel(absoluteRoot, absolute)
		if err != nil {
			return nil, err
		}
		relative = filepath.ToSlash(relative)
		blob, err := regularAuthorityBytes(root, relative)
		if err != nil {
			return nil, err
		}
		entry[installedDocumentKeys[i]] = map[string]any{"path": relative, "sha256": digestBytes(blob)}
	}
	catalog, err := buildInstalledProposal(root, s, rail, candidate, factual, quality)
	if err != nil {
		return nil, err
	}
	if err = ConfirmFinal(root, rail, catalog, proposal, audit, finalFactual, finalQuality, expectedSHA); err != nil {
		return nil, err
	}
	if err = validateInstalled(root, rail, catalog, expectedSHA); err != nil {
		return nil, err
	}
	for _, key := range installedDocumentKeys {
		if _, _, err = authorityDocument(root, object(entry[key])); err != nil {
			return nil, err
		}
	}
	afterRuntime, err := RuntimeHashes(root)
	if err != nil {
		return nil, err
	}
	afterSources, err := bindings(root)
	if err != nil || !same(beforeRuntime, afterRuntime) || !same(beforeSources, afterSources) {
		return nil, fmt.Errorf("installed authority draft runtime/source inventory changed during construction")
	}
	if _, err = loadInstalledAuthorities(root); err != nil {
		return nil, err
	}
	return entry, nil
}
