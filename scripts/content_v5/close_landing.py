#!/usr/bin/env python3
"""Prepare the receipt-only commit after an exact local V5 fast-forward.

Threat model: the root orchestrator owns the repo, evidence directory and
input manifest. This script independently binds those bytes and local Git
state, validates registry transitions and applies no Git ref changes. It
does not replace exact gates, the human/independent GO, or HTTP play.
"""

import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import subprocess
import sys

sys.dont_write_bytecode = True
V5 = Path(__file__).resolve().parent
SCRIPTS = V5.parent
sys.path.insert(0, str(V5))
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "landing"))
from content_file_transaction import atomic_write, restore_files
from content_registry import current_rows, encode as registry_encode, read_journal
from support import clean_source, exact_commit, git, read_artifact, read_json, require
from kgdiff import committed_delta
import link_install
from play import scope as pack_play_scope

REGISTRY = "docs/content-registry/registry.jsonl"
STATUS = "docs/STATUS.md"
QUEUE = "docs/content-registry/LANDING_QUEUE.md"
MAX_EVIDENCE = 50 * 1024 * 1024
PARITY_CASES_BY_RULES = {1: 1206, 2: 1332}
UNIT_CHECKS = {"cat-unit-frontend-build", "cat-frontend-unit", "cat-frontend-lint",
               "cat-frontend-types", "cat-backend-race", "cat-backend-vet",
               "cat-authcore-race", "cat-authcore-vet", "cat-route-budgets"}
FULL_CHECKS = UNIT_CHECKS | {"cat-full-build-cat-server", "cat-full-build-cat-browser-plan",
                             "cat-pg-accounts", "cat-pg-httpapi", "cat-http-parity",
                             "cat-legacy-owner-journey", "cat-browser-full",
                             "csp-measurement", "app-image-evidence", "browser-evidence"}
BUILD_CHECKS = {"cat-build-fresh-build-output", "cat-build-frontend-build",
                "cat-build-emitted-inventory", "cat-build-assets", "cat-build-gui-identity",
                "cat-build-build-cat-server", "cat-build-build-cat-browser-plan"}
CHECKS_4I = {"01-rails", "02-validate", "03-export", "04-ops", "05-mobile",
             "06-race", "07-vet", "08-auth", "09-doc", "10-diff"}
TRAIN = re.compile(r"[a-z0-9][a-z0-9-]{0,63}")
SHA256 = re.compile(r"[a-f0-9]{64}")
BUNDLE = "go-backend/internal/content/bundled.json"
BOARD_GAMES = {"alchimie", "conexiuni", "contexto", "intrusul", "lant", "perechi"}
WORD_REVIEW_FIELDS = ("v5_word_review_binding", "v5_derived_view_sha256", "v5_independence_checks")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2,
                       allow_nan=False) + "\n").encode("utf-8")


def parse_time(value):
    require(isinstance(value, str), "Landing time must be an ISO timestamp")
    when = datetime.fromisoformat(value.replace("Z", "+00:00"))
    require(when.utcoffset() == timezone.utc.utcoffset(None), "Landing time must be in UTC")
    require(when <= datetime.now(timezone.utc), "Landing time is in the future")
    return when


