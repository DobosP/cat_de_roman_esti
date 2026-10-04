package doccheck

import "testing"

func TestIndependentFleetTermCorpus(t *testing.T) {
	for _, s := range []string{"gpt-5.6-sol", "gpt-5.6-terra/medium", "gpt-5.6-luna", "claude-fable-5-1", "gpt-4o-mini-tts", "Fable 5.1", "claude-opus-5", "claude-sonnet-5", "claude-haiku-4-5-20251001", "Haiku 4.5", "ran gpt-5.", "a gpt-5.6 run", "photo3"} {
		if len(StaleTerms(s)) != 0 {
			t.Error("false positive", s)
		}
	}
	for _, s := range []string{"gpt-5.5", "gpt-5.4-mini", "gpt-5", "gpt-5.0", "claude-opus-4-8", "Opus 4.1", "Fable 5 ", "GPT-6", "o3-mini", "Claude 5.0", "gpt-4o", "claude-fable-5", "Sonnet 4", "claude 3.5", "the o3 model"} {
		if len(StaleTerms(s)) == 0 {
			t.Error("missed stale", s)
		}
	}
}
func TestIndependentFleetRetiredCorpus(t *testing.T) {
	for _, s := range []string{"agent-ops scope: <id> (<kind>)", "the agent-ops status doc", "run ops update-foo instead", "the ops.psx wrapper", "an agent-ops parking policy"} {
		if len(RetiredVerbs(s)) != 0 {
			t.Error("false positive", s)
		}
	}
	for _, s := range []string{"./ops tabs", "`ops park`", ".\\ops.ps1 park", "ops scope main --workspace", "ops new claude api-review", "ops pin TAB", "ops resume", "sync --handoff"} {
		if len(RetiredVerbs(s)) == 0 {
			t.Error("missed retired", s)
		}
	}
}
func TestWrappedProhibition(t *testing.T) {
	lines := []string{"names are never written as Fable 5, Claude 5.0,", "GPT-6, or any invented name."}
	if !guarded(lines, 0, staleGuard) || !guarded(lines, 1, staleGuard) || guarded([]string{"ran on Opus 4.1 today"}, 0, staleGuard) {
		t.Fatal("prohibition guard")
	}
}
