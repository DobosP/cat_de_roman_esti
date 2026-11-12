package contentrails

import (
	"fmt"
	"strings"
	"time"
)

func bridgeBoundObject(files *quickBridgeFiles, sha any) (map[string]any, error) {
	for _, b := range files.blobs {
		if digestBytes(b) == sha {
			return pendingDecode(b, quickPendingMaxBytes)
		}
	}
	return nil, fmt.Errorf("quick bridge missing original bound author evidence")
}

func bridgeReceipts(evidence, pending map[string]any, files *quickBridgeFiles) (map[string]map[string]any, error) {
	if !pendingExact(evidence, "schema", "pending_sha256", "items", "receipts") || evidence["schema"] != "quick-review-evidence-v1" || evidence["pending_sha256"] != object(pending["_bridge"])["pending_sha256"] || !arrayShape(evidence["receipts"], 1, 8192) {
		return nil, fmt.Errorf("quick bridge review receipt manifest shape/pending")
	}
	modes := map[string]any{}
	for _, v := range rows(pending["boards"]) {
		modes[text(object(v)["id"])] = "source_backed"
	}
	if !same(modes, evidence["items"]) {
		return nil, fmt.Errorf("quick bridge receipt item coverage")
	}
	out := map[string]map[string]any{}
	for _, v := range rows(evidence["receipts"]) {
		r := object(v)
		u, err := bridgeURL(text(r["url"]))
		if err != nil || !pendingExact(r, "url", "capture_path", "capture_sha256", "bytes", "fetched_by_role", "fetched_at") || out[u] != nil || !authorityDigest(r["capture_sha256"]) || integer(r["bytes"]) < 1 || integer(r["bytes"]) > MaxBytes {
			return nil, fmt.Errorf("quick bridge first-fetch receipt shape/duplicate/byte bound")
		}
		if _, err = bridgeTime(r["fetched_at"]); err != nil {
			return nil, fmt.Errorf("quick bridge receipt zoned time")
		}
		role := text(r["fetched_by_role"])
		if role != "author" && role != "critic" && role != "factual" && role != "quality" {
			return nil, fmt.Errorf("quick bridge false/legacy first-fetch role")
		}
		if _, err = files.read(map[string]any{"path": r["capture_path"], "sha256": r["capture_sha256"], "bytes": r["bytes"]}); err != nil {
			return nil, err
		}
		out[u] = r
	}
	original, err := bridgeBoundObject(files, object(pending["bindings"])["author_evidence_sha256"])
	if err != nil {
		return nil, err
	}
	for _, v := range rows(original["receipts"]) {
		r := object(v)
		u, err := bridgeURL(text(r["url"]))
		if err != nil || !same(out[u], r) {
			return nil, fmt.Errorf("quick bridge author first-fetch receipt changed/omitted")
		}
	}
	return out, nil
}

