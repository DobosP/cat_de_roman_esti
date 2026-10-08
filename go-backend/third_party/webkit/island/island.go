// Package island emits the server half of the frozen npm loader protocol.
package island

import (
	"context"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"html"
	"io"
	"regexp"
	"strings"
	"sync/atomic"

	"github.com/a-h/templ"
	"github.com/DobosP/roedu-ui/web-kit/csp"
)

type idsKey struct{}
var safeName=regexp.MustCompile(`^[A-Za-z][A-Za-z0-9_-]*$`)

// WithIDs starts a deterministic per-response sequence. Engine.Render installs
// it automatically. A standalone templ page should install it once at its root.
func WithIDs(ctx context.Context) context.Context {
	if _,ok:=ctx.Value(idsKey{}).(*atomic.Uint64);ok { return ctx }
	return context.WithValue(ctx,idsKey{},&atomic.Uint64{})
}

// Options configures server delivery without changing the payload passed to
// mount. Disabled renders only Skeleton (the app's kill switch).
type Options struct {
	Props any
	Load string
	Skeleton templ.Component
	Legacy string
	Disabled bool
	ID string
}

// Island emits light-DOM server markup and a nonced JSON payload. JSON's HTML
// escaping prevents </script>, U+2028 and U+2029 from breaking out of the body.
func Island(name string,props any) templ.Component {
	o,ok:=props.(Options);if !ok { o=Options{Props:props} }
	return templ.ComponentFunc(func(ctx context.Context,w io.Writer) error {
		if !safeName.MatchString(name) { return fmt.Errorf("invalid island name") }
		load:=o.Load;if load=="" { load="eager" }
		if load!="eager" && load!="visible" && load!="idle" && load!="interaction" { return fmt.Errorf("invalid island load mode") }
		if o.Disabled { if o.Skeleton!=nil { return o.Skeleton.Render(ctx,w) }; return nil }
		nonce:=csp.Nonce(ctx);if nonce=="" { return fmt.Errorf("island requires CSP nonce") }
		payload,err:=json.Marshal(o.Props);if err!=nil { return fmt.Errorf("island props: %w",err) }
		id:=o.ID
		if id!="" && !safeName.MatchString(id) { return fmt.Errorf("invalid island props ID") }
		if id=="" {
			if seq,ok:=ctx.Value(idsKey{}).(*atomic.Uint64);ok { id=fmt.Sprintf("roedu-props-%d",seq.Add(1)) } else {
				sum:=sha256.Sum256(append([]byte(name+"\x00"),payload...));id="roedu-props-"+hex.EncodeToString(sum[:8])
			}
		}
		var b strings.Builder
		fmt.Fprintf(&b,`<div data-island="%s" data-props="%s" data-load="%s"`,html.EscapeString(name),html.EscapeString(id),load)
		if o.Legacy!="" {
			if !strings.HasPrefix(o.Legacy,"/") || strings.HasPrefix(o.Legacy,"//") || strings.ContainsAny(o.Legacy,"\r\n\\") { return fmt.Errorf("invalid legacy script URL") }
			fmt.Fprintf(&b,` data-legacy="%s"`,html.EscapeString(o.Legacy))
		}
		b.WriteString(">")
		if o.Skeleton!=nil { if err:=o.Skeleton.Render(ctx,&b);err!=nil { return err } }
		fmt.Fprintf(&b,`</div><script type="application/json" id="%s" nonce="%s">%s</script>`,html.EscapeString(id),html.EscapeString(nonce),payload)
		_,err=io.WriteString(w,b.String());return err
	})
}
