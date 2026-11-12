//go:build linux

package contentrails

import "testing"

func TestQuickBridgeReplayStrictSignatureBoundary(t *testing.T) {
	cases := []struct {
		when   string
		accept bool
	}{
		{"2026-11-10T12:59:59.999999999Z", false},
		{"2026-11-10T13:00:00Z", false},
		{"2026-11-10T13:00:00.000000001Z", true},
		{"2026-11-10T15:00:00Z", true},
		{"2026-11-10T15:00:00.000000001Z", false},
	}
	for _, c := range cases {
		t.Run(c.when, func(t *testing.T) {
			f := newBridgeBlindFixture(t)
			_, identities, err := bridgeReviews(f.pending, f.dossiers, f.material, f.files)
			if err != nil {
				t.Fatal(err)
			}
			object(rows(f.material["operator_replay"]["replays"])[0])["replayed_at"] = c.when
			err = bridgeCritic(f.root, f.frame, f.pending, f.dossiers, f.public, f.private, f.material, f.consumer, identities, f.files)
			if (err == nil) != c.accept {
				t.Fatalf("accept=%v, error=%v", c.accept, err)
			}
		})
	}
}