// bridgeReviews validates assertions and bytes; source provenance and isolation
// are independently attested by the separately pinned operator replay receipt.
func bridgeReviews(pending map[string]any, dossiers map[string]map[string]any, material map[string]map[string]any, files *quickBridgeFiles) ([]any, map[string]string, error) {
	seal, err := bridgeBoundObject(files, object(pending["bindings"])["author_seal_sha256"])
	if err != nil {
		return nil, nil, err
	}
	author := text(seal["author"])
	sealed, err := bridgeTime(seal["sealed_at"])
	if err != nil {
		return nil, nil, err
	}
	release := material["author_release"]
	if !pendingExact(release, "schema", "author", "author_seal_sha256", "pending_sha256", "unsealed_at") || release["schema"] != "quick-review-release-v1" || release["author"] != author || release["author_seal_sha256"] != object(pending["bindings"])["author_seal_sha256"] || release["pending_sha256"] != object(pending["_bridge"])["pending_sha256"] {
		return nil, nil, fmt.Errorf("quick bridge author release/seal/pending binding")
	}
	unsealed, err := bridgeTime(release["unsealed_at"])
	if err != nil || !unsealed.After(sealed) {
		return nil, nil, fmt.Errorf("quick bridge source release chronology")
	}
	critic := material["critic_closure"]
	identities := map[string]string{"author": author, "critic": text(critic["reviewer"]), "factual": text(material["factual_envelope"]["reviewer"]), "quality": text(material["quality_envelope"]["reviewer"])}
	seen := map[string]bool{}
	for _, name := range identities {
		n := bridgeNorm(name)
		if n == "" || name != strings.TrimSpace(name) || seen[n] {
			return nil, nil, fmt.Errorf("quick bridge four fresh distinct fixed identities required")
		}
		seen[n] = true
	}
	times, latest := map[string]time.Time{}, sealed
	for _, role := range []string{"factual", "quality", "critic"} {
		env := material[role+"_envelope"]
		if role == "critic" {
			env = critic
		}
		signed, err := bridgeTime(env["signed_at"])
		if err != nil || !signed.After(sealed) || signed.After(unsealed) {
			return nil, nil, fmt.Errorf("quick bridge sealed/sign/release chronology")
		}
		times[role] = signed
		if signed.After(latest) {
			latest = signed
		}
	}
	for _, role := range []string{"factual", "quality"} {
		env := material[role+"_envelope"]
		if env["first_peer_read_at"] != nil {
			peer, err := bridgeTime(env["first_peer_read_at"])
			if err != nil || !peer.After(times["factual"]) || !peer.After(times["quality"]) {
				return nil, nil, fmt.Errorf("quick bridge peer read before both signatures")
			}
		}
	}
	if err = bridgeArtifacts(material["artifacts"], identities, files); err != nil {
		return nil, nil, err
	}
	receipts, err := bridgeReceipts(material["review_evidence"], pending, files)
	if err != nil {
		return nil, nil, err
	}
	authorURLs := map[string]bool{}
	for _, source := range ids(seal["urls"]) {
		u, err := bridgeURL(source)
		if err != nil {
			return nil, nil, err
		}
		authorURLs[u] = true
	}
	result, byRole := []any{}, map[string]map[string]map[string]any{}
	for _, role := range []string{"factual", "quality"} {
		env := material[role+"_envelope"]
		if !pendingExact(env, "schema", "role", "reviewer", "review_path", "review_sha256", "signed_at", "first_peer_read_at", "child_safe_by_item", "reviewer_chosen_sources") || env["schema"] != "quick-review-envelope-v1" || env["role"] != role {
			return nil, nil, fmt.Errorf("quick bridge raw envelope exact role/schema")
		}
		b, err := files.two(map[string]any{"path": env["review_path"], "sha256": env["review_sha256"]})
		if err != nil {
			return nil, nil, err
		}
		raw, err := pendingDecode(b, MaxBytes)
		if err != nil || !pendingExact(raw, "schema", "role", "reviewer", "pending_sha256", "rubric_sha256", "items") || raw["schema"] != "quick-raw-review-v1" || raw["role"] != role || raw["reviewer"] != identities[role] || raw["pending_sha256"] != object(pending["_bridge"])["pending_sha256"] || raw["rubric_sha256"] != object(pending["bindings"])["rubric_sha256"] || !arrayShape(raw["items"], len(dossiers), len(dossiers)) {
			return nil, nil, fmt.Errorf("quick bridge exact raw report role/identity/pending/rubric/coverage")
		}
		safety, choices := object(env["child_safe_by_item"]), object(env["reviewer_chosen_sources"])
		if len(safety) != len(dossiers) || len(choices) != len(dossiers) {
			return nil, nil, fmt.Errorf("quick bridge per-item safety/source coverage")
		}
		judged, rationaleCounts, duplicates := map[string]map[string]any{}, map[string]int{}, 0
		for _, v := range rows(raw["items"]) {
			r := object(v)
			id := text(r["id"])
			dossier := dossiers[id]
			if !pendingExact(r, "id", "review_binding", "record_sha256", "verdict", "rationale", "sources", "child_safe") || dossier == nil || judged[id] != nil || r["verdict"] != "accept" || r["child_safe"] != true || safety[id] != true || r["review_binding"] != dossier["review_binding"] || r["record_sha256"] != dossier["record_sha256"] || bridgeNorm(text(r["rationale"])) == "" {
				return nil, nil, fmt.Errorf("quick bridge hold/reject/unknown/duplicate/unsafe/stale raw item")
			}
			cited, err := bridgeSources(r["sources"])
			if err != nil {
				return nil, nil, err
			}
			for u := range cited {
				receipt := receipts[u]
				when, e := bridgeTime(receipt["fetched_at"])
				if receipt == nil || e != nil || when.After(times[role]) {
					return nil, nil, fmt.Errorf("quick bridge cited URL is an unfetched locator or post-sign capture")
				}
			}
			if !arrayShape(choices[id], 1, 32) {
				return nil, nil, fmt.Errorf("quick bridge independent reviewer source missing")
			}
			valid, chosenURLs := false, map[string]bool{}
			for _, choice := range rows(choices[id]) {
				c := object(choice)
				u, err := bridgeURL(text(c["url"]))
				receipt := receipts[u]
				if err != nil || !pendingExact(c, "url", "chosen_by", "fetched_by_role", "capture_path", "capture_sha256", "bytes", "fetched_at") || chosenURLs[u] || receipt == nil || c["chosen_by"] != identities[role] || !cited[u] {
					return nil, nil, fmt.Errorf("quick bridge reviewer-selected source identity/coverage")
				}
				chosenURLs[u] = true
				for _, key := range []string{"fetched_by_role", "capture_path", "capture_sha256", "bytes", "fetched_at"} {
					if !same(c[key], receipt[key]) {
						return nil, nil, fmt.Errorf("quick bridge false source first-fetch provenance")
					}
				}
				first := text(receipt["fetched_by_role"])
				when, _ := bridgeTime(receipt["fetched_at"])
				if !authorURLs[u] && (first == "factual" || first == "quality" || first == "critic") && !when.After(times[role]) {
					valid = true
				}
			}
			if !valid {
				return nil, nil, fmt.Errorf("quick bridge no fresh independently fetched reviewer-selected non-author URL")
			}
			rationale := bridgeNorm(text(r["rationale"]))
			if rationaleCounts[rationale] > 0 {
				duplicates++
			}
			rationaleCounts[rationale]++
			judged[id] = r
		}
		if len(judged) != len(dossiers) || duplicates*5 > len(dossiers) {
			return nil, nil, fmt.Errorf("quick bridge missing coverage or over 20 percent duplicated rationales")
		}
		byRole[role] = judged
		result = append(result, raw)
	}
	identical := 0
	for id := range dossiers {
		if bridgeNorm(text(byRole["factual"][id]["rationale"])) == bridgeNorm(text(byRole["quality"][id]["rationale"])) {
			identical++
		}
	}
	if identical*5 > len(dossiers) {
		return nil, nil, fmt.Errorf("quick bridge over 20 percent identical cross-pair rationales")
	}
	return result, identities, nil
}

