package contentrails

// Offline unit fixtures only. These exercise the typed validator after the
// independent file loader has frozen its closure. They create no reviews,
// proposals, admissions, network events or usable Root trust receipts.
import (
	"encoding/json"
	"fmt"
	"sort"
	"strings"
	"testing"
	"time"
)

type cacheFixture struct {
	root, base, inventory                  string
	packet, evidenceBytes                  []byte
	boards                                 []any
	seal, evidence, binding, controls, ack map[string]any
	inputs                                 map[string][]byte
	pin                                    QuickCachePin
}

func (f *cacheFixture) put(path string, v any) map[string]any {
	b, _ := Render(v)
	f.inputs[path] = b
	return map[string]any{"path": path, "sha256": digestBytes(b), "bytes": len(b)}
}
func (f *cacheFixture) finish() {
	f.binding["source_controls"] = f.put("/scratch/controls", f.controls)
	f.binding["inspection_ack"] = f.put("/scratch/ack", f.ack)
	ref := f.put("/scratch/binding", f.binding)
	f.pin = QuickCachePin{"/scratch/binding", text(ref["sha256"])}
	f.evidence["cache_binding"] = ref
	f.evidenceBytes, _ = Render(f.evidence)
	f.seal["evidence_sha256"] = digestBytes(f.evidenceBytes)
	f.seal["cache_binding_sha256"] = f.pin.SHA256
}
func (f *cacheFixture) check() error {
	return pendingEvidenceV2(f.root, f.base, f.inventory, f.packet, f.evidenceBytes, f.boards, f.seal, f.evidence, f.binding, f.inputs, f.pin)
}
func newCacheFixture(t *testing.T) *cacheFixture {
	t.Helper()
	f := &cacheFixture{root: "/fixture/root", base: strings.Repeat("b", 64), inventory: strings.Repeat("c", 64), inputs: map[string][]byte{}}
	urls, receipts, deliveries, inspected, captures := []any{}, []any{}, []any{}, []any{}, []any{}
	journal := ""
	first := time.Date(2026, 11, 11, 10, 0, 0, 0, time.UTC)
	for i := 0; i < 13; i++ {
		u := fmt.Sprintf("https://ro.wikipedia.org/wiki/Fixture%02d", i)
		urls = append(urls, u)
		body := []byte(fmt.Sprintf("offline fixture body %d", i))
		path := "/scratch/" + digestBytes(body) + ".body"
		f.inputs[path] = body
		role := "author"
		fetch := first
		kind := "new_response"
		if i >= 11 {
			role = "factual"
			fetch = first.Add(-24 * time.Hour)
			kind = "cache_hit"
		}
		raw := map[string]any{"url": u, "sha256": digestBytes(body), "status": 200, "bytes": len(body), "fetched_by_role": role, "fetched_at": json.Number(fmt.Sprint(fetch.Unix())), "headers": map[string]any{"content-type": "text/plain", "content-signal": "", "retry-after": ""}}
		ref := f.put("/scratch/"+digestBytes([]byte(u))+".receipt.json", raw)
		b, _ := json.Marshal(raw)
		journal += string(b) + "\n"
		receipts = append(receipts, map[string]any{"url": u, "capture_path": path, "capture_sha256": digestBytes(body), "bytes": len(body), "fetched_by_role": role, "fetched_at": fetch.Format(time.RFC3339Nano)})
		inspected = append(inspected, map[string]any{"url": u, "capture_path": path, "capture_sha256": digestBytes(body), "bytes": len(body), "first_receipt_sha256": ref["sha256"]})
		captures = append(captures, map[string]any{"exit": 0, "receipt": raw, "requested_role": "author", "started_at": "2026-11-11T10:00:00Z", "stderr": "", "url": u})
		deliveries = append(deliveries, map[string]any{"url": u, "first_receipt": ref, "attempt_sha256": "later", "result_row": i, "requested_role": "author", "delivery_kind": kind, "requested_at": "2026-11-11T10:00:00Z", "client_requested_at": "2026-11-11T10:00:00Z", "observed_by": "2026-11-11T10:01:00Z", "observation_kind": "observed_by"})
	}
	// Nine citations, thirteen actual body exposures, including two factual-first
	// cited members that may never become reviewer novelty by removing sources.
	citations := append(append([]any{}, urls[:7]...), urls[11:]...)
	f.boards = []any{map[string]any{"id": "iq92_fixture", "sources": citations}}
	f.packet, _ = Render(map[string]any{"schema": "quick-author-packet-v1", "baseline_source_sha256": f.base, "boards": f.boards})
	result := f.put("/scratch/attempt", map[string]any{"schema": "cat-m3-actual-author-source-capture-attempt-1", "all_cache_first_fetch_roles_retained": true, "author_capture_seal_yet": false, "author_context": "/root/fixture_author", "cache": "/scratch", "captures": captures, "client_sha256": quickApprovedManualClient, "source_judgment_or_admission": nil})
	for _, v := range deliveries {
		object(v)["attempt_sha256"] = result["sha256"]
	}
	f.inputs["/scratch/receipts.jsonl"] = []byte(journal)
	journalRef := map[string]any{"path": "/scratch/receipts.jsonl", "bytes": len(journal), "sha256": digestBytes([]byte(journal))}
	deniedBytes, _ := json.Marshal(map[string]any{"host": "dexonline.ro", "reason": "run dropped", "at": json.Number("1794000000")})
	f.inputs["/scratch/owner-refusals.jsonl"] = deniedBytes
	denied := map[string]any{"path": "/scratch/owner-refusals.jsonl", "bytes": len(deniedBytes), "sha256": digestBytes(deniedBytes)}
	robotBody := []byte("User-agent: *\nAllow: /\n")
	f.inputs["/scratch/"+digestBytes(robotBody)+".body"] = robotBody
	robotRef := map[string]any{"path": "/scratch/" + digestBytes(robotBody) + ".body", "bytes": len(robotBody), "sha256": digestBytes(robotBody)}
	robotReceipt := f.put("/scratch/"+digestBytes([]byte("https://ro.wikipedia.org/robots.txt"))+".receipt.json", map[string]any{"url": "https://ro.wikipedia.org/robots.txt", "sha256": digestBytes(robotBody), "status": 200, "bytes": len(robotBody), "fetched_by_role": "policy", "fetched_at": json.Number("1794300000"), "headers": map[string]any{"content-type": "text/plain", "content-signal": "", "retry-after": ""}})
	state := f.put("/scratch/ro.wikipedia.org.json", map[string]any{"last_start": json.Number("1794300000")})
	terms := f.put("/scratch/terms", map[string]any{"fixture": "offline existing terms observation"})
	f.controls = map[string]any{"schema": "quick-cache-current-controls-v1", "run_id": "fixture-run", "client_sha256": quickApprovedManualClient, "checked_at": "2026-11-11T10:02:00Z", "terms_checked_by": "agent:codex", "terms_evidence": []any{terms}, "hosts": []any{map[string]any{"host": "ro.wikipedia.org", "state": state, "robots_receipt": robotReceipt, "robots_body": robotRef}}}
	f.ack = map[string]any{"schema": "quick-author-inspection-ack-v1", "author": "fixture author", "root": f.root, "baseline_source_sha256": f.base, "inventory_sha256": f.inventory, "packet_sha256": digestBytes(f.packet), "run_id": "fixture-run", "client_sha256": quickApprovedManualClient, "acknowledged_at": "2026-11-11T10:03:00Z", "items": inspected, "attempt_sha256s": []string{text(result["sha256"])}, "exposure_urls": urls}
	f.binding = map[string]any{"schema": "quick-author-cache-binding-v1", "operator": "agent:codex", "root": f.root, "baseline_source_sha256": f.base, "inventory_sha256": f.inventory, "packet_sha256": digestBytes(f.packet), "run_id": "fixture-run", "cache_root": "/scratch", "client": map[string]any{"path": "/scratch/client", "bytes": 1, "sha256": quickApprovedManualClient}, "author": "fixture author", "author_context": "/root/fixture_author", "created_at": "2026-11-11T10:04:00Z", "source_controls": nil, "first_receipt_journal": journalRef, "owner_refusals": denied, "attempts": []any{result}, "deliveries": deliveries, "inspection_ack": nil, "exposure_urls": urls}
	f.evidence = map[string]any{"schema": "quick-author-evidence-v2", "packet_sha256": digestBytes(f.packet), "items": map[string]any{"iq92_fixture": "source_backed"}, "receipts": receipts, "cache_binding": nil}
	f.seal = map[string]any{"schema": "quick-author-seal-v2", "author": "fixture author", "packet_sha256": digestBytes(f.packet), "evidence_sha256": "later", "cache_binding_sha256": "later", "sealed_at": "2026-11-11T10:05:00Z", "urls": urls}
	f.finish()
	return f
}
func TestQuickAuthorCacheV2FullExposureAndImmutableFirstRole(t *testing.T) {
	f := newCacheFixture(t)
	if err := f.check(); err != nil {
		t.Fatal(err)
	}
	if len(rows(f.evidence["receipts"])) != 13 || len(ids(object(f.boards[0])["sources"])) != 9 || object(rows(f.evidence["receipts"])[11])["fetched_by_role"] != "factual" {
		t.Fatal("fixture lost complete exposure or original first role")
	}
}
func TestQuickAuthorCacheV2Mutations(t *testing.T) {
	cases := map[string]func(*cacheFixture){
		"first-role-forgery": func(f *cacheFixture) {
			object(rows(f.evidence["receipts"])[11])["fetched_by_role"] = "author"
			f.finish()
		},
		"body-mismatch": func(f *cacheFixture) {
			f.inputs[text(object(rows(f.evidence["receipts"])[0])["capture_path"])] = []byte("mutated")
		},
		"stale-Root":                  func(f *cacheFixture) { f.root = "/other/root" },
		"stale-base":                  func(f *cacheFixture) { f.base = strings.Repeat("d", 64) },
		"stale-inventory":             func(f *cacheFixture) { f.inventory = strings.Repeat("d", 64) },
		"wrong-cache-root":            func(f *cacheFixture) { f.binding["cache_root"] = "/other/cache"; f.finish() },
		"stale-run":                   func(f *cacheFixture) { f.binding["run_id"] = "other-run"; f.finish() },
		"wrong-author":                func(f *cacheFixture) { f.seal["author"] = "other author" },
		"uncited-exposure-truncation": func(f *cacheFixture) { f.seal["urls"] = ids(f.seal["urls"])[:9] },
		"citation-missing": func(f *cacheFixture) {
			object(f.boards[0])["sources"] = []string{"https://ro.wikipedia.org/wiki/Absent"}
		},
		"receipt-missing":    func(f *cacheFixture) { f.evidence["receipts"] = rows(f.evidence["receipts"])[:12]; f.finish() },
		"inspection-missing": func(f *cacheFixture) { f.ack["items"] = rows(f.ack["items"])[:12]; f.finish() },
		"preinspection-seal": func(f *cacheFixture) { f.seal["sealed_at"] = "2026-11-11T10:02:00Z" },
		"equal-binding-seal": func(f *cacheFixture) { f.seal["sealed_at"] = f.binding["created_at"] },
		"delivery-after-inspection": func(f *cacheFixture) {
			object(rows(f.binding["deliveries"])[0])["observed_by"] = "2026-11-11T10:04:00Z"
			f.finish()
		},
		"invented-request-time": func(f *cacheFixture) {
			object(rows(f.binding["deliveries"])[0])["client_requested_at"] = "2026-11-11T09:59:00Z"
			f.finish()
		},
		"cache-hit-relabeled-new": func(f *cacheFixture) {
			object(rows(f.binding["deliveries"])[11])["delivery_kind"] = "new_response"
			f.finish()
		},
		"no-independent-pin": func(f *cacheFixture) { f.pin = QuickCachePin{} },
		"author-selfpin":     func(f *cacheFixture) { f.inputs[f.pin.Path] = []byte("self signed replacement") },
		"legacy-first-role": func(f *cacheFixture) {
			object(rows(f.evidence["receipts"])[0])["fetched_by_role"] = "legacy"
			f.finish()
		},
		"policy-first-role": func(f *cacheFixture) {
			object(rows(f.evidence["receipts"])[0])["fetched_by_role"] = "policy"
			f.finish()
		},
		"host-policy-denial": func(f *cacheFixture) {
			h := object(rows(f.controls["hosts"])[0])
			h["state"] = f.put("/scratch/ro.wikipedia.org.json", map[string]any{"denied": "current refusal"})
			f.finish()
		},
		"active-breaker": func(f *cacheFixture) {
			h := object(rows(f.controls["hosts"])[0])
			h["state"] = f.put("/scratch/ro.wikipedia.org.json", map[string]any{"breaker_until": json.Number("1999999999")})
			f.finish()
		},
		"stale-controls":              func(f *cacheFixture) { f.controls["checked_at"] = "2026-11-11T09:00:00Z"; f.finish() },
		"attempts-lineage-truncation": func(f *cacheFixture) { f.binding["attempts"] = []any{}; f.finish() },
	}
	for name, mutate := range cases {
		t.Run(name, func(t *testing.T) {
			f := newCacheFixture(t)
			mutate(f)
			if err := f.check(); err == nil {
				t.Fatal("mutation accepted")
			}
		})
	}
}
func TestQuickAuthorCacheRobotsOffline(t *testing.T) {
	for _, body := range []string{"User-agent: *\nDisallow: /wiki\n", "User-agent: GPTBot\nDisallow: /\n", "Content-Signal: ai-input=no\n"} {
		if cacheRobots([]byte(body), "/wiki/Fixture") == nil {
			t.Fatal("robots denial bypassed")
		}
	}
	if err := cacheRobots([]byte("User-agent: *\nDisallow: /\nAllow: /wiki/Fixture$\n"), "/wiki/Fixture"); err != nil {
		t.Fatal(err)
	}
}
func TestQuickAuthorCacheLoaderRejectsMissingPinAndRoleAlias(t *testing.T) {
	if _, _, err := cacheLoad("/fixture/root", QuickCachePin{}, func(map[string]any) ([]byte, error) { t.Fatal("read before pin"); return nil, nil }); err == nil {
		t.Fatal("missing Root pin accepted")
	}
	if cacheExternal("/fixture/root", "/fixture/root/author.json") == nil {
		t.Fatal("Root path accepted as external evidence")
	}
}

