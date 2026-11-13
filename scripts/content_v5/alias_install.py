#!/usr/bin/env python3
"""Generate both fixture mirrors from reviewed V5 input forms.

The operator supplies the exact screen executable and two independently
produced judgment envelopes from the private pool. Candidate JSON is data,
never code. Reviewer attestations bind an archived V5 response and its cached
body. The screen is rerun on the actual checkout. The command writes
only the fixture mirrors in an explicitly requested clean content/v5
checkout, rolls back on failure and leaves export, audits and gates to S7–S9.
"""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unicodedata
from urllib.parse import unquote

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "landing"))
from content_file_transaction import atomic_write, file_transaction
from content_registry import current_rows
from support import clean_source, exact_commit, git, read_artifact, read_json, require

KG = "cat_de_roman_esti/fixtures/kg_sample.json"
MIRROR = "tests/fixtures/kg_sample.json"
REGISTRY = "docs/content-registry/registry.jsonl"
HEX = re.compile(r"[a-f0-9]{64}")
ROLE_NAMES = ("factual", "quality")
RO_WIKTIONARY = re.compile(r"https://ro\.wiktionary\.org/wiki/[^\s?#]+")


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def digest(value, label):
    require(isinstance(value, str) and HEX.fullmatch(value), f"Invalid {label} SHA-256")
    return value


def owned_file(root, name, limit):
    return read_artifact(root, name, limit)


def verified_binary(path, expected):
    path = path.absolute()
    raw = owned_file(path.parent, path.name, 64 * 1024 * 1024)
    require(sha256(raw) == digest(expected, "executable"), "Executable digest differs")
    return path


def capture(command, description):
    done = subprocess.run(command, capture_output=True, check=False, timeout=360)
    require(done.returncode == 0, f"{description} failed: {done.stderr.decode(errors='replace')[:1500]}")
    require(len(done.stdout) <= 8 * 1024 * 1024, f"{description} returned too much data")
    return done.stdout


def eligible_source(scratch, source, author):
    ref = source.get("receipt")
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"}:
        return False
    path = ref["path"]
    require(isinstance(path, str) and re.fullmatch(r"cache/[a-f0-9]{64}\.response\.json", path),
            "Source must bind an immutable V5 cache response")
    raw = owned_file(scratch, path, 512 * 1024)
    require(sha256(raw) == digest(ref["sha256"], "source receipt"), "Source receipt digest differs")
    receipt = read_json(raw)
    if (receipt.get("url") != source["url"] or receipt.get("origin") != "v5"
            or receipt.get("first_fetch_origin") != "v5" or receipt.get("status") != 200
            or receipt.get("body_problem") or receipt.get("fetched_by_role") not in {"script", "factual", "quality", "critic", "policy"}
            or not isinstance(receipt.get("first_fetcher"), str)
            or receipt["first_fetcher"] in {"", author}):
        return False
    body_sha = digest(receipt["sha256"], "source body")
    body = owned_file(scratch, f"cache/{body_sha}.body", 16 * 1024 * 1024)
    require(len(body) == receipt.get("bytes") and sha256(body) == body_sha, "Cached source body differs")
    return True


def lemma_key(text):
    require(isinstance(text, str) and text.strip(), "Expected a reviewed lexical lemma")
    return " ".join(unicodedata.normalize("NFC", text).replace("_", " ").split()).casefold()


def entry_key(url):
    match = RO_WIKTIONARY.fullmatch(url)
    require(match, "Expected Romanian Wiktionary entry URL")
    return lemma_key(unquote(url.removeprefix("https://ro.wiktionary.org/wiki/"), errors="strict"))