def read_receipts(scratch, manifests, candidate, base, gui, lock, lock_sha):
    common = {"assembly", "build", "4i", "reference", "pin-review", "http-play", "landing-review"}
    required = common | ({"unit", "full", "unit-wrapper", "full-wrapper", "full-supervisor"} if gui else set())
    require(isinstance(manifests, dict) and set(manifests) == required, "Receipt set differs")
    found = {}
    documents = {}
    total = 0
    for role, ref in sorted(manifests.items()):
        require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, f"Bad {role} receipt reference")
        require(isinstance(ref["sha256"], str) and SHA256.fullmatch(ref["sha256"]), "Invalid receipt digest")
        require(ref["path"] not in {item["path"] for item in found.values()}, "Reused receipt path")
        raw = read_artifact(scratch, ref["path"], MAX_EVIDENCE - total)
        require(raw and sha256(raw) == ref["sha256"], f"Changed {role} receipt")
        data = read_json(raw)
        documents[role] = data
        require(data.get("sha") == candidate, f"{role} receipt has wrong candidate SHA")
        if role == "landing-review":
            require(data.get("verdict") == "GO" and isinstance(data.get("thread_id"), str)
                    and data["thread_id"], "Fresh landing GO required")
        elif role == "pin-review":
            require(data.get("verdict") == "GO" and isinstance(data.get("thread_id"), str)
                    and data["thread_id"], "Independent pin GO required")
        elif role not in {"unit-wrapper", "full-wrapper", "full-supervisor"}:
            require(data.get("status") == "pass", f"{role} receipt is not green")
        if role in {"build", "unit", "full"}:
            require(data.get("schema") == 1 and data.get("target") == role and data.get("dirty") is False
                    and data.get("versions_lock_sha256") == lock_sha
                    and data.get("toolchain_digest") == lock["toolchain_image"]["image_id"]
                    and isinstance(data.get("checks"), list) and data["checks"]
                    and len({check.get("name") for check in data["checks"]}) == len(data["checks"])
                    and all(check.get("status") == "pass"
                            or (role == "unit" and check.get("status") == "skipped"
                                and check.get("reason") in {"no-dsn", "no-device"})
                            for check in data["checks"])
                    and isinstance(data.get("tree_sha256"), str) and SHA256.fullmatch(data["tree_sha256"]),
                    f"{role} receipt must be from the clean pinned gate")
        if role == "build":
            require(BUILD_CHECKS <= {check.get("name") for check in data["checks"]},
                    "Pinned build check roster differs")
        if role in {"unit", "full"}:
            expected_checks = UNIT_CHECKS if role == "unit" else FULL_CHECKS
            require(data.get("parallel") == 4 and expected_checks <= {check.get("name") for check in data["checks"]},
                    f"{role} check roster or parallelism differs")
        if role == "4i":
            require(data.get("baseline") == base and len(data["checks"]) == len(CHECKS_4I)
                    and {item.get("name") for item in data["checks"]} == CHECKS_4I
                    and all(type(item.get("exit_code")) is int and item["exit_code"] == 0
                            for item in data["checks"]), "4i checks or baseline differ")
        total += len(raw)
        found[role] = {**ref, "bytes": len(raw)}
    require(documents["pin-review"]["thread_id"] != documents["landing-review"]["thread_id"],
            "Landing and pin reviewers must be distinct")
    require(documents["4i"].get("build_receipt_sha256") == found["build"]["sha256"]
            and documents["4i"].get("source_tree_sha256") == documents["build"]["tree_sha256"],
            "4i does not bind the exact build receipt and tree")
    require(documents["landing-review"].get("assembly_sha256") == found["assembly"]["sha256"]
            and documents["landing-review"].get("http_play_sha256") == found["http-play"]["sha256"]
            and documents["landing-review"].get("reference_sha256") == found["reference"]["sha256"]
            and documents["landing-review"].get("pin_review_sha256") == found["pin-review"]["sha256"],
            "Landing review does not bind the exact assembly and HTTP play")
    require(documents["assembly"].get("baseline") == base
            and documents["http-play"].get("baseline") == base, "Assembly or HTTP play baseline differs")
    if gui:
        require(all(documents[role]["tree_sha256"] == documents["build"]["tree_sha256"]
                    for role in ("unit", "full")), "GUI receipt tree identities differ")
        for role, operator in (("unit", "agent:codex"), ("full", None)):
            wrapper = documents[f"{role}-wrapper"]
            require(wrapper.get("schema") == 1 and wrapper.get("target") == role
                    and wrapper.get("tree_sha256") == documents[role]["tree_sha256"]
                    and wrapper.get("toolchain_digest") == documents[role]["toolchain_digest"]
                    and "operator" in wrapper and wrapper["operator"] == operator
                    and isinstance(wrapper.get("invocation"), str)
                    and re.fullmatch(r"[a-f0-9-]{36}", wrapper["invocation"]),
                    f"{role} owning wrapper differs")
        supervisor = documents["full-supervisor"]
        require(supervisor.get("schema") == 1
                and supervisor.get("wrapper_invocation") == documents["full-wrapper"]["invocation"]
                and supervisor.get("gate_exit") == supervisor.get("owner_exit") == 0
                and supervisor.get("errors") == [] and supervisor.get("cleanup", {}).get("verified") is True,
                "Full supervisor or owner cleanup did not pass")
    return found, documents


def evidence_file(scratch, ref, limit):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "Invalid evidence reference")
    raw = read_artifact(scratch, ref["path"], limit)
    require(sha256(raw) == ref["sha256"], f"Evidence digest differs for {ref['path']}")
    return raw


class Evidence:
    def __init__(self, scratch, initial):
        self.scratch = scratch
        self.attachments = dict(initial)
        self.paths = {item["path"]: item for item in initial.values()}
        self.used = sum(item["bytes"] for item in initial.values())

    def add(self, name, ref, limit=MAX_EVIDENCE, *, shared=False):
        require(isinstance(ref, dict) and ref.keys() == {"path", "sha256"}, "Invalid evidence reference")
        prior = self.paths.get(ref["path"])
        if prior and shared:
            require(prior["sha256"] == ref["sha256"], "Conflicting digest for shared closeout evidence")
            return evidence_file(self.scratch, ref, min(limit, prior["bytes"]))
        require(name not in self.attachments and prior is None, "Evidence file reused across closeout roles")
        raw = evidence_file(self.scratch, ref, min(limit, MAX_EVIDENCE - self.used))
        entry = {**ref, "bytes": len(raw)}
        self.attachments[name] = self.paths[ref["path"]] = entry
        self.used += len(raw)
        return raw