func TestQuickAuthorCacheMissingHistoricalStartRequiresRealFreshDelivery(t *testing.T) {
	f := newCacheFixture(t)
	oldRef := object(rows(f.binding["attempts"])[0])
	old, _ := cacheObject(f.inputs, oldRef)
	all := rows(old["captures"])
	first := object(clone(old))
	first["captures"] = all[:9]
	firstRef := f.put("/scratch/attempt-one", first)
	secondRows, thirdRows := []any{}, []any{}
	for i, v := range all[9:] {
		r := object(clone(v))
		delete(r, "started_at")
		delete(r, "stderr")
		r["error"] = ""
		if i < 2 {
			secondRows = append(secondRows, r)
		} else {
			thirdRows = append(thirdRows, r)
		}
	}
	secondRef := f.put("/scratch/attempt-two", map[string]any{"schema": "cat-m3-additional-actual-author-captures-1", "captures": secondRows, "no_source_approval_or_seal": true, "whole_original_URLset_and_first_roles_retained": true})
	thirdRef := f.put("/scratch/attempt-three", map[string]any{"schema": "cat-m3-final-bounded-author-captures-1", "captures": thirdRows, "original_URLsets_first_roles_and_all_prior_attempts_preserved": true, "source_approval": nil})
	f.binding["attempts"] = []any{firstRef, secondRef, thirdRef}
	hashes := []string{text(firstRef["sha256"]), text(secondRef["sha256"]), text(thirdRef["sha256"])}
	// Explicit fresh Root cache handoff. No historical timestamp is synthesized.
	for i, v := range rows(f.binding["deliveries"]) {
		d := object(v)
		ref, index := firstRef, i
		if i >= 11 {
			ref, index = thirdRef, i-11
		} else if i >= 9 {
			ref, index = secondRef, i-9
		}
		d["attempt_sha256"], d["result_row"] = ref["sha256"], index
		d["delivery_kind"] = "cache_hit"
		d["requested_at"] = "2026-11-11T10:01:00Z"
		if i >= 9 {
			d["client_requested_at"] = nil
		}
	}
	// The lower-level typed validation does not infer omitted external inputs;
	// the native closure loader separately rejects the now-unused old file.
	delete(f.inputs, text(oldRef["path"]))
	for i := 0; i < len(hashes); i++ {
		for j := i + 1; j < len(hashes); j++ {
			if hashes[j] < hashes[i] {
				hashes[i], hashes[j] = hashes[j], hashes[i]
			}
		}
	}
	f.ack["attempt_sha256s"] = hashes
	f.finish()
	if err := f.check(); err != nil {
		t.Fatal(err)
	}
	object(rows(f.binding["deliveries"])[9])["client_requested_at"] = "2026-11-11T10:00:00Z"
	f.finish()
	if f.check() == nil {
		t.Fatal("invented missing historical start accepted")
	}
}

