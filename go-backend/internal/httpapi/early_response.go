package httpapi

import (
	"io"
	"net/http"
	"time"
)

// incomingBody observes consumption without reading ahead. A privacy/size gate
// can therefore return before upload and refuse HTTP/1 reuse of the unread body.
type incomingBody struct {
	io.ReadCloser
	expected, received int64
	eof                bool
}

func (b *incomingBody) Read(p []byte) (int, error) {
	n, err := b.ReadCloser.Read(p)
	b.received += int64(n)
	if err == io.EOF {
		b.eof = true
	}
	return n, err
}
func (b *incomingBody) unread() bool {
	if b.eof || b.expected == 0 {
		return false
	}
	return b.expected < 0 || b.received < b.expected
}

type refusalResponse struct {
	http.ResponseWriter
	request *http.Request
	body    *incomingBody
}

func (w *refusalResponse) Unwrap() http.ResponseWriter { return w.ResponseWriter }
func (w *refusalResponse) WriteHeader(status int) {
	if status >= 400 && w.body.unread() && w.request.ProtoMajor == 1 {
		w.Header().Set("Connection", "close")
		// net/http drains small unread bodies before sending a keepalive response.
		// Closing reuse avoids that drain, and the read deadline also bounds body
		// cleanup after response flush. The write deadline remains unchanged.
		_ = http.NewResponseController(w.ResponseWriter).SetReadDeadline(time.Now())
	}
	w.ResponseWriter.WriteHeader(status)
}
func observeRefusals(w http.ResponseWriter, r *http.Request) http.ResponseWriter {
	if r.Body == nil || r.Body == http.NoBody {
		return w
	}
	b := &incomingBody{ReadCloser: r.Body, expected: r.ContentLength}
	r.Body = b
	return &refusalResponse{ResponseWriter: w, request: r, body: b}
}