def check_reference(repo, candidate, bundle, evidence, documents):
    reference = documents["reference"]
    pin_review = documents["pin-review"]
    attachment = evidence.add

    corpus_raw = attachment("reference-corpus", reference["corpus"])
    corpus_digest = sha256(corpus_raw)
    if corpus_raw.startswith(b"\x1f\x8b"):
        with gzip.GzipFile(fileobj=io.BytesIO(corpus_raw)) as archive:
            corpus_raw = archive.read(MAX_EVIDENCE + 1)
        require(len(corpus_raw) <= MAX_EVIDENCE, "Reference corpus exceeds decompression bound")
    corpus = read_json(corpus_raw)
    rules = corpus.get("rules_version", 1)
    require(type(rules) is int and rules in PARITY_CASES_BY_RULES, "Unknown HTTP parity rules version")
    case_count = PARITY_CASES_BY_RULES[rules]
    require(reference.get("case_count") == case_count and pin_review.get("case_count") == case_count,
            "Reference and pin review counts must match the rules version")
    capture = read_json(attachment("reference-capture", reference["capture"]))
    replay = read_json(attachment("reference-replay", reference["replay"]))
    pins = read_json(attachment("pin-changes", pin_review["changes"]))
    attachment("http-transcript", documents["http-play"]["transcript"])
    require(corpus.get("schema_version") == 1 and isinstance(corpus["cases"], list)
            and len(corpus["cases"]) == case_count
            and all(valid_case(case) for case in corpus["cases"])
            and isinstance(corpus.get("reference"), str) and corpus["reference"]
            and corpus.get("sources") == bundle["sources"], "Exact source-bound corpus required")
    require(capture.get("schema") == "cat-v5-independent-recapture-1"
            and capture.get("sha") == candidate and capture.get("case_count") == case_count
            and capture.get("corpus_sha256") == corpus_digest and capture.get("reference") == corpus["reference"]
            and reference.get("expectations_origin") == corpus["reference"]
            and reference.get("source_is_independent") is True, "Independent capture evidence differs")
    require(replay.get("schema") == "cat-v5-native-replay-1"
            and replay.get("sha") == candidate and replay.get("corpus_sha256") == corpus_digest,
            "Native replay receipt did not use the independent corpus")
    report = replay["report"]
    require(report.get("ok") is True and report.get("mode") in {"golden_replay", "independent_parity"}
            and report.get("requests") == case_count and report.get("rules_version", 1) == rules
            and report.get("reference") == corpus["reference"]
            and report.get("content_hash") == bundle["manifest"]["content_hash"],
            "Native reference replay differs")
    require(pin_review.get("reference_sha256") == evidence.attachments["reference"]["sha256"]
            and pin_review.get("corpus_sha256") == corpus_digest,
            "Pin review does not bind the exact independent reference")
    pin = exact_commit(repo, pin_review["pin_sha"])
    previous = git(repo, "rev-parse", f"{pin}^").decode().strip()
    require(pin == candidate and previous != candidate
            and pins.get("before") == previous and pins.get("after") == pin
            and isinstance(pins.get("changes"), list) and pins["changes"], "Separate pin commit/list differs")
    changed = {name.decode("utf-8") for name in
               git(repo, "diff", "--name-only", "-z", previous, pin).split(b"\0") if name}
    rows = pins["changes"]
    require(pin_review["corpus_pin_path"] in changed
            and any(row["path"] == pin_review["corpus_pin_path"] and row["after_sha256"] == corpus_digest
                    for row in rows), "Pinned expectation file differs from captured corpus")
    require({row["path"] for row in rows} == changed and len(changed) == len(rows)
            and all(path.startswith(("tests/", "go-backend/internal/", "frontend/e2e/")) for path in changed),
            "Pin commit changed unexpected paths")
    for row in rows:
        path = row["path"]
        for label, sha in (("before_sha256", previous), ("after_sha256", pin)):
            listed = git(repo, "ls-tree", "--name-only", sha, "--", path).splitlines()
            actual = sha256(git(repo, "show", f"{sha}:{path}")) if path.encode() in listed else None
            require(row[label] == actual, f"Pin file digest differs for {path}")


def valid_case(case):
    if not isinstance(case, dict) or set(case) != {"request", "status", "body"}:
        return False
    request = case["request"]
    return (isinstance(request, dict) and isinstance(request.get("method"), str)
            and isinstance(request.get("path"), str) and request["path"].startswith("/")
            and isinstance(request.get("body"), str)
            and type(case["status"]) is int and 100 <= case["status"] <= 599)


def board_payload(game, installed):
    if game in {"intrusul", "perechi"}:
        return {**installed["payload"], "category": installed["category"],
                "difficulty": installed["difficulty"]}
    return {key: value for key, value in installed.items() if key not in {
        "id", "source", "status", "provenance",
    }}


def valid_seed(seed):
    return type(seed) is int and 0 <= seed < 10000


def reviewed_word_rows(registry, events, item_ids):
    predecessors = {row["id"]: row for row in events if row["id"] in item_ids and row["state"] == "reviewed"}
    result = dict(registry)
    for item in item_ids:
        row = registry[item]
        if row["state"] != "qualified":
            continue
        prior = predecessors.get(item)
        fields = ("frozen_payload", "reviews", "holds", *WORD_REVIEW_FIELDS)
        require(prior is not None and row["previous_sha256"] == sha256(registry_encode(prior).encode("utf-8"))
                and all(row.get(field) == prior.get(field) for field in fields)
                and all(row["checks"].get(field) == prior["checks"].get(field) for field in (
                    "v5_word_source_sha256", *WORD_REVIEW_FIELDS,
                )), f"Qualified word changed exact reviewed evidence for {item}")
        result[item] = prior
    return result


def word_artifacts(items, links, delta):
    words = {item["node"]["id"] for item in items}
    incident = [edge for edge in delta["edges"]["added"]
                if edge["src_id"] in words or edge["dst_id"] in words]
    actual = {link_install.link_key(edge): edge for edge in incident}
    require(len(actual) == len(incident) and actual.keys() == {link_install.link_key(edge) for edge in links},
            "Committed incident links differ from frozen word reviews")
    for edge in links:
        installed = actual[link_install.link_key(edge)]
        require(type(installed["is_distractor"]) is int and type(installed["bidirectional"]) is int
                and installed == {**edge, "id": installed["id"], "is_distractor": 0,
                                  "bidirectional": int(edge["bidirectional"])},
                "Committed incident link fields differ from frozen word review")
    nodes = {row["id"]: row for row in delta["concepts"]["added"]}
    expected = {}
    for item in items:
        node = item["node"]
        edge_ids = sorted(actual[link_install.link_key(edge)]["id"] for edge in item["links"])
        require(nodes.get(node["id"]) == {**node, "degree": len(edge_ids),
                                         "difficulty_tier": link_install.tier_for_salience(node["salience"])},
                f"Committed node differs from frozen word review for {item['id']}")
        expected[item["id"]] = {"node_id": node["id"], "edge_ids": edge_ids}
    return expected