// Adapted unchanged assertions from independent native_review_test.go; synthetic tests only.
// Independent negative tests only. Synthetic fixture bytes are not Root, author,
// policy, content or admission evidence. Run only in Root's pinned native lane.
func TestQuickAuthorCacheRepairIndependentRobotsSplitlinesPolicy(t *testing.T) {
	for _, sep := range []string{"\r", "\v", "\f", "\u0085", "\u2028", "\u2029"} {
		t.Run(sep, func(t *testing.T) {
			body := "User-agent: *" + sep + "Disallow: /"
			if err := cacheRobots([]byte(body), "/wiki/Fixture"); err == nil {
				t.Fatalf("approved client's splitlines denial bypassed with separator %q", sep)
			}
		})
	}
}

func TestQuickAuthorCacheRepairIndependentOriginalRequestCannotBeAfterCurrentUse(t *testing.T) {
	f := newCacheFixture(t)
	oldRef := object(rows(f.binding["attempts"])[0])
	a, err := cacheObject(f.inputs, oldRef)
	if err != nil {
		t.Fatal(err)
	}
	a = object(clone(a))
	object(rows(a["captures"])[0])["started_at"] = "2027-11-11T10:00:00Z"
	ref := f.put("/scratch/attempt", a)
	for i, v := range rows(f.binding["deliveries"]) {
		d := object(v)
		d["attempt_sha256"] = ref["sha256"]
		if i == 0 {
			d["client_requested_at"] = "2027-11-11T10:00:00Z"
			d["delivery_kind"] = "cache_hit"
		}
	}
	f.binding["attempts"] = []any{ref}
	hashes := []string{text(ref["sha256"])}
	sort.Strings(hashes)
	f.ack["attempt_sha256s"] = hashes
	f.finish()
	if err := f.check(); err == nil {
		t.Fatal("original attempt in future of observed delivery, ack, binding and seal accepted")
	}
}