def acceptance(judgments, accepted, expected_input, scratch, registry):
    require(set(judgments) == {"schema", "input_sha256", "items"}
            and judgments["schema"] == "cat-v5-alias-judgments-1"
            and judgments["input_sha256"] == expected_input, "Judgments do not bind the candidate")
    require(set(judgments["items"]) == accepted.keys(), "Judgment item coverage differs")
    for item_id, row in judgments["items"].items():
        expected = accepted[item_id]
        roles = ROLE_NAMES if expected["kind"] == "form" else (*ROLE_NAMES, "critic")
        durable = registry[item_id]["v5_review_binding"]
        require(row == durable and set(row) == {"author_thread", "payload_sha256", "reviews"}
                and isinstance(row["author_thread"], str) and row["author_thread"],
                f"Judgment manifest differs from reviewed registry evidence for {item_id}")
        identity = registry[item_id]["identity"]
        require(isinstance(identity.get("sense"), str) and identity["sense"].strip(),
                f"Missing selected sense for {item_id}")
        expected_lemmas = {lemma_key(identity.get("lemma"))}
        if expected["kind"] == "synonym":
            expected_lemmas.add(lemma_key(identity.get("synonym_lemma")))
            require(len(expected_lemmas) == 2, f"Synonym lemmas are not distinct for {item_id}")
        frozen = {**expected, "identity": identity}
        require(row["payload_sha256"] == sha256(canonical(frozen)), f"Frozen payload differs for {item_id}")
        view = digest(registry[item_id]["v5_derived_view_sha256"], "derived view")
        require(registry[item_id]["v5_independence_checks"] == {
            "signed_reviews": True, "rationale_overlap_ok": True,
            "reviewer_identity_leaks_checked": True, "source_reuse_checked": True,
        }, f"S5 independence checks are incomplete for {item_id}")
        require(set(row["reviews"]) == set(roles), f"Missing independent evidence for {item_id}")
        threads = {row["author_thread"]}
        evidence_paths = set()
        for role in roles:
            ref = row["reviews"][role]
            require(set(ref) == {"path", "sha256"} and ref["path"] not in evidence_paths,
                    f"Invalid or reused evidence for {item_id}")
            evidence_paths.add(ref["path"])
            raw = owned_file(scratch, ref["path"], 128 * 1024)
            require(sha256(raw) == digest(ref["sha256"], "judgment"), "Judgment digest differs")
            review = read_json(raw)
            require(review.get("role") == role and review.get("item_id") == item_id
                    and review.get("payload_sha256") == row["payload_sha256"]
                    and review.get("derived_view_sha256") == view,
                    f"{role} judgment binding differs for {item_id}")
            thread = review["thread_id"]
            require(isinstance(thread, str) and thread and thread not in threads, "Review threads must be distinct")
            threads.add(thread)
            if role == "critic":
                require(review.get("verdict") == "pass", f"Blind critic did not pass {item_id}")
                continue
            require(review.get("verdict") == "accept" and review.get("child_safe") is True,
                    f"{role} judgment did not accept {item_id}")
            sources = review["sources"]
            require(isinstance(sources, list), f"Invalid sources for {item_id}")
            wiktionary = set()
            romanian = set()
            for source in sources:
                if not isinstance(source, dict) or not isinstance(source.get("url"), str):
                    continue
                url = source["url"]
                kind = source.get("kind")
                wiktionary_kind = "inflection-table" if expected["kind"] == "form" else "selected-sense"
                if kind == wiktionary_kind and RO_WIKTIONARY.fullmatch(url):
                    if eligible_source(scratch, source, row["author_thread"]):
                        wiktionary.add(entry_key(url))
                if kind == "second-romanian-source" and re.fullmatch(r"https://ro\.wikipedia\.org/wiki/[^\s?#]+", url):
                    if eligible_source(scratch, source, row["author_thread"]):
                        romanian.add(url)
            if expected["kind"] == "form":
                require(expected_lemmas <= wiktionary,
                        f"{role} lacks eligible Wiktionary evidence for {item_id}")
            else:
                require(expected_lemmas <= wiktionary and romanian and review.get("substitution_pass") is True,
                        f"{role} synonym evidence incomplete for {item_id}")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def selected_rows(screen, input_sha, kg_sha, binary_sha):
    require(screen.get("schema") == "cat-form-screen-result-1", "Unexpected form screen result")
    bindings = screen["bindings"]
    for name, expected in (("input", input_sha), ("kg", kg_sha), ("executable", binary_sha)):
        require(bindings[f"{name}_sha256"] == expected, f"Screen {name} binding differs")
    rows = screen["items"]
    require(isinstance(rows, list) and 0 < len(rows) <= 100, "Invalid form batch size")
    selected = {}
    for row in rows:
        require(row["state"] == "screened" and row["reason_code"] == "screened",
                f"Form batch contains a refused item: {row['id']}")
        require(row["id"] not in selected and row["kind"] in {"form", "synonym"}, "Invalid screened item")
        forms = row["accepted_forms"]
        require(isinstance(forms, list) and forms
                and all(isinstance(form, str) and form.strip() == form and form for form in forms),
                "Invalid accepted forms")
        selected[row["id"]] = {"id": row["id"], "kind": row["kind"], "owner_id": row["owner_id"], "forms": forms}
    require(sum(len(item["forms"]) for item in selected.values()) <= 100, "V5 forms train exceeds 100 forms")
    return selected


def require_reviewed_pool(registry, selected):
    for item_id, item in selected.items():
        row = registry.get(item_id)
        require(row is not None and row["state"] == "reviewed" and not row["holds"],
                f"Item is outside the unheld reviewed pool: {item_id}")
        require(row["type"] == item["kind"]
                and row["identity"].get("owner_id") == item["owner_id"]
                and row["payload"].get("node_id") in (None, item["owner_id"])
                and row["payload"].get("forms") == item["forms"],
                f"Reviewed registry payload differs for {item_id}")
        group = row.get("co_landing_group")
        if group:
            members = {member_id for member_id, member in registry.items()
                       if member.get("co_landing_group") == group}
            require(members <= selected.keys(), f"Partial reviewed co-landing group {group}")
        dependencies = row.get("dependencies", [])
        require(isinstance(dependencies, list) and all(isinstance(dep, str) for dep in dependencies),
                f"Invalid reviewed dependencies for {item_id}")
        for dep in dependencies:
            require(dep in selected or (dep in registry and registry[dep]["state"] == "landed"),
                    f"Unlanded reviewed dependency {dep}")


