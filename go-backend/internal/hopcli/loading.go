package hopcli

import (
	"context"
	"github.com/DobosP/cat_de_roman_esti/go-backend/internal/roeduclient"
)

// LoadOnline retains the original CLI's health-only offline fallback. A healthy
// server's content refusal, malformed response or missing provenance is an error
// and cannot silently turn into offline success.
func LoadOnline(ctx context.Context, c *roeduclient.Client, fixture, category, difficulty string) (b *Bundle, fallback bool, err error) {
	h, healthErr := c.Health(ctx)
	if healthErr != nil || h["ok"] == false {
		b, err = ReadFixture(fixture)
		return b, true, err
	}
	raw, err := c.Load(ctx, category, difficulty)
	if err != nil {
		return nil, false, err
	}
	b, err = Parse(raw)
	return b, false, err
}
