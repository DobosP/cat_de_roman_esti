// Package guibuild verifies Cat's private compiled GUI identity.
package guibuild

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/fs"
	"path"
	"strings"

	"github.com/DobosP/roedu-ui/web-kit/health"
)

const (
	ManifestPath = "dist/.vite/manifest.json"
	DescriptorPath = "build/dist/.gui-build.json"
	VersionsLockPath = "build/dist/versions.lock.json"
)

// readRegular checks each directory entry, including symlink ancestors, and
// bounds the bytes actually read. The production inputs are immutable embed.FS.
func readRegular(files fs.FS, name string, limit int64) ([]byte, error) {
	if !fs.ValidPath(name) { return nil, fmt.Errorf("invalid GUI build input path") }
	parts := strings.Split(name, "/")
	parent := "."
	for index, part := range parts {
		entries, err := fs.ReadDir(files, parent)
		if err != nil { return nil, err }
		var found fs.DirEntry
		for _, entry := range entries {
			if entry.Name() == part { found = entry; break }
		}
		if found == nil { return nil, fs.ErrNotExist }
		info, err := found.Info()
		if err != nil { return nil, err }
		if info.Mode()&fs.ModeSymlink != 0 { return nil, fmt.Errorf("GUI build input symlink refused") }
		if index < len(parts)-1 {
			if !info.IsDir() { return nil, fmt.Errorf("GUI build input ancestor is not a directory") }
		} else if !info.Mode().IsRegular() || info.Size() > limit {
			return nil, fmt.Errorf("GUI build input is nonregular or too large")
		}
		parent = path.Join(parent, part)
	}
	file, err := files.Open(name)
	if err != nil { return nil, err }
	defer file.Close()
	data, err := io.ReadAll(io.LimitReader(file, limit+1))
	if err != nil { return nil, err }
	if int64(len(data)) > limit { return nil, fmt.Errorf("GUI build input exceeds byte limit") }
	return data, nil
}

// The private descriptor has exactly the four public identity fields. Token
// decoding refuses duplicate and case-folded keys as well as extra values.
func decodeDescriptor(data []byte) (*health.Identity, error) {
	decoder := json.NewDecoder(bytes.NewReader(data))
	token, err := decoder.Token()
	if err != nil || token != json.Delim('{') { return nil, fmt.Errorf("GUI build descriptor must be an object") }
	identity := &health.Identity{}
	fields := map[string]*string{
		"sha": &identity.SHA, "tree_sha256": &identity.TreeSHA256,
		"manifest_sha256": &identity.ManifestSHA256, "versions_lock_sha256": &identity.VersionsLockSHA256,
	}
	seen := make(map[string]bool)
	for decoder.More() {
		token, err := decoder.Token()
		if err != nil { return nil, err }
		key, ok := token.(string)
		destination, known := fields[key]
		if !ok || !known || seen[key] { return nil, fmt.Errorf("GUI build descriptor field refused") }
		value, err := decoder.Token()
		if err != nil { return nil, err }
		text, ok := value.(string)
		if !ok { return nil, fmt.Errorf("GUI build descriptor field must be a string") }
		*destination = text
		seen[key] = true
	}
	if token, err = decoder.Token(); err != nil || token != json.Delim('}') || len(seen) != len(fields) {
		return nil, fmt.Errorf("GUI build descriptor is incomplete")
	}
	if _, err := decoder.Token(); err != io.EOF { return nil, fmt.Errorf("GUI build descriptor has trailing data") }
	if err := identity.Validate(); err != nil { return nil, err }
	return identity, nil
}

// Load never reads runtime environment claims. The source identifiers must be
// baked by the owning pre-image build; hashes are recomputed from compiled bytes.
func Load(assets, metadata fs.FS) (*health.Identity, error) {
	descriptor, err := readRegular(metadata, DescriptorPath, 4096)
	if err != nil { return nil, err }
	baked, err := decodeDescriptor(descriptor)
	if err != nil { return nil, err }
	manifest, err := readRegular(assets, ManifestPath, 4*1024*1024)
	if err != nil { return nil, err }
	lock, err := readRegular(metadata, VersionsLockPath, 2*1024*1024)
	if err != nil { return nil, err }
	actual, err := health.NewIdentity(baked.SHA, baked.TreeSHA256, manifest, lock)
	if err != nil { return nil, err }
	if *actual != *baked { return nil, fmt.Errorf("GUI build descriptor differs from embedded bytes") }
	return actual, nil
}
