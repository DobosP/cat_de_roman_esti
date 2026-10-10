package httpapi

import (
	"bytes"
	"compress/gzip"
	"io"
	"net/http/httptest"
	"strings"
	"testing"
	"testing/fstest"

	"github.com/andybalholm/brotli"
)

// These synthetic current-tree fixtures exercise Cat through the unchanged SDK.
// They do not replace producer validation or a real image/network qualification.
func managedCompressionFixture(t *testing.T, precompressed bool) (*Server, fstest.MapFS, []string) {
	t.Helper()
	files := managedSPAFixture()
	assets := []string{"/assets/app-1234abcd.js", "/assets/app-1234abcd.css"}
	files["dist"+assets[0]].Data = []byte(strings.Repeat("console.log('compresie română, aceeași sursă');\n", 128))
	files["dist"+assets[1]].Data = []byte(strings.Repeat(".card{color:#123456}/* aceeași sursă */\n", 128))
	if precompressed {
		for _, asset := range assets {
			body := files["dist"+asset].Data
			var gz bytes.Buffer
			gzipWriter := gzip.NewWriter(&gz)
			if _, err := gzipWriter.Write(body); err != nil {
				t.Fatal(err)
			}
			if err := gzipWriter.Close(); err != nil {
				t.Fatal(err)
			}
			var br bytes.Buffer
			brotliWriter := brotli.NewWriterLevel(&br, 11)
			if _, err := brotliWriter.Write(body); err != nil {
				t.Fatal(err)
			}
			if err := brotliWriter.Close(); err != nil {
				t.Fatal(err)
			}
			files["dist"+asset+".gz"] = &fstest.MapFile{Data: bytes.Clone(gz.Bytes())}
			files["dist"+asset+".br"] = &fstest.MapFile{Data: bytes.Clone(br.Bytes())}
		}
	}
	s := testServer(t)
	var err error
	s.managedUI, err = newManagedSPA(files, "current")
	if err != nil {
		t.Fatal(err)
	}
	s.managedUIError = nil
	return s, files, assets
}

func managedCompressionRequest(s *Server, method, asset, encoding, validator string) *httptest.ResponseRecorder {
	r := httptest.NewRequest(method, asset, nil)
	r.Header.Set("Accept-Encoding", encoding)
	if validator != "" {
		r.Header.Set("If-None-Match", validator)
	}
	w := httptest.NewRecorder()
	s.ServeHTTP(w, r)
	return w
}

func assertManagedCompressionMetadata(t *testing.T, w *httptest.ResponseRecorder) {
	t.Helper()
	if w.Header().Get("Cache-Control") != "max-age=315360000, public, immutable" || w.Header().Get("ETag") == "" || w.Header().Get("X-Content-Type-Options") != "nosniff" {
		t.Fatalf("successful SDK representation lost validator/cache/type metadata: %d %v", w.Code, w.Header())
	}
	for _, value := range w.Header().Values("Vary") {
		for _, token := range strings.Split(value, ",") {
			if strings.EqualFold(strings.TrimSpace(token), "Accept-Encoding") {
				return
			}
		}
	}
	t.Fatal("SDK representation lost Accept-Encoding Vary")
}

