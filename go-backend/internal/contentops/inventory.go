package contentops

import (
	"errors"
	"io/fs"
	"os"
	"path/filepath"
	"reflect"
	"sort"
	"strings"
)

// Membership matters as well as old file bytes: a newly added implementation or
// policy input must invalidate review before writes and again before publication.
func runtimeInventory(root string) ([]string, error) {
	paths := []string{}
	err := filepath.WalkDir(filepath.Join(root, "go-backend"), func(path string, entry fs.DirEntry, err error) error {
		if os.IsNotExist(err) {
			return nil
		}
		if err != nil {
			return err
		}
		if entry.IsDir() {
			return nil
		}
		if strings.HasSuffix(path, ".go") && !strings.HasSuffix(path, "_test.go") {
			paths = append(paths, path)
		}
		return nil
	})
	if err != nil {
		return nil, err
	}
	for _, name := range []string{"rules_unicode15.json", "rules_provenance.json"} {
		path := filepath.Join(root, "go-backend/internal/contentbuild", name)
		if _, err := os.Lstat(path); err == nil {
			paths = append(paths, path)
		} else if !os.IsNotExist(err) {
			return nil, err
		}
	}
	sort.Strings(paths)
	return paths, nil
}
func (s *Sources) checkInventory() error {
	actual, err := runtimeInventory(s.Root)
	if err != nil {
		return err
	}
	if !reflect.DeepEqual(s.BaseInventory, actual) {
		return errors.New("native runtime/policy source inventory changed during review")
	}
	return nil
}
