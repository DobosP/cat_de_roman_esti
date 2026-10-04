package main

import (
	"strings"
	"testing"
)

func TestAnonymousRuntimeConfigurationFailsClosed(t *testing.T) {
	names := []string{"CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS", "CAT_ACCOUNTS_ENABLED", "CAT_SUBMISSIONS_DIR", "CAT_MAX_REQUEST_BYTES", "CAT_SESSION_TTL_SECONDS", "CAT_MAX_SESSIONS_PER_GAME"}
	for _, name := range names {
		t.Setenv(name, "")
	}
	t.Setenv("CAT_MAX_REQUEST_BYTES", "65536")
	t.Setenv("CAT_SESSION_TTL_SECONDS", "7200")
	t.Setenv("CAT_MAX_SESSIONS_PER_GAME", "1000")
	if err := validateRuntimeEnvironment(); err != nil {
		t.Fatal(err)
	}
	for _, c := range []struct{ name, value string }{{"CAT_ACCOUNTS_ENABLED", "1"}, {"CAT_ACCOUNTS_ENABLED", " YES "}, {"CAT_ACCOUNTS_ENABLED", "\x1cYES\x1f"}, {"CAT_KG_FIXTURE", "synthetic.json"}, {"CAT_GAMES_PACK", "synthetic.json"}, {"CAT_BOARD_RANKINGS", "synthetic.json"}, {"CAT_MAX_REQUEST_BYTES", "4096"}, {"CAT_SESSION_TTL_SECONDS", "NaN"}, {"CAT_SESSION_TTL_SECONDS", "0"}, {"CAT_MAX_SESSIONS_PER_GAME", "0"}} {
		t.Run(c.name+"-"+c.value, func(t *testing.T) {
			t.Setenv(c.name, c.value)
			err := validateRuntimeEnvironment()
			if err == nil || !strings.Contains(err.Error(), c.name) {
				t.Fatalf("configuration notrefused byname: %v", err)
			}
			if strings.Contains(err.Error(), c.value) && c.value != "0" {
				t.Fatal("configuration error exposed value")
			}
		})
	}
	t.Setenv("CAT_MAX_REQUEST_BYTES", " +٦٥٥٣٦ ")
	t.Setenv("CAT_SESSION_TTL_SECONDS", "0.25")
	t.Setenv("CAT_MAX_SESSIONS_PER_GAME", "3")
	if err := validateRuntimeEnvironment(); err != nil {
		t.Fatal("supportedsessionconfigrefused")
	}
}

func TestNativeSubmissionConfigurationIsSupported(t *testing.T) {
	for _, name := range []string{"CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS", "CAT_ACCOUNTS_ENABLED", "CAT_MAX_REQUEST_BYTES", "CAT_SESSION_TTL_SECONDS", "CAT_MAX_SESSIONS_PER_GAME"} {
		t.Setenv(name, "")
	}
	t.Setenv("CAT_SUBMISSIONS_DIR", t.TempDir())
	t.Setenv("CAT_MAX_REQUEST_BYTES", "65536")
	t.Setenv("CAT_SESSION_TTL_SECONDS", "7200")
	t.Setenv("CAT_MAX_SESSIONS_PER_GAME", "1000")
	if err := validateRuntimeEnvironment(); err != nil {
		t.Fatal(err)
	}
}
