#!/usr/bin/env python3
"""Generate both fixture mirrors from reviewed V5 input forms.

The operator supplies the exact screen executable and two independently
produced judgment envelopes from the private pool. Candidate JSON is data,
never code. Reviewer attestations bind a cached V5 response or a gated dump
revision and two independent raw-table transcriptions. The screen is rerun
on the actual checkout. The command writes
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
from types import ModuleType
import unicodedata
from urllib.parse import unquote
from xml.parsers.expat import ExpatError

sys.dont_write_bytecode = True
V5 = Path(__file__).resolve().parent
SCRIPTS = V5.parent
sys.path.insert(0, str(V5))
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "landing"))
from content_file_transaction import atomic_write, file_transaction
from content_registry import current_rows, dump_page_receipt
import dump_transcriptions
from support import clean_source, exact_commit, git, read_artifact, read_json, require

KG = "cat_de_roman_esti/fixtures/kg_sample.json"
MIRROR = "tests/fixtures/kg_sample.json"
REGISTRY = "docs/content-registry/registry.jsonl"
HEX = re.compile(r"[a-f0-9]{64}")
ROLE_NAMES = ("factual", "quality")
RO_WIKTIONARY = re.compile(r"https://ro\.wiktionary\.org/wiki/[^\s?#]+")
PARSER_PATH = "scripts/content_v5/wiktionary_dump.py"
COMPARATOR_PATH = "scripts/content_v5/check_cached_nouns.py"
ARCHIVE_KEYS = ("archive_url", "archive_sha256", "archive_receipt_sha256")
SAMPLE_KINDS = {
    "adjective": "adjective",
    "invariable-marked noun": "noun",
    "plural-only noun": "noun",
    "single table with two plurals": "noun",
    "ordinary noun": "noun",
}


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


def verified_json(scratch, ref, label):
    require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}, f"Invalid {label} reference")
    return dump_transcriptions.verified_document(scratch, ref["path"], ref["sha256"])


def archive_binding(source):
    return {key: source[key] for key in ARCHIVE_KEYS}


def replay_parser_gate(scratch, day, code_and_samples, historical, fresh):
    cache = scratch / "cache"
    require(cache.is_dir() and cache.resolve() == cache, "Canonical dump cache required")
    with tempfile.TemporaryDirectory(prefix="alias-gate-", dir=scratch) as name:
        staging = Path(name)
        for path, data in code_and_samples.items():
            (staging / path).write_bytes(data)
        command = [sys.executable, "-I", "-B", str(staging / Path(COMPARATOR_PATH).name), str(cache),
                   "--sample", str(staging / f"{day}-sample.json")]
        baseline = ["--cached-baseline", str(staging / f"{day}-cached.json")]
        for description, report, options in (("historical", historical, baseline), ("additional live", fresh, [])):
            replay = read_json(capture([*command, *options], f"Dump parser gate {description} replay"))
            require(replay.get("equal") is True and canonical(replay) == canonical(report),
                    f"Dump parser gate {description} replay differs from the reviewed comparison")


def reviewed_parser_gate(scratch, ref, repo, sha):
    require(repo is not None and sha is not None, "Exact checkout required for dump parser gate")
    gate = verified_json(scratch, ref, "parser gate")
    require(set(gate) == {"schema", "verdict", "reviewer_thread", "archive", "parser_sha256",
                          "comparator_sha256", "sample_sha256", "historical", "fresh"}
            and gate["schema"] == "cat-v5-wiktionary-parser-gate-1"
            and gate["verdict"] == "GO" and isinstance(gate["reviewer_thread"], str)
            and dump_transcriptions.THREAD.fullmatch(gate["reviewer_thread"]),
            "A reviewed GO receipt is required for the dump parser gate")
    archive = gate["archive"]
    require(isinstance(archive, dict) and set(archive) == set(ARCHIVE_KEYS)
            and isinstance(archive["archive_url"], str)
            and all(dump_transcriptions.valid_digest(value) for value in
                    (archive["archive_sha256"], archive["archive_receipt_sha256"], gate["sample_sha256"])),
            "Invalid parser gate archive binding")
    archive_match = dump_transcriptions.ARCHIVE_URL.fullmatch(archive["archive_url"])
    require(archive_match, "Expected a dated Romanian Wiktionary archive")
    day = archive_match[1]
    sample_path = f"scripts/content_v5/dump_samples/{day}"
    sample_raw = git(repo, "--no-replace-objects", "show", f"{sha}:{sample_path}-sample.json")
    baseline_raw = git(repo, "--no-replace-objects", "show", f"{sha}:{sample_path}-cached.json")
    sample = read_json(sample_raw)
    baseline = read_json(baseline_raw)
    baseline_sha = sha256(baseline_raw)
    require(sha256(sample_raw) == gate["sample_sha256"]
            and sample["archive_date"] == day and sample["archive_sha256"] == archive["archive_sha256"]
            and sample["cached_comparison_sha256"] == baseline_sha
            and baseline["archive"] == {**archive, "missing_titles": []},
            "Dump parser gate differs from the committed samples or their archive")
    fresh_rows = sample["pages"]
    past_rows = baseline["cached_comparison"]
    require(isinstance(fresh_rows, list) and len(fresh_rows) == 10, "Invalid additional live sample")
    require(isinstance(past_rows, list) and 14 <= len(past_rows) <= 64, "Invalid historical live sample")
    categories = [row["category"] for row in fresh_rows]
    require(all(category in SAMPLE_KINDS for category in categories)
            and all(categories.count(category) >= 2 for category in SAMPLE_KINDS if category != "ordinary noun"),
            "Dump parser gate sample lacks required categories")
    require(not {row["title"] for row in past_rows} & {row["title"] for row in fresh_rows}
            and not {row["dump_revision"] for row in past_rows} & {row["dump_revision"] for row in fresh_rows},
            "Additional live comparison repeats historical pages")

    historical = verified_json(scratch, gate["historical"], "historical comparison")
    fresh = verified_json(scratch, gate["fresh"], "additional live comparison")
    for report in (historical, fresh):
        require(report.get("equal") is True and report.get("archive") == {**archive, "missing_titles": []}
                and all(report.get(key) == gate[key] for key in
                        ("parser_sha256", "comparator_sha256", "sample_sha256")),
                "Dump parser gate has an unbound or failing comparison")

    parser_code = git(repo, "--no-replace-objects", "show", f"{sha}:{PARSER_PATH}")
    comparator_code = git(repo, "--no-replace-objects", "show", f"{sha}:{COMPARATOR_PATH}")
    require(sha256(parser_code) == digest(gate["parser_sha256"], "parser")
            and sha256(comparator_code) == digest(gate["comparator_sha256"], "comparator"),
            "Dump parser gate does not bind the exact committed parser and comparator")
    code_and_samples = {
        Path(PARSER_PATH).name: parser_code, Path(COMPARATOR_PATH).name: comparator_code,
        f"{day}-sample.json": sample_raw, f"{day}-cached.json": baseline_raw,
    }
    replay_parser_gate(scratch, day, code_and_samples, historical, fresh)
    # Execute the verified tracked bytes instead of importing a potentially stale .pyc.
    parser = ModuleType("wiktionary_dump")
    exec(compile(parser_code, str(repo / PARSER_PATH), "exec"), parser.__dict__)
    return gate, parser, day


def check_dump_proposal(scratch, dump, gate, proposal, item, row, view, review_threads):
    require(gate["reviewer_thread"] not in {*review_threads.values(), row["author_thread"]},
            "Parser gate reviewer must be distinct from the author and both S5 reviewers")
    require(proposal.get("item_id") == item["id"] and proposal.get("payload") == item
            and proposal.get("author_thread") == row["author_thread"]
            and proposal.get("payload_sha256") == row["payload_sha256"]
            and proposal.get("derived_view_sha256") == view
            and dump_transcriptions.valid_source(proposal.get("source"))
            and archive_binding(proposal["source"]) == gate["archive"],
            f"Dump proposal differs from the reviewed payload or parser gate for {item['id']}")
    require(set(dump["transcriptions"]) == set(ROLE_NAMES), "Exactly two S5 transcriptions are required")
    refs = [dump["proposal"], *(dump["transcriptions"][role] for role in ROLE_NAMES)]
    require(len({ref["path"] for ref in refs}) == 3, "Dump evidence requires distinct original artifacts")
    transcripts = [verified_json(scratch, dump["transcriptions"][role], f"{role} transcription")
                   for role in ROLE_NAMES]
    for role, transcript in zip(ROLE_NAMES, transcripts, strict=True):
        require(transcript.get("thread_id") == review_threads[role] and transcript.get("role") == role,
                f"Dump transcription does not bind the {role} S5 reviewer")
    report = dump_transcriptions.compare(proposal, transcripts)
    require(report["pass"] is True and report["forms"].keys() == set(item["forms"]),
            f"Independent dump transcriptions differ for {item['id']}")


def matches_dump_provenance(ref, binding):
    return (isinstance(ref, dict) and dump_page_receipt(ref)
            and all(ref.get(key) == value for key, value in binding.items())
            and ref.get("origin", "v5") == "v5"
            and isinstance(ref.get("scope", ""), str) and ref.get("scope") not in {"kg-only", "model", "legacy"}
            and type(ref.get("status", 200)) is int and ref.get("status", 200) == 200
            and ref.get("body_problem", "") == "" and "dump_failure" not in ref)


def verify_dump_pages(scratch, archive, parser, day, items):
    cache = scratch / "cache"
    require(cache.is_dir() and cache.resolve() == cache, "Canonical dump cache required")
    titles = list(dict.fromkeys(proposal["source"]["title"] for proposal, *_ in items))
    pages = {}
    for offset in range(0, len(titles), parser.MAX_TITLES):
        extracted = parser.extract(cache, day, titles[offset:offset + parser.MAX_TITLES],
                                   expected_archive_sha256=archive["archive_sha256"])
        require(archive_binding(extracted) == archive and not extracted["missing_titles"],
                "Extracted dump archive or exact titles differ from the reviewed gate")
        pages.update((page["title"], page) for page in extracted["pages"])
    receipt, receipt_sha = parser.archive_receipt(cache, day)
    require(receipt_sha == archive["archive_receipt_sha256"]
            and receipt.get("url") == archive["archive_url"] and receipt.get("sha256") == archive["archive_sha256"],
            "Verified dump archive receipt changed")
    fetcher = receipt.get("first_fetcher")
    require(receipt.get("fetched_by_role") == "script" and receipt.get("first_fetch_origin") == "v5"
            and isinstance(fetcher, str) and dump_transcriptions.THREAD.fullmatch(fetcher),
            "Dump archive lacks independent V5 script-fetch provenance")
    provenance_fields = {"first_fetcher": fetcher, "first_fetch_origin": "v5", "fetched_by_role": "script"}
    table_cells = {}
    for proposal, table_kind, provenance in items:
        source = proposal["source"]
        page = pages[source["title"]]
        require(page["revision_id"] == source["revision_id"]
                and page["text_sha256"] == source["text_sha256"]
                and sha256(page["wikitext"].encode("utf-8")) == source["text_sha256"],
                f"Raw dump page differs for {proposal['item_id']}")
        require(fetcher != proposal["author_thread"], "Dump archive first fetcher is the author")
        binding = {**source, **provenance_fields}
        require(any(matches_dump_provenance(ref, binding) for ref in provenance),
                f"Dump source differs from eligible reviewed registry provenance for {proposal['item_id']}")
        table = (source["title"], table_kind)
        if table not in table_cells:
            result = parser.parse_literal_table(source["title"], page["wikitext"], table_kind)
            table_cells[table] = set(result["forms"])
        require(dump_transcriptions.table_cells(proposal["proposed_cells"]) <= table_cells[table],
                f"Proposed cells differ from the gated parser for {proposal['item_id']}")


def acceptance(judgments, accepted, expected_input, scratch, registry, *, repo=None, sha=None):
    require(set(judgments) == {"schema", "input_sha256", "items"}
            and judgments["schema"] == "cat-v5-alias-judgments-1"
            and judgments["input_sha256"] == expected_input, "Judgments do not bind the candidate")
    require(set(judgments["items"]) == accepted.keys(), "Judgment item coverage differs")
    gates = {}
    dump_batches = {}
    dump_receipts = {}
    for item_id, row in judgments["items"].items():
        expected = accepted[item_id]
        roles = ROLE_NAMES if expected["kind"] == "form" else (*ROLE_NAMES, "critic")
        durable = registry[item_id]["v5_review_binding"]
        fields = {"author_thread", "payload_sha256", "reviews"}
        if "dump" in row:
            fields.add("dump")
        require(row == durable and set(row) == fields
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
        proposal = None
        if "dump" in row:
            dump = row["dump"]
            require(expected["kind"] == "form" and isinstance(dump, dict)
                    and set(dump) == {"gate", "proposal", "transcriptions", "table_kind"}
                    and dump["table_kind"] in {"noun", "adjective"}, f"Invalid dump form binding for {item_id}")
            ref = dump["gate"]
            require(isinstance(ref, dict) and set(ref) == {"path", "sha256"}
                    and isinstance(ref["path"], str), "Invalid parser gate reference")
            gate_key = (ref["path"], digest(ref["sha256"], "parser gate"))
            if gate_key not in gates:
                gates[gate_key] = reviewed_parser_gate(scratch, ref, repo, sha)
            gate, parser, day = gates[gate_key]
            proposal = verified_json(scratch, dump["proposal"], "dump proposal")

        threads = {row["author_thread"]}
        review_threads = {}
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
            review_threads[role] = thread
            if role == "critic":
                require(review.get("verdict") == "pass", f"Blind critic did not pass {item_id}")
                continue
            require(review.get("verdict") == "accept" and review.get("child_safe") is True,
                    f"{role} judgment did not accept {item_id}")
            sources = review["sources"]
            require(isinstance(sources, list), f"Invalid sources for {item_id}")
            if proposal is not None:
                citation = {"kind": "dump-inflection-table", "source": proposal.get("source"),
                            "table_kind": dump["table_kind"]}
                require(citation in sources, f"{role} does not cite the exact dump table for {item_id}")
                continue
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

        if proposal is not None:
            check_dump_proposal(scratch, dump, gate, proposal, frozen, row, view, review_threads)
            archive = gate["archive"]
            archive_key = tuple(archive[key] for key in ARCHIVE_KEYS)
            _, _, _, items = dump_batches.setdefault(archive_key, (archive, parser, day, []))
            items.append((proposal, dump["table_kind"], registry[item_id]["provenance"]))
            dump_receipts[item_id] = gate_key[1]
    for batch in dump_batches.values():
        verify_dump_pages(scratch, *batch)
    return dump_receipts


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
            dump_receipts = acceptance(judgments, selected, sha256(candidate), scratch, registry, repo=repo, sha=sha)
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
            **({"dump_parser_gate_sha256": dump_receipts} if dump_receipts else {}),
        }, ensure_ascii=True, sort_keys=True))
    except (KeyError, TypeError, OSError, ValueError, subprocess.SubprocessError, ExpatError) as exc:
        parser.exit(1, f"alias install: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