func TestManagedCompressionActualSDKRepresentations(t *testing.T) {
	s, files, assets := managedCompressionFixture(t, true)
	for _, asset := range assets {
		for _, encoding := range []string{"identity", "gzip", "br"} {
			t.Run(asset+"/"+encoding, func(t *testing.T) {
				w := managedCompressionRequest(s, "GET", asset, encoding, "")
				if w.Code != 200 {
					t.Fatalf("actual SDK refused representation: %d", w.Code)
				}
				assertManagedCompressionMetadata(t, w)
				raw := files["dist"+asset].Data
				var decoded io.Reader = bytes.NewReader(w.Body.Bytes())
				switch encoding {
				case "identity":
					if w.Header().Get("Content-Encoding") != "" || !bytes.Equal(w.Body.Bytes(), raw) {
						t.Fatal("explicit identity request changed raw source bytes")
					}
				case "gzip":
					if w.Header().Get("Content-Encoding") != "gzip" || !bytes.Equal(w.Body.Bytes(), files["dist"+asset+".gz"].Data) {
						t.Fatal("SDK did not serve the actual gzip sidecar bytes")
					}
					reader, err := gzip.NewReader(bytes.NewReader(w.Body.Bytes()))
					if err != nil {
						t.Fatal(err)
					}
					defer reader.Close()
					decoded = reader
				case "br":
					if w.Header().Get("Content-Encoding") != "br" || !bytes.Equal(w.Body.Bytes(), files["dist"+asset+".br"].Data) {
						t.Fatal("SDK did not serve the actual Brotli sidecar bytes")
					}
					decoded = brotli.NewReader(bytes.NewReader(w.Body.Bytes()))
				}
				body, err := io.ReadAll(io.LimitReader(decoded, int64(len(raw))+1))
				if err != nil || !bytes.Equal(body, raw) {
					t.Fatal("actual representation did not decode to the original source bytes: ", err)
				}
				if strings.HasSuffix(asset, ".js") && !strings.Contains(w.Header().Get("Content-Type"), "javascript") || strings.HasSuffix(asset, ".css") && !strings.Contains(w.Header().Get("Content-Type"), "text/css") {
					t.Fatal("encoded representation changed source media type")
				}
			})
		}
	}
}

func TestManagedCompressionHeadAndConditionalSDKMetadata(t *testing.T) {
	s, _, assets := managedCompressionFixture(t, true)
	for _, asset := range assets {
		for _, encoding := range []string{"identity", "gzip", "br"} {
			t.Run(asset+"/"+encoding, func(t *testing.T) {
				get := managedCompressionRequest(s, "GET", asset, encoding, "")
				if get.Code != 200 {
					t.Fatal("GET did not establish the actual SDK representation")
				}
				assertManagedCompressionMetadata(t, get)
				validator := get.Header().Get("ETag")
				head := managedCompressionRequest(s, "HEAD", asset, encoding, "")
				if head.Code != 200 || head.Body.Len() != 0 || head.Header().Get("ETag") != validator {
					t.Fatal("SDK HEAD changed status, bodylessness or representation validator")
				}
				assertManagedCompressionMetadata(t, head)
				for _, method := range []string{"GET", "HEAD"} {
					conditional := managedCompressionRequest(s, method, asset, encoding, validator)
					if conditional.Code != 304 || conditional.Body.Len() != 0 || conditional.Header().Get("ETag") != validator || conditional.Header().Get("Content-Range") != "" {
						t.Fatalf("SDK conditional %s changed its actual representation contract: %d %v", method, conditional.Code, conditional.Header())
					}
					assertManagedCompressionMetadata(t, conditional)
				}
			})
		}
	}
}

func TestManagedCompressionMissingSidecarsRetainIdentityFallback(t *testing.T) {
	s, files, assets := managedCompressionFixture(t, false)
	for _, asset := range assets {
		for _, encoding := range []string{"gzip", "br"} {
			t.Run(asset+"/"+encoding, func(t *testing.T) {
				w := managedCompressionRequest(s, "GET", asset, encoding, "")
				if w.Code != 200 || w.Header().Get("Content-Encoding") != "" || !bytes.Equal(w.Body.Bytes(), files["dist"+asset].Data) {
					t.Fatal("missing sidecar did not retain the actual SDK identity fallback")
				}
				assertManagedCompressionMetadata(t, w)
			})
		}
	}
}

func TestManagedCompressionDirectSidecarsRemainPrivate(t *testing.T) {
	s, files, assets := managedCompressionFixture(t, true)
	for _, asset := range assets {
		for _, suffix := range []string{".gz", ".br"} {
			for _, method := range []string{"GET", "HEAD"} {
				t.Run(method+asset+suffix, func(t *testing.T) {
					w := managedCompressionRequest(s, method, asset+suffix, "gzip, br", "")
					if w.Code != 404 || w.Header().Get("Content-Encoding") != "" || strings.Contains(w.Header().Get("Cache-Control"), "immutable") || bytes.Equal(w.Body.Bytes(), files["dist"+asset+suffix].Data) {
						t.Fatalf("direct compressed filename escaped the unchanged SDK refusal: %d %v", w.Code, w.Header())
					}
				})
			}
		}
	}
}