// Adapted unchanged assertions from independent native_policy_parity_test.go; synthetic tests only.
// Independent refusal-equivalence regressions. All values are synthetic;
// no usable Root, source policy, author, review or admission evidence is made.
func TestQuickAuthorCacheRepairIndependentPolicyUnicodeWhitespace(t *testing.T) {
	for _, space := range []string{"\u00a0", "\u1680", "\u2000", "\u2007", "\u202f", "\u205f", "\u3000"} {
		t.Run(space, func(t *testing.T) {
			signal := "ai-input" + space + "=" + space + "no"
			if err := cacheRobots([]byte("Content-Signal: "+signal+"\n"), "/wiki/Fixture"); err == nil {
				t.Fatalf("approved Python Unicode-space robots policy denial bypassed: %q", signal)
			}
		})
	}
}
func TestQuickAuthorCacheRepairIndependentReceiptPolicyUnicodeWhitespace(t *testing.T) {
	for _, space := range []string{"\u00a0", "\u1680", "\u2007", "\u202f", "\u205f", "\u3000"} {
		t.Run(space, func(t *testing.T) {
			signal := "ai-input" + space + "=" + space + "no"
			r := map[string]any{"url": "https://ro.wikipedia.org/wiki/Fixture", "sha256": strings.Repeat("a", 64), "status": 200, "bytes": 1, "fetched_by_role": "factual", "fetched_at": json.Number("1794300000"), "headers": map[string]any{"content-type": "text/plain", "content-signal": signal, "retry-after": ""}}
			if err := cacheRawReceipt(r); err == nil {
				t.Fatalf("approved Python Unicode-space original receipt policy denial bypassed: %q", signal)
			}
		})
	}
}
func TestQuickAuthorCacheRepairIndependentPolicyPythonTrimCharacters(t *testing.T) {
	for _, trim := range []string{"\x1c", "\x1d", "\x1e", "\x1f"} {
		t.Run(trim, func(t *testing.T) {
			if err := cacheRobots([]byte(trim+"Content-Signal: ai-input=no\n"), "/wiki/Fixture"); err == nil {
				t.Errorf("approved Python strip/splitlines policy denial bypassed: %q", trim)
			}
			if err := cacheRobots([]byte("User-agent: *"+trim+"\nDisallow: /\n"), "/wiki/Fixture"); err == nil {
				t.Errorf("approved Python strip wildcard denial bypassed: %q", trim)
			}
		})
	}
}
func TestQuickAuthorCacheRepairIndependentPolicyPythonIgnoreCaseSpecialI(t *testing.T) {
	for _, signal := range []string{"a\u0130-input=no", "a\u0131-input=no", "ai-\u0130nput=no", "ai-\u0131nput=no", "ai-tra\u0130n=no", "ai-tra\u0131n=no"} {
		t.Run(signal, func(t *testing.T) {
			if err := cacheRobots([]byte("Content-Signal: "+signal+"\n"), "/wiki/Fixture"); err == nil {
				t.Fatalf("approved Python ignore-case robots policy denial bypassed: %q", signal)
			}
		})
	}
}
func TestQuickAuthorCacheRepairIndependentReceiptPolicyPythonIgnoreCaseSpecialI(t *testing.T) {
	for _, signal := range []string{"a\u0130-input=no", "a\u0131-input=no", "ai-\u0130nput=no", "ai-\u0131nput=no", "ai-tra\u0130n=no", "ai-tra\u0131n=no"} {
		t.Run(signal, func(t *testing.T) {
			r := map[string]any{"url": "https://ro.wikipedia.org/wiki/Fixture", "sha256": strings.Repeat("a", 64), "status": 200, "bytes": 1, "fetched_by_role": "factual", "fetched_at": json.Number("1794300000"), "headers": map[string]any{"content-type": "text/plain", "content-signal": signal, "retry-after": ""}}
			if err := cacheRawReceipt(r); err == nil {
				t.Fatalf("approved Python ignore-case original receipt policy denial bypassed: %q", signal)
			}
		})
	}
}