def actual_play_text(value):
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, (dict, list)):
        return any(actual_play_text(item) for item in (value.values() if isinstance(value, dict) else value))
    return False


def word_board_scope(evidence, assembly, before_bundle_sha, bundle_sha, other_roles):
    diff_ref = assembly["board_view_diff"]
    diff = read_json(evidence.add("board-view-diff", diff_ref, 8 * 1024 * 1024))
    require(diff.get("schema") == "cat-board-view-diff-1" and "one_word_dry_run" not in diff
            and diff.get("baseline_bundle_sha256") == before_bundle_sha
            and diff.get("candidate_bundle_sha256") == bundle_sha
            and isinstance(diff.get("games"), dict) and diff["games"].keys() == BOARD_GAMES
            and isinstance(diff.get("disturbed"), list)
            and type(diff.get("disturbed_total")) is int and diff["disturbed_total"] == len(diff["disturbed"]),
            "Exact full word-train board-view diff required")
    views = {}
    for row in diff["disturbed"]:
        require(row["game"] in BOARD_GAMES and isinstance(row["id"], str) and row["id"]
                and row["kind"] == "changed"
                and SHA256.fullmatch(row.get("before_sha256", "")) and SHA256.fullmatch(row.get("after_sha256", ""))
                and row["before_sha256"] != row["after_sha256"],
                "Disturbed board must have a playable changed view")
        key = (row["game"], row["id"])
        require(key not in views, "Duplicate disturbed board")
        views[key] = row["after_sha256"]
    require(all(type(row.get("disturbed")) is int and row["disturbed"] == sum(key[0] == game for key in views)
                for game, row in diff["games"].items()), "Board-view disturbance counts differ")
    if not views and "board_reblind" not in assembly:
        return views
    reblind = read_json(evidence.add("board-reblind", assembly["board_reblind"], 4 * 1024 * 1024))
    require(reblind.get("schema") == "cat-v5-board-reblind-1" and reblind.get("sha") == assembly["sha"]
            and reblind.get("board_view_diff_sha256") == diff_ref["sha256"]
            and isinstance(reblind.get("boards"), list), "Reblind receipt differs from exact word-train view diff")
    fields = ("game", "id", "view_sha256", "thread_id", "verdict")
    seen, transcript_hashes, play_hashes = set(), set(), set()
    for index, row in enumerate(reblind["boards"], 1):
        key = (row["game"], row["id"])
        thread = row["thread_id"]
        require(key in views and key not in seen and row["view_sha256"] == views[key]
                and link_install.text(thread, 128) and thread not in other_roles and row["verdict"] == "pass",
                "Independent reblind pass differs from exact disturbed board view")
        ref = row["transcript"]
        raw = evidence.add(f"board-reblind-transcript-{index}", ref)
        require(ref["sha256"] not in transcript_hashes, "Reused disturbed-board reblind transcript")
        transcript = read_json(raw)
        play = transcript.get("play")
        require(transcript.keys() == {*fields, "play"}
                and all(transcript[field] == row[field] for field in fields)
                and isinstance(play, list) and play and all(isinstance(step, dict) and step for step in play)
                and actual_play_text(play), "Disturbed-board reblind transcript lacks exact binding or play")
        play_sha = sha256(link_install.canonical(play))
        require(play_sha not in play_hashes, "Reused disturbed-board reblind play")
        seen.add(key)
        transcript_hashes.add(ref["sha256"])
        play_hashes.add(play_sha)
    require(seen == views.keys(), "Reblind evidence must cover every disturbed board")
    return views


def other_reblind_roles(evidence, documents, rows, judgments):
    threads = {documents[role]["thread_id"] for role in ("landing-review", "pin-review")}
    for index, row in enumerate(rows, 1):
        checks = row["checks"]
        word = judgments.get(row["id"])
        binding = word or row.get("v5_review_binding", {})
        author = checks.get("v5_author")
        authored_thread = author.get("thread_id") if isinstance(author, dict) else None
        threads.update(filter(None, (row.get("v5_author_thread"), authored_thread, binding.get("author_thread"))))
        threads.update(proof["thread_id"] for proof in row["reviews"]
                       if proof.get("role") in {"critic", "factual", "quality"} and proof.get("thread_id"))
        for blind in (row.get("v5_blind"), checks.get("v5_blind")):
            if isinstance(blind, dict) and blind.get("thread_id"):
                threads.add(blind["thread_id"])
        for role, ref in binding.get("reviews", {}).items():
            if role not in {"critic", "factual", "quality"}:
                continue
            proof = read_json(evidence.add(f"item-{index}-{role}-review", ref, link_install.MAX_INPUT,
                                           shared=word is None))
            threads.add(proof["thread_id"])
            if role == "critic" and word is not None:
                transcript = {"path": proof["transcript_path"], "sha256": proof["transcript_sha256"]}
                evidence.add(f"item-{index}-critic-transcript", transcript, link_install.MAX_INPUT)
        dump = binding.get("dump")
        if dump:
            evidence.add(f"item-{index}-dump-proposal", dump["proposal"], link_install.MAX_INPUT, shared=True)
            for role, ref in dump["transcriptions"].items():
                evidence.add(f"item-{index}-dump-{role}-transcription", ref, link_install.MAX_INPUT, shared=True)
            dump_gate = read_json(evidence.add(f"item-{index}-dump-parser-gate", dump["gate"],
                                              link_install.MAX_INPUT, shared=True))
            for name in ("historical", "fresh"):
                evidence.add(f"item-{index}-dump-parser-{name}", dump_gate[name],
                             link_install.MAX_INPUT, shared=True)
    return threads


