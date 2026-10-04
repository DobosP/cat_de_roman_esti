// Package roeduclient implements the read-only RO-EDU /v1 contract without
// importing producer internals. Fetches are bounded and refusal is an error.
package roeduclient

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"regexp"
	"strings"
	"time"
)

type Record = map[string]any

type Limits struct {
	PageSize, Pages, Records int
	PageBytes                int64
}

func DefaultLimits() Limits { return Limits{200, 500, 50000, 4 << 20} }

type Client struct {
	base   *url.URL
	key    string
	http   *http.Client
	limits Limits
}

var snapshotGrammar = regexp.MustCompile(`^(sha256|live)-[0-9a-f]{64}$`)
var ErrUnavailable = errors.New("RO-EDU product unavailable")

type Page struct {
	Available  bool     `json:"available"`
	Records    []Record `json:"records"`
	NextCursor string   `json:"next_cursor"`
	SnapshotID string   `json:"snapshot_id"`
	ReleaseID  *string  `json:"release_id"`
	Note       string   `json:"note"`
}
type Product struct {
	Records []Record       `json:"records"`
	Pages   []PageIdentity `json:"pages"`
}
type PageIdentity struct {
	SnapshotID string  `json:"snapshot_id"`
	ReleaseID  *string `json:"release_id"`
}