func TestQuickAuthorCacheRepairPolicyAllPythonSeparators(t *testing.T) {
	for _, sep := range []string{"\n", "\r\n", "\r", "\v", "\f", "\x1c", "\x1d", "\x1e", "\u0085", "\u2028", "\u2029"} {
		t.Run(fmt.Sprintf("%q", sep), func(t *testing.T) {
			if err := cacheRobots([]byte("User-agent: *"+sep+"Disallow: /"), "/wiki/Fixture"); err == nil {
				t.Fatal("Python splitlines denial accepted")
			}
			if err := cacheRobots([]byte("User-agent: *"+sep+"Disallow: /private"+sep+"Allow: /wiki/Fixture$"), "/wiki/Fixture"); err != nil {
				t.Fatalf("positive longest allow rejected: %v", err)
			}
		})
	}
}
func TestQuickAuthorCacheRepairDottedIAgentCannotOverrideWildcard(t *testing.T) {
	for _, agent := range []string{"cat-de-roman-est\u0130-content-research", "cat-de-roman-est\u0131-content-research"} {
		body := "User-agent: " + agent + "\nAllow: /\nUser-agent: *\nDisallow: /\n"
		if err := cacheRobots([]byte(body), "/wiki/Fixture"); err == nil {
			t.Fatalf("nonmatching own agent bypasses wildcard: %q", agent)
		}
	}
	body := "User-agent: CAT-DE-ROMAN-ESTI-CONTENT-RESEARCH\nAllow: /\nUser-agent: *\nDisallow: /\n"
	if err := cacheRobots([]byte(body), "/wiki/Fixture"); err != nil {
		t.Fatalf("actual own-agent override rejected: %v", err)
	}
}
func TestQuickAuthorCacheRepairPolicySignalAllPythonWhitespaceAndPositive(t *testing.T) {
	spaces := []string{"\t", "\n", "\v", "\f", "\r", "\x1c", "\x1d", "\x1e", "\x1f", " ", "\u0085", "\u00a0", "\u1680", "\u2000", "\u2001", "\u2002", "\u2003", "\u2004", "\u2005", "\u2006", "\u2007", "\u2008", "\u2009", "\u200a", "\u2028", "\u2029", "\u202f", "\u205f", "\u3000"}
	for _, space := range spaces {
		for _, key := range []string{"ai-input", "ai-train", "AI-INPUT", "AI-TRAIN"} {
			signal := key + space + "=" + space + "no"
			if !cachePolicySignalDenied(signal) {
				t.Fatalf("policy whitespace bypass: %q", signal)
			}
		}
	}
	for _, signal := range []string{"", "ai-input=yes", "ai-train=yes", "ai-input=none", "ai-input=nope", "ai-search=no", "ai-input\u200b=no"} {
		if cachePolicySignalDenied(signal) {
			t.Fatalf("positive signal rejected: %q", signal)
		}
	}
}