def check_word_landing(repo, evidence, documents, delta, item_ids, registry, journal, base, candidate,
                       before_bundle_sha, bundle_sha):
    scratch = evidence.scratch
    assembly = documents["assembly"]
    word_ids = {item for item in item_ids if registry[item]["type"] == "concept"
                and "v5_word_source_sha256" in registry[item]["checks"]}
    if not word_ids:
        require(not ({"word_link_manifest", "board_view_diff", "board_reblind"} & assembly.keys()),
                "Word-train evidence requires a reviewed additive word")
        return {}, {}
    document = read_json(evidence.add("word-link-manifest", assembly["word_link_manifest"], link_install.MAX_INPUT))
    require(document.keys() == {"schema", "items", "gate", "claims", "judgments"}
            and document["schema"] == "cat-v5-link-install-1" and isinstance(document["items"], list)
            and len(document["items"]) == len(word_ids) <= 20
            and {item["id"] for item in document["items"]} == word_ids,
            "Word manifest must cover exactly the reviewed word items")
    items = document["items"]
    for index, item in enumerate(items, 1):
        row = registry[item["id"]]
        raw = link_install.canonical(item)
        require(row["checks"]["v5_word_source_sha256"] == sha256(raw)
                and evidence.add(f"word-{index}-frozen", row["frozen_payload"], link_install.MAX_INPUT) == raw,
                f"Frozen word evidence differs for {item['id']}")
    contract = read_json(read_artifact(scratch, "contract.json", 64 * 1024))
    require(contract.get("campaign") == "v5-pilot-2", "Expected the active Pilot 2 word contract")
    pilot_base = exact_commit(repo, contract["base_sha"])
    git(repo, "merge-base", "--is-ancestor", pilot_base, base)
    kg = git(repo, "--no-replace-objects", "show", f"{base}:{link_install.KG}")
    origin = read_json(git(repo, "--no-replace-objects", "show", f"{pilot_base}:{link_install.KG}"))
    key_for, excluded = link_install.native_label_authority(repo, kg, base)
    _, links = link_install.merge_input(items, read_json(kg), origin, key_for=key_for, excluded=excluded)
    artifacts = word_artifacts(items, links, delta)
    evidence.add("word-link-claims", document["claims"], link_install.MAX_INPUT)
    gate = read_json(evidence.add("word-parser-gate", document["gate"], link_install.MAX_INPUT))
    for name in ("historical", "fresh"):
        evidence.add(f"word-parser-{name}", gate[name], link_install.MAX_INPUT)
    events = (read_json(line) for line in journal.splitlines())
    reviewed = reviewed_word_rows(registry, events, word_ids)
    roles = other_reblind_roles(evidence, documents, (reviewed[item] for item in sorted(item_ids)),
                                document["judgments"])
    views = word_board_scope(evidence, assembly, before_bundle_sha, bundle_sha, roles)
    _, edge_results = link_install.verify_span_evidence(scratch, document["claims"], links)
    gate, bindings = link_install.verified_sources(scratch, document["gate"], repo, candidate, items)
    link_install.verify_registry(scratch, document, reviewed, bindings, gate, edge_results, False)
    return {item: {**artifact, "payload_sha256": registry[item]["checks"]["v5_word_source_sha256"]}
            for item, artifact in artifacts.items()}, views