def generate(raw, selected):
    fixture = read_json(raw)
    owners = {node["id"]: node for node in fixture["kg_nodes"]}
    require(len(owners) == len(fixture["kg_nodes"]), "Duplicate node ID in fixture")
    seen = set()
    for item in selected.values():
        owner = item["owner_id"]
        require(owner in owners, f"Missing owner {owner}")
        node = owners[owner]
        aliases = node.setdefault("aliases", [])
        require(isinstance(aliases, list), f"Invalid alias list for {owner}")
        taken = {unicodedata.normalize("NFC", value).casefold() for value in [node["label_ro"], *aliases]}
        for form in item["forms"]:
            key = unicodedata.normalize("NFC", form).casefold()
            require(key not in taken and key not in seen, f"Duplicate accepted alias for {owner}")
            aliases.append(form)
            taken.add(key)
            seen.add(key)
    return (json.dumps(fixture, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode("utf-8")


def install_mirrors(repo, raw, fixture):
    lock = repo / ".cat-content-ops.lock"
    with lock.open("xb"):
        pass
    try:
        paths = [repo / KG, repo / MIRROR]
        with file_transaction(paths) as snapshots:
            require(all(before == raw for before in snapshots.values()), "Fixtures changed during assembly")
            for path in paths:
                atomic_write(path, fixture)
            require(all(path.read_bytes() == fixture for path in paths), "Generated mirrors differ")
    finally:
        lock.unlink()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path.cwd())
    parser.add_argument("--sha", required=True)
    parser.add_argument("--scratch", required=True, type=Path)
    parser.add_argument("--input", required=True, help="Candidate JSON relative to scratch")
    parser.add_argument("--judgments", required=True, help="Judgment manifest relative to scratch")
    parser.add_argument("--screen", required=True, type=Path)
    parser.add_argument("--screen-sha256", required=True)
    parser.add_argument("--cat-content", required=True, type=Path)
    parser.add_argument("--cat-content-sha256", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        sha = exact_commit(repo, args.sha)
        clean_source(repo, sha)
        require(git(repo, "symbolic-ref", "-q", "HEAD").strip() == b"refs/heads/content/v5",
                "Alias installation requires the content/v5 checkout")
        scratch = args.scratch.absolute()
        require(scratch.is_dir() and scratch.resolve() == scratch, "Canonical scratch required")
        raw = owned_file(repo, KG, 16 * 1024 * 1024)
        require(raw == owned_file(repo, MIRROR, 16 * 1024 * 1024), "Fixture mirrors differ")
        candidate = owned_file(scratch, args.input, 512 * 1024)
        judgments = read_json(owned_file(scratch, args.judgments, 512 * 1024))
        screen = verified_binary(args.screen, args.screen_sha256)
        validator = verified_binary(args.cat_content, args.cat_content_sha256)
        with tempfile.TemporaryDirectory(prefix="alias-install-", dir=scratch) as name:
            staging = Path(name)
            candidate_path = staging / "candidate.json"
            candidate_path.write_bytes(candidate)
            screen_raw = capture([str(screen), "--root", str(repo), "--input", str(candidate_path)], "Form screen")
            screen_receipt = read_json(screen_raw)
            selected = selected_rows(screen_receipt, sha256(candidate), sha256(raw), args.screen_sha256)
            registry_raw = owned_file(repo, REGISTRY, 64 * 1024 * 1024)
            require(screen_receipt["bindings"]["registry_sha256"] == sha256(registry_raw),
                    "Screen registry binding differs")
            require(registry_raw.endswith(b"\n"), "Registry journal has an incomplete tail")
            registry = current_rows((read_json(line) for line in registry_raw.split(b"\n")[:-1]), repo)
            require_reviewed_pool(registry, selected)
            acceptance(judgments, selected, sha256(candidate), scratch, registry)
            fixture = generate(raw, selected)
            staged = staging / "kg_sample.json"
            staged.write_bytes(fixture)
            capture([str(validator), "validate-fixture", "--root", str(repo), "--kg", str(staged)], "Native fixture validator")
        clean_source(repo, sha)
        if args.write:
            install_mirrors(repo, raw, fixture)
        print(json.dumps({
            "schema": "cat-v5-alias-install-1", "base": sha, "written": args.write,
            "candidate_sha256": sha256(candidate), "screen_result_sha256": sha256(screen_raw),
            "screen_executable_sha256": args.screen_sha256, "validator_executable_sha256": args.cat_content_sha256,
            "previous_kg_sha256": sha256(raw), "generated_kg_sha256": sha256(fixture),
            "items": selected,
        }, ensure_ascii=True, sort_keys=True))
    except (KeyError, TypeError, OSError, ValueError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"alias install: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
