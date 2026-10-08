package health

import (
	"bytes"
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"net/http"
	"strings"
)

// Identity is the shared HTTP witness for the source, embedded asset manifest
// and version lock in an app binary. Treat it as immutable after construction.
// The host gate separately verifies the built/running image IDs; this type
// neither inspects Docker nor reads the filesystem, environment or credentials.
type Identity struct {
	SHA string `json:"sha"`
	TreeSHA256 string `json:"tree_sha256"`
	ManifestSHA256 string `json:"manifest_sha256"`
	VersionsLockSHA256 string `json:"versions_lock_sha256"`
}

func validIdentityHex(value string, length int) bool {
	if len(value) != length || strings.ToLower(value) != value { return false }
	decoded, err := hex.DecodeString(value)
	if err != nil { return false }
	for _, value := range decoded { if value != 0 { return true } }
	return false
}

func validIdentityJSON(data []byte) bool {
	trimmed := bytes.TrimSpace(data)
	return len(trimmed) > 0 && trimmed[0] == '{' && json.Valid(data)
}

// NewIdentity validates the Git SHA/tree digest and hashes the exact JSON
// bytes supplied by the app's embed.FS. Empty, malformed JSON or placeholder
// zero identifiers fail before a qualifying HTTP witness can be served.
func NewIdentity(sha, tree string, manifest, versionsLock []byte) (*Identity, error) {
	if !validIdentityHex(sha, 40) || !validIdentityHex(tree, 64) { return nil, fmt.Errorf("identity requires a complete Git SHA and tree digest") }
	if !validIdentityJSON(manifest) { return nil, fmt.Errorf("identity requires the actual manifest JSON object bytes") }
	if !validIdentityJSON(versionsLock) { return nil, fmt.Errorf("identity requires the actual versions lock JSON object bytes") }
	manifestHash := sha256.Sum256(manifest)
	versionsHash := sha256.Sum256(versionsLock)
	return &Identity{
		SHA: sha,
		TreeSHA256: tree,
		ManifestSHA256: hex.EncodeToString(manifestHash[:]),
		VersionsLockSHA256: hex.EncodeToString(versionsHash[:]),
	}, nil
}

// Validate also protects consumers accidentally registering a zero-value or
// partially constructed Identity instead of calling NewIdentity.
func (i *Identity) Validate() error {
	if i == nil || !validIdentityHex(i.SHA,40) || !validIdentityHex(i.TreeSHA256,64) || !validIdentityHex(i.ManifestSHA256,64) || !validIdentityHex(i.VersionsLockSHA256,64) {
		return fmt.Errorf("identity is incomplete or invalid")
	}
	return nil
}

// ServeHTTP emits only a valid witness, with no cache and no mutation endpoint.
// It returns 500 for an invalid identity rather than reporting empty evidence.
func (i *Identity) ServeHTTP(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Cache-Control","no-store")
	if r.Method != http.MethodGet && r.Method != http.MethodHead { w.Header().Set("Allow","GET, HEAD"); http.Error(w,"method not allowed",http.StatusMethodNotAllowed); return }
	if err := i.Validate(); err != nil { http.Error(w,"identity unavailable",http.StatusInternalServerError); return }
	w.Header().Set("Content-Type","application/json")
	if r.Method == http.MethodHead { w.WriteHeader(http.StatusOK); return }
	_ = json.NewEncoder(w).Encode(i)
}

// Handler is convenient for routers accepting http.Handler. Identity itself
// also implements http.Handler, so mux.Handle(path, identity) is equivalent.
func (i *Identity) Handler() http.Handler { return i }