def check_scope(scratch, documents, delta, item_ids, registry, bundle, words=None, views=None,
                legacy_puzzles_verified=False):
    assembly = documents["assembly"]
    expected_ids = sorted(item_ids)
    require(assembly.get("item_ids") == expected_ids
            and documents["landing-review"].get("item_ids") == expected_ids,
            "Manifest, exact assembly and landing review item sets differ")
    frozen = assembly["frozen_payload_sha256"]
    require(isinstance(frozen, dict) and set(frozen) == set(item_ids), "Assembly payload coverage differs")
    installed = assembly["installed"]
    require(isinstance(installed, dict) and set(installed) == set(item_ids), "Installed item coverage differs")
    added_aliases = {(row["id"], row["form"]) for row in delta["aliases"]["added"]}
    added_nodes = {row["id"]: row for row in delta["concepts"]["added"]}
    added_edges = {row["id"]: row for row in delta["edges"]["added"]}
    added_boards = {game: {row["id"]: row for row in diff["added"]} for game, diff in delta["boards"].items()}
    bound_aliases = set()
    bound_boards = set()
    bound_nodes = set()
    bound_edges = set()
    words = words or {}
    views = views or {}
    word_edges = {edge for artifact in words.values() for edge in artifact["edge_ids"]}
    for item in item_ids:
        row = registry.get(item)
        require(row is not None, f"Unknown registry ID {item}")
        word = words.get(item)
        expected_sha = word["payload_sha256"] if word else sha256(registry_encode(row["payload"]).encode("utf-8"))
        require(frozen[item] == expected_sha, f"Assembly differs from frozen registry payload for {item}")
        kind = row["type"]
        artifact = installed[item]
        if word:
            node = word["node_id"]
            require(artifact == {"node_id": node, "edge_ids": word["edge_ids"]} and node not in bound_nodes,
                    f"Installed word and incident link IDs differ for {item}")
            bound_nodes.add(node)
        elif kind in {"form", "synonym"}:
            owner = row["identity"]["owner_id"]
            forms = {(owner, form) for form in row["payload"]["forms"]}
            require(artifact == {"owner_id": owner} and forms and forms <= added_aliases
                    and not forms & bound_aliases, f"Installed aliases differ for {item}")
            bound_aliases.update(forms)
        elif kind.startswith("board."):
            game = kind.removeprefix("board.")
            board = artifact["board_id"]
            require(board in added_boards[game] and (game, board) not in bound_boards
                    and board_payload(game, added_boards[game][board]) == row["payload"],
                    f"Installed board payload differs for {item}")
            bound_boards.add((game, board))
        elif kind in {"concept", "name", "edge"}:
            records, bound, id_key = (added_edges, bound_edges, "edge_id") if kind == "edge" else (
                added_nodes, bound_nodes, "node_id"
            )
            ident = artifact[id_key]
            payload = row["payload"]
            required_fields = {"src_id", "dst_id", "relation"} if kind == "edge" else {
                "id", "label_ro", "node_type", "description", "category",
            }
            require(ident in records and ident not in bound
                    and (kind != "edge" or ident not in word_edges)
                    and required_fields <= payload.keys()
                    and all(records[ident].get(key) == value for key, value in payload.items()),
                    f"Installed {kind} payload differs for {item}")
            bound.add(ident)
        else:
            raise ValueError(f"Lane closeout adapter is missing for {kind}")
    require(not delta["aliases"].get("removed") and not delta["concepts"].get("removed")
            and not delta["edges"].get("removed") and not delta["edges"].get("changed")
            and all(set(row["fields"]) <= {"degree"} for row in delta["concepts"].get("changed", ()))
            and not any(diff["removed"] or diff["changed"] for diff in delta["boards"].values())
            and (legacy_puzzles_verified
                 or not any(delta.get("legacy_puzzles", {}).get(field) for field in ("added", "removed", "changed"))),
            "Committed removal or existing content rewrite is outside the reviewed train")
    require(bound_aliases == added_aliases, "Committed aliases are outside the reviewed train")
    require(bound_nodes == added_nodes.keys() and bound_edges | word_edges == added_edges.keys(),
            "Committed graph additions are outside the reviewed train")
    require(bound_boards == {(game, board) for game, ids in added_boards.items() for board in ids},
            "Committed boards are outside the reviewed train")

    pack_delta = {**delta, "boards": {game: diff for game, diff in delta["boards"].items()
                                     if game in {"conexiuni", "contexto", "lant", "alchimie"}}}
    touched_pairs = assembly["touched_boards"]
    require(isinstance(touched_pairs, list), "Invalid touched board list")
    for touched in touched_pairs:
        require(isinstance(touched, list) and len(touched) == 2
                and all(isinstance(field, str) for field in touched), "Invalid touched board")
    require(views.keys() <= {tuple(pair) for pair in touched_pairs},
            "Every disturbed board must be in exact HTTP play scope")
    pack_touched = [board for game, board in touched_pairs if game in pack_delta["boards"]]
    pack_boards, blocked, _ = pack_play_scope(pack_delta, bundle, pack_touched)
    require(not blocked, "Committed pack change contains an unplayable board")
    required_boards = {(row["game"], row["id"]) for row in pack_boards}
    required_boards.update((game, board) for game, board in bound_boards if game in {"intrusul", "perechi"})
    quick_ids = {(row["game"], row["catalog_id"]) for row in bundle.get("boards", [])}
    for game, board in touched_pairs:
        require((game, board) in required_boards or (game, board) in quick_ids,
                "Touched board identity is not in the serving export")
        required_boards.add((game, board))
    required_aliases = {(row["id"], row["form"]): row["label"] for row in delta["aliases"]["added"]}
    cald_targets = {}
    for row in bundle["pack_items"]:
        if row["game"] == "contexto" and row["pilot_eligible"] and row["status"] == "approved":
            cald_targets.setdefault(row["payload"]["target"], set()).add(row["id"])
    http = documents["http-play"]
    ref = http["transcript"]
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, "Invalid HTTP transcript reference")
    raw = read_artifact(scratch, ref["path"], 8 * 1024 * 1024)
    require(sha256(raw) == ref["sha256"], "HTTP transcript digest differs")
    rows = [read_json(line) for line in raw.splitlines()]
    require(len(rows) >= 2 and rows[0] == {
        "sha": http["sha"], "baseline": http["baseline"], "content_hash": bundle["manifest"]["content_hash"],
    }, "HTTP transcript candidate identity differs")
    boards, aliases = set(), set()
    for row in rows[1:-1]:
        require("error" not in row, "HTTP transcript contains a failed play")
        if "alias" in row:
            key = (row["id"], row["alias"])
            wins = row.get("wins")
            require(key in required_aliases and row.get("label") == required_aliases[key]
                    and valid_seed(row.get("repeat_seed")) and isinstance(wins, dict)
                    and set(wins) == cald_targets.get(row["id"], set())
                    and all(valid_seed(seed) for seed in wins.values()),
                    "HTTP alias repeat/win evidence differs")
            require(key not in aliases, "Duplicate HTTP alias evidence")
            aliases.add(key)
        else:
            require(row.get("won") is True and valid_seed(row.get("seed")), "HTTP board win missing")
            key = (row["game"], row["id"])
            require(key not in boards, "Duplicate HTTP board evidence")
            boards.add(key)
    require(boards == required_boards and aliases == required_aliases.keys(), "HTTP play scope differs from committed delta")
    require(rows[-1] == {"boards": len(boards), "aliases": len(aliases), "failures": 0},
            "HTTP transcript totals differ")