// New refuses URL credentials and redirects, which must never forward API keys.
func New(base, key string, limits Limits) (*Client, error) {
	u, err := url.Parse(base)
	if err != nil || u.Host == "" || (u.Scheme != "http" && u.Scheme != "https") || u.User != nil || u.RawQuery != "" || u.Fragment != "" {
		return nil, errors.New("RO-EDU requires an HTTP(S) base URL without credentials, query or fragment")
	}
	if limits.PageSize < 1 || limits.PageSize > 500 || limits.Pages < 1 || limits.Pages > 10000 || limits.Records < 1 || limits.Records > 100000 || limits.PageBytes < 1 || limits.PageBytes > 16<<20 {
		return nil, errors.New("invalid RO-EDU bounds")
	}
	u.Path = strings.TrimRight(u.Path, "/")
	return &Client{u, key, &http.Client{Timeout: 30 * time.Second, CheckRedirect: func(_ *http.Request, _ []*http.Request) error { return http.ErrUseLastResponse }}, limits}, nil
}
func (c *Client) get(ctx context.Context, path string, query url.Values, out any) error {
	u := *c.base
	u.Path += path
	u.RawQuery = query.Encode()
	req, err := http.NewRequestWithContext(ctx, http.MethodGet, u.String(), nil)
	if err != nil {
		return err
	}
	req.Header.Set("Accept", "application/json")
	req.Header.Set("X-API-Key", c.key)
	resp, err := c.http.Do(req)
	if err != nil {
		return errors.New("RO-EDU transport failed")
	}
	defer resp.Body.Close()
	if resp.StatusCode != http.StatusOK {
		return fmt.Errorf("RO-EDU HTTP status %d", resp.StatusCode)
	}
	raw, err := io.ReadAll(io.LimitReader(resp.Body, c.limits.PageBytes+1))
	if err != nil {
		return errors.New("RO-EDU response read failed")
	}
	if int64(len(raw)) > c.limits.PageBytes {
		return errors.New("RO-EDU page byte cap exceeded")
	}
	if err = validateWire(raw); err != nil {
		return err
	}
	d := json.NewDecoder(bytes.NewReader(raw))
	d.UseNumber()
	if err = d.Decode(out); err != nil {
		return errors.New("RO-EDU invalid JSON response")
	}
	if d.Decode(new(any)) != io.EOF {
		return errors.New("RO-EDU trailing JSON response")
	}
	return nil
}
func (c *Client) Health(ctx context.Context) (Record, error) {
	var h Record
	err := c.get(ctx, "/v1/health", nil, &h)
	if err == nil && h == nil {
		err = errors.New("RO-EDU invalid health response")
	}
	return h, err
}
func (c *Client) Products(ctx context.Context) ([]Record, error) {
	var p []Record
	err := c.get(ctx, "/v1/products", nil, &p)
	return p, err
}
func (c *Client) Page(ctx context.Context, product, cursor string, filters url.Values) (Page, error) {
	if product != "kg_nodes" && product != "kg_edges" && product != "kg_puzzles" {
		return Page{}, errors.New("unsupported RO-EDU product")
	}
	q := url.Values{}
	for k, v := range filters {
		if k == "cursor" || k == "limit" {
			return Page{}, errors.New("reserved pagination filter")
		}
		q[k] = append([]string{}, v...)
	}
	q.Set("limit", fmt.Sprint(c.limits.PageSize))
	if cursor != "" {
		q.Set("cursor", cursor)
	}
	var p Page
	err := c.get(ctx, "/v1/products/"+product, q, &p)
	if err != nil {
		return p, err
	}
	if !p.Available {
		if p.Note == "snapshot changed during read" {
			return p, errors.New("RO-EDU torn snapshot read")
		}
		return p, ErrUnavailable
	}
	if p.Records == nil {
		return p, errors.New("RO-EDU missing record array")
	}
	if len(p.Records) > c.limits.PageSize {
		return p, errors.New("RO-EDU page record cap exceeded")
	}
	if p.SnapshotID != "" && !snapshotGrammar.MatchString(p.SnapshotID) {
		return p, errors.New("RO-EDU invalid snapshot identity")
	}
	if p.ReleaseID != nil && (*p.ReleaseID != p.SnapshotID || !strings.HasPrefix(p.SnapshotID, "sha256-")) {
		return p, errors.New("RO-EDU invalid release identity")
	}
	if len(p.NextCursor) > 4096 {
		return p, errors.New("RO-EDU cursor byte cap exceeded")
	}
	return p, nil
}
func (c *Client) Fetch(ctx context.Context, product string, filters url.Values, maxRecords int) (Product, error) {
	if maxRecords < 1 || maxRecords > c.limits.Records {
		return Product{}, errors.New("invalid product record cap")
	}
	out := Product{Records: []Record{}, Pages: []PageIdentity{}}
	seen := map[string]bool{}
	ids := map[string]bool{}
	cursor := ""
	var identity string
	for n := 0; n < c.limits.Pages; n++ {
		p, err := c.Page(ctx, product, cursor, filters)
		if err != nil {
			return Product{}, err
		}
		if n == 0 {
			identity = p.SnapshotID
		} else if p.SnapshotID != identity {
			return Product{}, errors.New("RO-EDU snapshot changed across pages")
		}
		if len(out.Records)+len(p.Records) > maxRecords {
			return Product{}, errors.New("RO-EDU product record cap exceeded")
		}
		for _, rec := range p.Records {
			id, _ := rec["id"].(string)
			if id == "" || ids[id] {
				return Product{}, errors.New("RO-EDU missing or duplicate record identity")
			}
			ids[id] = true
			out.Records = append(out.Records, rec)
		}
		out.Pages = append(out.Pages, PageIdentity{p.SnapshotID, p.ReleaseID})
		if p.NextCursor == "" {
			return out, nil
		}
		if seen[p.NextCursor] {
			return Product{}, errors.New("RO-EDU repeated pagination cursor")
		}
		seen[p.NextCursor] = true
		cursor = p.NextCursor
	}
	return Product{}, errors.New("RO-EDU page cap exceeded")
}

// PublicLegal rejects unknown permissions and preserves all source fields.
func PublicLegal(r Record) bool {
	access, _ := r["access_type"].(string)
	basis, _ := r["legal_basis"].(string)
	return r["redistributable"] == true && r["gdpr_relevant"] == false && strings.TrimSpace(basis) != "" && (access == "public_document" || access == "open_license" || access == "public_domain")
}