// Update only the original immutable synthetic result and its actual references.
// No first receipt, source body or real author event is changed.
func cacheRepairReplaceAttempt(t *testing.T, f *cacheFixture, mutate func(map[string]any)) {
	t.Helper()
	oldRef := object(rows(f.binding["attempts"])[0])
	a, err := cacheObject(f.inputs, oldRef)
	if err != nil {
		t.Fatal(err)
	}
	a = object(clone(a))
	mutate(a)
	ref := f.put("/scratch/attempt", a)
	f.binding["attempts"] = []any{ref}
	for _, v := range rows(f.binding["deliveries"]) {
		object(v)["attempt_sha256"] = ref["sha256"]
	}
	f.ack["attempt_sha256s"] = []string{text(ref["sha256"])}
	f.finish()
}
func TestQuickAuthorCacheRepairOriginalChronology(t *testing.T) {
	for _, started := range []string{"2026-11-11T10:00:01Z", "2026-11-11T10:01:01Z", "2026-11-11T10:03:01Z", "2026-11-11T10:04:01Z", "2026-11-11T10:05:01Z", "2027-11-11T10:00:00Z"} {
		t.Run(started, func(t *testing.T) {
			f := newCacheFixture(t)
			object(rows(f.binding["deliveries"])[0])["delivery_kind"] = "cache_hit"
			object(rows(f.binding["deliveries"])[0])["client_requested_at"] = started
			cacheRepairReplaceAttempt(t, f, func(a map[string]any) { object(rows(a["captures"])[0])["started_at"] = started })
			if err := f.check(); err == nil {
				t.Fatal("selected original request after current event accepted")
			}
		})
	}
	for _, started := range []string{"2026-11-11T09:59:00Z", "2026-11-11T10:00:00Z"} {
		f := newCacheFixture(t)
		d := object(rows(f.binding["deliveries"])[0])
		d["delivery_kind"] = "cache_hit"
		d["client_requested_at"] = started
		cacheRepairReplaceAttempt(t, f, func(a map[string]any) { object(rows(a["captures"])[0])["started_at"] = started })
		if err := f.check(); err != nil {
			t.Fatalf("older/equal original start rejected: %s: %v", started, err)
		}
	}
}
func TestQuickAuthorCacheRepairUnselectedLinkedFutureRequest(t *testing.T) {
	for _, started := range []string{"2026-11-11T10:01:01Z", "2027-11-11T10:00:00Z"} {
		f := newCacheFixture(t)
		cacheRepairReplaceAttempt(t, f, func(a map[string]any) {
			extra := object(clone(rows(a["captures"])[0]))
			extra["started_at"] = started
			a["captures"] = append(rows(a["captures"]), extra)
		})
		if err := f.check(); err == nil {
			t.Fatalf("unselected linked future request accepted: %s", started)
		}
	}
}
func TestQuickAuthorCacheRepairRobotsReceiptSignalVariants(t *testing.T) {
	for _, signal := range []string{"ai-input\u00a0=\u00a0no", "a\u0130-input=no", "ai-tra\u0131n=no", "ai-input\x1f=\x1fno"} {
		f := newCacheFixture(t)
		h := object(rows(f.controls["hosts"])[0])
		r, err := cacheObject(f.inputs, h["robots_receipt"])
		if err != nil {
			t.Fatal(err)
		}
		r = object(clone(r))
		object(r["headers"])["content-signal"] = signal
		h["robots_receipt"] = f.put(text(object(h["robots_receipt"])["path"]), r)
		f.finish()
		if err := f.check(); err == nil {
			t.Fatalf("robots receipt policy bypass: %q", signal)
		}
	}
}