def transitions(prior, ids, receipt, candidate, at):
    rows = []
    require(set(ids) <= prior.keys(), "Unknown registry ID")
    for item_id in sorted(ids):
        old = prior[item_id]
        require(old["state"] in {"reviewed", "qualified"}, f"{item_id} is outside the reviewed pool")
        require(not old["holds"], f"{item_id} has a hold")
        group = old.get("co_landing_group")
        if group:
            required = {row["id"] for row in prior.values() if row.get("co_landing_group") == group}
            require(required <= set(ids), f"Partial co-landing group {group}")
        dependencies = old.get("dependencies", [])
        require(isinstance(dependencies, list) and all(isinstance(dep, str) for dep in dependencies),
                f"Unsupported dependencies for {item_id}")
        for dep in dependencies:
            require(dep in ids or (dep in prior and prior[dep]["state"] == "landed"),
                    f"Unlanded dependency {dep}")
        for state in (("qualified", "landed") if old["state"] == "reviewed" else ("landed",)):
            new = {**old, "event": "transition", "state": state, "recorded_at": at,
                   "previous_sha256": sha256(registry_encode(old).encode("utf-8")),
                   "v5_landing": {"candidate": candidate, "receipt": receipt}}
            rows.append(new)
            old = new
    return rows


def needs_gui(delta, before_bundle, after_bundle, changed):
    def recipes(bundle):
        return (
            bundle["discovery_world"]["recipes"],
            {board["id"]: board["additions"] for board in bundle["recipe_extensions"]["boards"]},
        )

    return (
        any(delta["edges"][field] for field in ("added", "removed", "changed"))
        or any(any(diff[field] for field in ("added", "removed", "changed"))
               or any((diff.get("eligibility") or {}).values()) for diff in delta["boards"].values())
        or before_bundle["lant_captions"] != after_bundle["lant_captions"]
        or recipes(before_bundle) != recipes(after_bundle)
        or any(path.startswith(b"frontend/e2e/") for path in changed)
    )


def expected(repo, scratch, manifest):
    require(set(manifest) == {"train_id", "baseline", "candidate", "landed_at", "item_ids",
                              "gui_gates", "evidence"}, "Unexpected closeout fields")
    train = manifest["train_id"]
    require(isinstance(train, str) and TRAIN.fullmatch(train), "Invalid train ID")
    base = exact_commit(repo, manifest["baseline"])
    candidate = exact_commit(repo, manifest["candidate"])
    require(base != candidate, "Candidate must advance main")
    clean_source(repo, candidate)
    require(git(repo, "symbolic-ref", "-q", "HEAD").strip() == b"refs/heads/main",
            "Run only from the clean local main after the fast-forward")
    require(git(repo, "reflog", "show", "-1", "--format=%gs", "refs/heads/main").strip()
            == f"merge {candidate}: Fast-forward".encode(), "Expected actual exact-SHA fast-forward")
    require(git(repo, "rev-parse", "refs/heads/main@{1}").decode().strip() == base,
            "Fast-forward predecessor differs")
    git(repo, "merge-base", "--is-ancestor", base, candidate)
    when = parse_time(manifest["landed_at"])
    logged = git(repo, "reflog", "show", "-1", "--format=%gD", "--date=iso-strict", "refs/heads/main")
    match = re.fullmatch(rb"refs/heads/main@\{([^}]+)\}", logged.strip())
    require(match is not None and abs((when - datetime.fromisoformat(match[1].decode())).total_seconds()) < 2,
            "Landing timestamp differs from the main reflog")
    when = datetime.fromisoformat(match[1].decode()).astimezone(timezone.utc)
    ids = manifest["item_ids"]
    require(isinstance(ids, list) and 0 < len(ids) <= 100
            and all(isinstance(item, str) and 0 < len(item) <= 200 and item.isprintable() for item in ids)
            and len(set(ids)) == len(ids), "Invalid landing item IDs")
    require(type(manifest["gui_gates"]) is bool, "gui_gates must be boolean")
    changed = git(repo, "diff", "--name-only", "-z", base, candidate).split(b"\0")
    delta = committed_delta(repo, base, candidate, include_neighbors=False)
    before_bundle_raw = git(repo, "show", f"{base}:{BUNDLE}")
    bundle_raw = git(repo, "show", f"{candidate}:{BUNDLE}")
    before_bundle = read_json(before_bundle_raw)
    bundle = read_json(bundle_raw)
    require(manifest["gui_gates"] or not needs_gui(delta, before_bundle, bundle, changed),
            "Changed board, edge or caption source requires GUI gates")
    lock_raw = git(repo, "show", f"{candidate}:versions.lock.json")
    receipts, documents = read_receipts(scratch, manifest["evidence"], candidate, base,
                                        manifest["gui_gates"], read_json(lock_raw), sha256(lock_raw))
    evidence = Evidence(scratch, receipts)
    journal = read_artifact(repo, REGISTRY)
    registry = current_rows(read_journal(repo / REGISTRY), repo)
    prior_journal = git(repo, "show", f"{base}:{REGISTRY}")
    require(prior_journal.endswith(b"\n") and journal.startswith(prior_journal),
            "Candidate rewrote the append-only registry")
    previous_rows = current_rows((read_json(line) for line in prior_journal.split(b"\n")[:-1]), repo)
    protected = {key: row for key, row in previous_rows.items()
                 if row["state"] in {"landed", "held_owner", "held_recorded"}}
    require(all(registry.get(key) == row for key, row in protected.items())
            and all(key in protected for key, row in registry.items() if row["state"] == "landed"),
            "Candidate changed protected registry state before closeout")
    require(set(ids) <= registry.keys(), "Unknown registry ID")
    words, views = check_word_landing(repo, evidence, documents, delta, ids, registry,
                                      journal, base, candidate, sha256(before_bundle_raw), sha256(bundle_raw))
    legacy_puzzles_verified = False
    if words and any(delta["legacy_puzzles"][field] for field in ("added", "removed", "changed")):
        kg = read_json(git(repo, "--no-replace-objects", "show", f"{candidate}:{link_install.KG}"))
        expected_puzzles = kg["kg_puzzles"]
        rebuilt = link_install.rebuild_document(kg, kg["kg_nodes"], kg["kg_edges"], "v5-closeout", "")
        require(expected_puzzles == read_json(rebuilt)["kg_puzzles"],
                "Committed legacy puzzles differ from exact graph regeneration")
        legacy_puzzles_verified = True
    check_scope(scratch, documents, delta, ids, registry, bundle, words, views, legacy_puzzles_verified)
    check_reference(repo, candidate, bundle, evidence, documents)
    train_dir = train if train.startswith("v5-") else f"v5-{train}"
    docs_path = f"reviews/{train_dir}/landing.json"
    path = f"docs/{docs_path}"
    receipt = json_bytes({
        "schema": "cat-v5-landing-1", "train_id": train, "actual_local_landed": True,
        "baseline": base, "candidate": candidate, "actual_landing_at": when.isoformat(),
        "prescribed_command": ["git", "merge", "--ff-only", candidate],
        "observed_reflog": f"merge {candidate}: Fast-forward", "operator": "agent:codex",
        "item_ids": sorted(ids), "gui_gates": manifest["gui_gates"], "evidence": evidence.attachments,
    })
    ref = {"path": path, "sha256": sha256(receipt), "bytes": len(receipt)}
    entries = transitions(registry, ids, ref, candidate, when.isoformat())
    current_rows((*read_journal(repo / REGISTRY), *entries), repo)
    updated = journal + b"".join((registry_encode(row) + "\n").encode("utf-8") for row in entries)
    status = read_artifact(repo, STATUS).decode("utf-8")
    lines = status.splitlines(keepends=True)
    require(len(lines) <= 120 and len(lines) >= 3 and lines[2].startswith("Last verified:"),
            "Unexpected STATUS layout")
    old = lines[2].rstrip("\r\n")
    headline = f"Last verified: {when.date().isoformat()} — V5 train `{train}` landed locally at `{candidate}`."
    link = f" [Landing receipt]({docs_path})."
    if " — V5 train " in old:
        previous = ""
    else:
        previous = f" Previous status: {old.removeprefix('Last verified: ')}"
    lines[2] = headline + link + previous + "\n"
    queue = read_artifact(repo, QUEUE)
    queue_entry = (
        f"\n## V5 train {train}\n\n"
        f"Local main advanced from `{base}` to `{candidate}` at {when.isoformat()} "
        f"with {len(ids)} items. [Landing receipt](../{docs_path}).\n"
    ).encode()
    return {REGISTRY: updated, STATUS: "".join(lines).encode("utf-8"),
            QUEUE: queue + queue_entry, path: receipt}


