package httpapi

import (
	"testing"
	"testing/fstest"
)

// DCR-1: cat-server refuses to serve on this error, so it must name every
// managed admission failure and nothing once StaticRoot replaces delivery.
func TestManagedUIErrorReportsOnlyActiveManagedDelivery(t *testing.T) {
	t.Setenv("CAT_CSP_ENFORCE", "")
	files := managedSPAFixture()
	s := testServer(t)
	s.managedUI, s.managedUIError = newManagedSPA(files, "current")
	if s.managedUI == nil || s.ManagedUIError() != nil {
		t.Fatalf("admitted managed UI reported %v", s.ManagedUIError())
	}
	for name, admit := range map[string]func() (*managedSPA, error){
		"unbuilt scaffold": func() (*managedSPA, error) {
			return newManagedSPA(fstest.MapFS{"dist/.keep": &fstest.MapFile{}}, "current")
		},
		"unbounded CAT_UI": func() (*managedSPA, error) { return newManagedSPA(files, "invalid") },
		"invalid CAT_CSP_ENFORCE": func() (*managedSPA, error) {
			t.Setenv("CAT_CSP_ENFORCE", "yes")
			defer t.Setenv("CAT_CSP_ENFORCE", "")
			return newManagedSPA(files, "current")
		},
	} {
		s.StaticRoot = ""
		s.managedUI, s.managedUIError = admit()
		if s.managedUI != nil || s.managedUIError == nil || s.ManagedUIError() != s.managedUIError {
			t.Fatalf("%s: ManagedUIError = %v, admission error %v", name, s.ManagedUIError(), s.managedUIError)
		}
		s.StaticRoot = t.TempDir()
		if err := s.ManagedUIError(); err != nil {
			t.Fatalf("%s: StaticRoot override still reported %v", name, err)
		}
	}
}
