package contentbuild

import (
	"bytes"
	"os"
	"path/filepath"
	"reflect"
	"strings"
	"testing"
)

// Literal eleven-file GUI4f36 snapshot, captured before the Source7 merge. This
// is historical test input; live Build still uses main's reviewed Source7 pins.
const reviewedSource6ContextArchive = "docs/reviews/gui-source6-runtime-requalification/reference/reviewed-source6-context.tar.gz"
const reviewedSource6ContextManifest = "docs/reviews/gui-source6-runtime-requalification/reference/reviewed-source6-context-manifest.json"
const reviewedSource6ContextArchiveSHA256 = "2340f25cbb52d84a0d668c41c9aad3bef8d960a1fdcbf85624a9ba03cfe70c7f"
const reviewedSource6ContextManifestSHA256 = "fd36c1444bc1371398a0cce522700d7d8f4fd42fb316b6052becc014573bc9d6"

func reviewedSource6HistoricalRoot(t *testing.T) string {
	t.Helper()
	return source6ContextRoot(t, reviewedSource6ContextArchive, reviewedSource6ContextManifest, reviewedSource6ContextArchiveSHA256, reviewedSource6ContextManifestSHA256, "gui-immutable-reviewed-source6-test-context-v1", "4f36abf34c98d338f35e844b9a202a5c39923121", "a220c22ec948e0738fa34d614fa033d715aee10a9ebf18369691f1dbe1166a4a", "41295fbf205e586a4abb271cf77f0bb38ea35bd4109e965ffdbe8152fc602286")
}

// The testing process-global Setenv guard refuses parallel scope. Cleanup
// restores the complete live map after success or Fatal; no production pin changes.
func reviewedSource6ReviewedPins(t *testing.T) {
	t.Helper()
	t.Setenv("CAT_CONTENTBUILD_HISTORICAL_TEST_CONTEXT", "reviewed-gui-source6")
	previous := reviewedPins
	t.Cleanup(func() { reviewedPins = previous })
	reviewedPins = map[string]string{
		"derived_catalog_v38.json": "fdc94e5ded3477b44aaffe90858ca1070cd1c1d344be22724c0e02f0110bb96a",
		"quick_games_v92.json":     "234305a844033cff0914a5213f6c0b8dcd1b21918d57cc851780259c9e87ee59",
		"release_reserve_v1.json":  "fd522b637ab87681d0e890ffb38de44fc57480bf37c302746a328d71a9219fb7",
	}
}

func TestReviewedSource6PinsRestoreAndChangedSourceRefuses(t *testing.T) {
	previous := reviewedPins
	context, hadContext := os.LookupEnv("CAT_CONTENTBUILD_HISTORICAL_TEST_CONTEXT")
	t.Run("bounded historical scope and changed quick source", func(t *testing.T) {
		root := reviewedSource6HistoricalRoot(t)
		reviewedSource6ReviewedPins(t)
		if len(reviewedPins) != 3 || reviewedPins["quick_games_v92.json"] != "234305a844033cff0914a5213f6c0b8dcd1b21918d57cc851780259c9e87ee59" {
			t.Fatal("reviewed GUI Source6 pin scope differs")
		}
		built, err := Build(root)
		if err != nil {
			t.Fatal("complete literal historical context must rebuild before mutation", err)
		}
		installed, err := os.ReadFile(filepath.Join(root, "go-backend/internal/content/bundled.json"))
		if err != nil || !bytes.Equal(built, installed) {
			t.Fatal("positive reviewed historical builder differs", err)
		}
		file := sourcePath(root, "quick_games_v92.json")
		raw, err := os.ReadFile(file)
		if err != nil {
			t.Fatal(err)
		}
		if err = os.WriteFile(file, append(raw, '\n'), 0600); err != nil {
			t.Fatal(err)
		}
		if _, err = Build(root); err == nil || !strings.Contains(err.Error(), "quick_games_v92.json: reviewed artifact digest drift") {
			t.Fatal("changed historical quick bytes bypassed the real reviewed pin", err)
		}
	})
	if !reflect.DeepEqual(reviewedPins, previous) {
		t.Fatal("live reviewed pins were not restored after reviewed GUI Source6 scope")
	}
	if value, present := os.LookupEnv("CAT_CONTENTBUILD_HISTORICAL_TEST_CONTEXT"); value != context || present != hadContext {
		t.Fatal("reviewed GUI Source6 environment scope was not restored")
	}
}