func bridgeArtifacts(artifacts map[string]any, identities map[string]string, files *quickBridgeFiles) error {
	if !pendingExact(artifacts, "schema", "artifacts") || artifacts["schema"] != "quick-review-artifacts-v1" || !arrayShape(artifacts["artifacts"], 5, 5) {
		return fmt.Errorf("quick bridge exact M1-M5 inventory required")
	}
	stages, paths, digests := map[string]bool{}, map[string]bool{}, map[string]bool{}
	for _, v := range rows(artifacts["artifacts"]) {
		r := object(v)
		stage, path, sha := text(r["stage"]), text(r["path"]), text(r["sha256"])
		if !pendingExact(r, "stage", "path", "bytes", "sha256") || stage != "M1" && stage != "M2" && stage != "M3" && stage != "M4" && stage != "M5" || stages[stage] || paths[path] || digests[sha] {
			return fmt.Errorf("quick bridge reused/missing M1-M5 artifact")
		}
		b, err := files.read(map[string]any{"path": path, "sha256": sha, "bytes": r["bytes"]})
		if err != nil {
			return err
		}
		for _, role := range []string{"factual", "quality"} {
			if strings.Contains(bridgeNorm(path+" "+string(b)), bridgeNorm(identities[role])) {
				return fmt.Errorf("quick bridge reviewer-name leakage into M1-M5")
			}
		}
		stages[stage], paths[path], digests[sha] = true, true, true
	}
	return nil
}
