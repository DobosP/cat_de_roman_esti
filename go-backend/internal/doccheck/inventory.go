package doccheck

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"os"
	"path"
	"path/filepath"
	"sort"
	"strings"
	"unicode/utf8"
)

const maxInventoryBytes = 1 << 20
const maxInventoryPaths = 10000

// These are wrapper/dependency outputs, not source-document exemptions.
var generatedDirectories = map[string]bool{
	".git": true, "node_modules": true, ".gate": true,
	".vitest": true, "dist": true, "test-results": true,
}

// CheckInventory admits the externally Git-derived source inventory only when
// its complete declared Markdown set equals the actual physical source tree.
// It then runs exactly the same policies as the developer Git-based Check.
func CheckInventory(root, inventoryPath string) (Report, error) {
	r := emptyReport()
	root, err := filepath.Abs(root)
	if err != nil {
		return r, err
	}
	if err = unaliasedDirectory(root); err != nil {
		return r, err
	}
	file, err := inventoryFile(root, inventoryPath)
	if err != nil {
		return r, err
	}
	defer file.Close()
	raw, err := io.ReadAll(io.LimitReader(file, maxInventoryBytes+1))
	if err != nil {
		return r, err
	}
	paths, err := decodeInventory(raw)
	if err != nil {
		return r, err
	}
	physical, err := physicalMarkdown(root)
	if err != nil {
		return r, err
	}
	if len(physical) == 0 {
		return r, fmt.Errorf("Markdown inventory requires physical source documents")
	}
	if len(paths) != len(physical) {
		return r, fmt.Errorf("Markdown inventory differs from physical source set: declared %d, actual %d", len(paths), len(physical))
	}
	for i, name := range paths {
		if name != physical[i] {
			return r, fmt.Errorf("Markdown inventory differs from physical source set at %q (actual %q)", name, physical[i])
		}
	}
	r, err = checkFiles(root, paths)
	if err != nil {
		return r, err
	}
	if r.Files == 0 {
		return r, fmt.Errorf("Markdown inventory requires current, non-history documents")
	}
	return r, nil
}

func unaliasedDirectory(directory string) error {
	for current := directory; ; current = filepath.Dir(current) {
		info, err := os.Lstat(current)
		if err != nil {
			return err
		}
		if info.Mode()&os.ModeSymlink != 0 || !info.IsDir() {
			return fmt.Errorf("Markdown inventory directory alias refused: %s", current)
		}
		if filepath.Dir(current) == current {
			return nil
		}
	}
}

func inventoryFile(root, name string) (*os.File, error) {
	if name == "" || !utf8.ValidString(name) || strings.ContainsRune(name, '\x00') {
		return nil, fmt.Errorf("invalid Markdown inventory path")
	}
	if !filepath.IsAbs(name) {
		name = filepath.Join(root, name)
	}
	name = filepath.Clean(name)
	relative, err := filepath.Rel(root, name)
	if err != nil || relative == "." || relative == ".." || strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return nil, fmt.Errorf("Markdown inventory must be inside its source root")
	}
	if err = unaliasedDirectory(filepath.Dir(name)); err != nil {
		return nil, err
	}
	info, err := os.Lstat(name)
	if err != nil {
		return nil, err
	}
	if !info.Mode().IsRegular() || info.Size() > maxInventoryBytes {
		return nil, fmt.Errorf("Markdown inventory must be a regular file of at most %d bytes", maxInventoryBytes)
	}
	return os.Open(name)
}

func decodeInventory(raw []byte) ([]string, error) {
	if len(raw) > maxInventoryBytes || !utf8.Valid(raw) {
		return nil, fmt.Errorf("Markdown inventory size or UTF-8 refused")
	}
	decoder := json.NewDecoder(bytes.NewReader(raw))
	token, err := decoder.Token()
	if err != nil || token != json.Delim('{') {
		return nil, fmt.Errorf("Markdown inventory must be an object")
	}
	seen := map[string]bool{}
	var schema int
	var paths []string
	for decoder.More() {
		token, err = decoder.Token()
		if err != nil {
			return nil, err
		}
		key, ok := token.(string)
		if !ok || seen[key] {
			return nil, fmt.Errorf("duplicate or invalid Markdown inventory field")
		}
		seen[key] = true
		switch key {
		case "schema":
			err = decoder.Decode(&schema)
		case "paths":
			err = decoder.Decode(&paths)
		default:
			return nil, fmt.Errorf("unknown Markdown inventory field %q", key)
		}
		if err != nil {
			return nil, err
		}
	}
	if token, err = decoder.Token(); err != nil || token != json.Delim('}') {
		return nil, fmt.Errorf("invalid Markdown inventory object ending")
	}
	if decoder.Decode(new(json.RawMessage)) != io.EOF {
		return nil, fmt.Errorf("trailing Markdown inventory content")
	}
	if len(seen) != 2 || schema != 1 || len(paths) == 0 || len(paths) > maxInventoryPaths {
		return nil, fmt.Errorf("Markdown inventory schema or path count refused")
	}
	for i, name := range paths {
		if name == "" || !utf8.ValidString(name) || strings.ContainsAny(name, "\\:\x00") ||
			path.IsAbs(name) || filepath.IsAbs(name) || path.Clean(name) != name ||
			name == "." || name == ".." || strings.HasPrefix(name, "../") || !strings.HasSuffix(name, ".md") {
			return nil, fmt.Errorf("unsafe Markdown inventory path %q", name)
		}
		if i > 0 && paths[i-1] >= name {
			return nil, fmt.Errorf("Markdown inventory paths must be sorted and unique")
		}
	}
	return paths, nil
}

func physicalMarkdown(root string) ([]string, error) {
	paths := []string{}
	err := filepath.WalkDir(root, func(name string, entry fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		if entry.IsDir() {
			if name != root && generatedDirectories[entry.Name()] {
				return filepath.SkipDir
			}
			return nil
		}
		if entry.Type()&os.ModeSymlink != 0 {
			target, err := os.Stat(name)
			if strings.HasSuffix(entry.Name(), ".md") || err != nil || target.IsDir() {
				return fmt.Errorf("Markdown file or directory alias refused: %s", name)
			}
			return nil
		}
		if !strings.HasSuffix(entry.Name(), ".md") {
			return nil
		}
		if !entry.Type().IsRegular() {
			return fmt.Errorf("Markdown source must be regular: %s", name)
		}
		relative, err := filepath.Rel(root, name)
		if err != nil {
			return err
		}
		paths = append(paths, filepath.ToSlash(relative))
		if len(paths) > maxInventoryPaths {
			return fmt.Errorf("physical Markdown source exceeds %d paths", maxInventoryPaths)
		}
		return nil
	})
	sort.Strings(paths)
	return paths, err
}