def write(repo, outputs, doc_checker):
    # Validate every existing target before making the first write. The caller
    # holds exclusive write ownership of main. Roll back owned writes on failure.
    saved = {name: read_artifact(repo, name) for name in (REGISTRY, STATUS, QUEUE)}
    receipt = next(name for name in outputs if name not in saved)
    path = repo / receipt
    require(path.parent.parent.resolve() == path.parent.parent and path.parent.parent.is_dir(),
            "Receipt parent must be a canonical tracked docs directory")
    require(not path.parent.is_symlink() and (not path.parent.exists() or path.parent.is_dir()),
            "Landing directory must be a real directory")
    require(not path.is_symlink() and not path.exists(), "Landing receipt already exists")
    created_parent = not path.parent.exists()
    if created_parent:
        path.parent.mkdir(mode=0o755)
    done = []
    try:
        for name, data in outputs.items():
            atomic_write(repo / name, data)
            done.append(name)
        git(repo, "diff", "--check")
        subprocess.run([str(doc_checker), "--root", str(repo), "--inventory", "docs/tracked-markdown.json"],
                       check=True, timeout=120, capture_output=True)
        current_rows(read_journal(repo / REGISTRY), repo)
        for name, data in outputs.items():
            require(read_artifact(repo, name) == data, f"Written bytes differ for {name}")
    except BaseException as original:
        try:
            restore_files({repo / name: saved[name] for name in done if name in saved})
        finally:
            try:
                path.unlink(missing_ok=True)
                if created_parent:
                    path.parent.rmdir()
            except OSError as cleanup:
                raise RuntimeError(f"Closeout failed: {original}; receipt cleanup also failed: {cleanup}") from original
        raise


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--manifest", required=True, help="Relative to campaign scratch")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--doc-checker", type=Path, help="Pinned native cat-doc-check executable")
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        scratch = args.scratch.absolute()
        require(scratch.is_dir() and scratch.resolve() == scratch
                and not scratch.is_relative_to(Path("/tmp")), "Canonical V5 scratch required")
        manifest = read_json(read_artifact(scratch, args.manifest, 64 * 1024))
        outputs = expected(repo, scratch, manifest)
        if args.write:
            require(args.doc_checker is not None and args.doc_checker.is_absolute()
                    and args.doc_checker.is_file(), "--write requires the pinned native doc checker")
            write(repo, outputs, args.doc_checker)
        print(json.dumps({"schema": "cat-v5-close-1", "written": args.write,
                          "files": {name: sha256(raw) for name, raw in outputs.items()}}, sort_keys=True))
    except (KeyError, TypeError, OSError, ValueError, RuntimeError, EOFError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"close landing: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
