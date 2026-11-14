#!/usr/bin/env python3
"""Build and replay the offline Pilot 2 forms collision probes."""

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from xml.parsers.expat import ExpatError

sys.dont_write_bytecode = True
V5 = Path(__file__).resolve().parent
sys.path[:0] = [str(V5), str(V5.parent / "landing")]
from alias_install import reviewed_parser_gate, verified_binary
from resolver_diff import read_bundle
from support import digest, exact_commit, git, read_artifact, read_json, require

PROFANITY = "scripts/content_v5/profanity-probes.json"
FREQ_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt"
FREQ_RECEIPT = "legacy-cache/2ceb8896f4828d4d2966ffde387ef33f9b12a517f56058ef4fe5ce63528bdc36.receipt.json"
FREQ_RECEIPT_SHA = "a9239dbee76db1263750199e632b32a310386a25b849d64f396964183acc97d3"
FREQ_BODY_SHA = "af4d7d1fc980ee7f988a5114dd34478dd5c7abd1e66a45c25a5da330f06faba5"
RESOLVER_DIFF = "scripts/content_v5/resolver_diff.py"
HEX = re.compile(r"[a-f0-9]{64}")
IDENTIFIER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,191}")
PROBE_TEXT = re.compile(r"[a-z]+(?:[ '-][a-z]+)*")
POTENTIAL_ROMANIAN = re.compile(r"^==[ \t]*(?:\{\{[ \t]*limba[ \t]*\|[ \t]*ro(?:n)?\b|român[ăa]\b)", re.I | re.M)
PARTS_OF_SPEECH = re.compile(
    r"\{\{[ \t]*(?:-[ \t]*)?(?:Format:[ \t]*)?(substantiv|adjectiv|verb)[ \t]*(?:-\s*ron\b|-\s*\|\s*ron\b)",
    re.I,
)
MAX_FORMS = 100
MAX_PROBE_INPUTS = 1000
MAX_ARTIFACT = 128 * 1024 * 1024
MAX_CORPUS = 64 * 1024 * 1024
MAX_CORPUS_ROWS = 2_000_000
CATEGORIES = {"sexual profanity", "scatological profanity", "severe vulgar abuse"}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, allow_nan=False, sort_keys=True,
                       separators=(",", ":")) + "\n").encode("utf-8")


def pinned(root, path, expected, limit=MAX_ARTIFACT):
    require(isinstance(expected, str) and HEX.fullmatch(expected), "Expected a lowercase SHA-256")
    data = read_artifact(root, path, limit)
    require(digest(data) == expected, f"SHA-256 differs for {path}")
    return data


def frequency_rows(raw):
    rows = {}
    for line in raw.decode("utf-8").splitlines():
        token, separator, count = line.rpartition(" ")
        require(token and separator and re.fullmatch(r"[1-9][0-9]*", count) and token not in rows,
                "Invalid or repeated FrequencyWords row")
        rows[token] = int(count)
    require(len(rows) == 50_000, "Expected the exact 50,000 FrequencyWords rows")
    return rows


def profanity_probes(raw, scratch):
    doc = read_json(raw)
    source = {"url": FREQ_URL, "receipt": FREQ_RECEIPT, "receipt_sha256": FREQ_RECEIPT_SHA,
              "body_sha256": FREQ_BODY_SHA}
    require(set(doc) == {"schema", "frequency_source", "seed", "supplement"}
            and doc["schema"] == "cat-v5-profanity-probes-1" and doc["frequency_source"] == source,
            "Invalid tracked profanity probe provenance")
    receipt = read_json(pinned(scratch, FREQ_RECEIPT, FREQ_RECEIPT_SHA, 512 * 1024))
    body = pinned(scratch, f"legacy-cache/{FREQ_BODY_SHA}.body", FREQ_BODY_SHA, 1024 * 1024)
    require(receipt.get("url") == FREQ_URL and receipt.get("sha256") == FREQ_BODY_SHA
            and receipt.get("status") == 200 and receipt.get("bytes") == len(body),
            "FrequencyWords receipt and body differ")
    frequencies = frequency_rows(body)
    probes, witnesses = [], []
    for key in ("seed", "supplement"):
        fields = {"probe", "category", "rows"} if key == "seed" else {"probe", "category"}
        group = doc[key]
        require(isinstance(group, list) and group, "Expected an explicit nonempty profanity probe group")
        group_keys = []
        for row in group:
            require(isinstance(row, dict), "Invalid tracked profanity probe entry")
            keyboard = key == "supplement" and set(row) == fields | {"usage"} and row["usage"] == "keyboard spelling"
            require((set(row) == fields or keyboard) and isinstance(row["probe"], str)
                    and PROBE_TEXT.fullmatch(row["probe"]) and row["category"] in CATEGORIES,
                    "Invalid tracked profanity probe entry")
            group_keys.append(row["probe"])
            if key == "seed":
                matches = row["rows"]
                require(isinstance(matches, list) and matches, "Seed probe lacks exact source rows")
                seen = set()
                for match in matches:
                    require(isinstance(match, dict) and set(match) == {"token", "count"}
                            and isinstance(match["token"], str) and type(match["count"]) is int
                            and frequencies.get(match["token"]) == match["count"] and match["token"] not in seen,
                            "Seed probe differs from its exact frequency row")
                    seen.add(match["token"])
                    witnesses.append({"probe": row["probe"], "token": match["token"]})
        require(group_keys == sorted(set(group_keys)), "Unsorted or repeated profanity probe entry")
        probes.extend(group_keys)
    require(len(probes) == len(set(probes)) < MAX_PROBE_INPUTS - MAX_FORMS, "Invalid profanity probe count")
    return sorted(probes), witnesses


def proposals(raw):
    doc = read_json(raw)
    require(set(doc) == {"schema", "items"} and doc["schema"] == "cat-v5-form-probe-input-1"
            and isinstance(doc["items"], list) and 0 < len(doc["items"]) <= MAX_FORMS,
            "Invalid form probe proposal packet")
    seen_ids = set()
    out = []
    for row in doc["items"]:
        require(isinstance(row, dict) and set(row) == {"id", "owner_id", "forms"}
                and all(isinstance(row[key], str) and IDENTIFIER.fullmatch(row[key]) for key in ("id", "owner_id"))
                and row["id"] not in seen_ids and isinstance(row["forms"], list) and row["forms"],
                "Invalid or repeated form probe proposal item")
        seen_ids.add(row["id"])
        surfaces = set()
        for surface in row["forms"]:
            require(isinstance(surface, str) and surface == surface.strip()
                    and 0 < len(surface.encode("utf-8")) <= 256
                    and all(ord(ch) >= 32 and ord(ch) != 127 for ch in surface) and surface not in surfaces,
                    "Invalid or repeated literal proposed form")
            surfaces.add(surface)
            out.append({"item_id": row["id"], "owner_id": row["owner_id"], "surface": surface})
    require(0 < len(out) <= MAX_FORMS, "Probe proposals exceed the forms train limit")
    return sorted(out, key=lambda row: (row["item_id"], row["owner_id"], row["surface"]))


def romanian_sections(parser, wikitext):
    starts, comments, _ = parser.top_level_lines(wikitext)
    sections = []
    start = None
    for heading, next_line, is_romanian in parser.section_headings(wikitext, starts, comments):
        if start is not None:
            sections.append(wikitext[start:heading])
        start = next_line if is_romanian else None
    if start is not None:
        sections.append(wikitext[start:])
    return sections


def collect_corpus(parser, cache, day, binding):
    receipt, receipt_sha = parser.archive_receipt(cache, day)
    require({"archive_url": receipt["url"], "archive_sha256": receipt["sha256"],
             "archive_receipt_sha256": receipt_sha} == binding, "Archive differs from the parser gate")
    titles, forms, scanned_titles = set(), set(), set()
    uncovered = {}
    counts = Counter({key: 0 for key in (
        "main_namespace_pages", "main_namespace_redirects_without_language_proof",
        "unreadable_wikitext_pages", "possible_romanian_headings_in_unreadable_wikitext",
        "unconfirmed_romanian_heading_markers", "pages_without_supported_romanian_heading",
        "romanian_title_pages", "supported_noun_tables", "unsupported_noun_table_pages",
        "supported_adjective_tables", "unsupported_adjective_table_pages", "ungated_verb_pages",
    )})
    revision_scan = parser.RevisionScan

    class CorpusScan(revision_scan):
        @property
        def selected(self):
            return self.page.get("ns") == "0" and not self.page.get("redirect")

        def finish_page(self):
            title = self.page.get("title")
            namespace = self.page.get("ns")
            if not title or namespace is None or not parser.DECIMAL.fullmatch(namespace):
                raise parser.DumpError("page lacks a valid title or namespace")
            if namespace != "0":
                return
            counts["main_namespace_pages"] += 1
            if title in scanned_titles:
                raise parser.DumpError("duplicate main namespace page title")
            scanned_titles.add(title)
            require(len(scanned_titles) <= MAX_CORPUS_ROWS, "Archive exceeds the main namespace page limit")
            if self.page.get("redirect"):
                counts["main_namespace_redirects_without_language_proof"] += 1
                return
            # The original scanner validates revision ID, model, format and
            # exact text bytes. Release each verified page after inspecting it.
            super().finish_page()
            wikitext = self.results.pop(title)["wikitext"]
            self.results_bytes = 0
            try:
                sections = romanian_sections(parser, wikitext)
            except parser.UnsupportedTable:
                counts["unreadable_wikitext_pages"] += 1
                if POTENTIAL_ROMANIAN.search(wikitext):
                    counts["possible_romanian_headings_in_unreadable_wikitext"] += 1
                    uncovered[title] = ["unreadable Romanian-marked wikitext"]
                return
            if not sections:
                if POTENTIAL_ROMANIAN.search(wikitext):
                    counts["unconfirmed_romanian_heading_markers"] += 1
                    uncovered[title] = ["Romanian heading marker outside a confirmed section"]
                else:
                    counts["pages_without_supported_romanian_heading"] += 1
                return
            titles.add(title)
            counts["romanian_title_pages"] += 1
            pos = {match[1].lower() for section in sections for match in PARTS_OF_SPEECH.finditer(section)}
            if "verb" in pos:
                counts["ungated_verb_pages"] += 1
                uncovered.setdefault(title, []).append("ungated verb paradigm")
            for kind, marker in parser.TABLE_NAMES.items():
                if marker not in pos:
                    continue
                try:
                    table = parser.parse_literal_table(title, wikitext, kind)
                except parser.UnsupportedTable:
                    counts[f"unsupported_{kind}_table_pages"] += 1
                    uncovered.setdefault(title, []).append(f"unsupported {kind} table")
                else:
                    counts[f"supported_{kind}_tables"] += 1
                    forms.update(cell[2] for cell in table["forms"])

    # reviewed_parser_gate creates an isolated module instance from the
    # reviewed bytes. Reuse its own streaming XML and checksum implementation.
    parser.RevisionScan = CorpusScan
    try:
        parser.scan_archive(cache / (receipt["sha256"] + ".dump"), receipt, [])
    finally:
        parser.RevisionScan = revision_scan
    corpus = sorted(titles | forms)
    require(titles and 0 < len(corpus) <= MAX_CORPUS_ROWS, "Invalid exact Romanian corpus size")
    raw = json_bytes(corpus)
    require(len(raw) <= MAX_CORPUS, "Exact Romanian corpus exceeds the byte limit")
    return raw, uncovered, {
        **counts, "exact_title_surfaces": len(titles), "exact_literal_table_surfaces": len(forms),
        "exact_union_surfaces": len(corpus), "pages_with_classified_coverage_gaps": len(uncovered),
        "table_scope": ["supported noun templates", "supported adjective templates"],
        "unsupported_scope": [
            "redirect spellings without their own Romanian section",
            "entries without a supported Romanian heading",
            "literal cells in unsupported or ambiguous templates and markup",
            "verb paradigms awaiting a separate parser gate",
            "inflections absent from titles and supported literal tables",
        ],
    }


def shards(probe_rows, neighbors, profanity):
    # The resolver diff counts aliases from the candidate bundle plus extra
    # array entries before deduplication. Each profanity probe is checked
    # against all Cald targets in the first shard.
    capacity = MAX_PROBE_INPUTS - len(probe_rows)
    require(0 < len(profanity) < capacity, "Profanity probes exceed the available shard slots")
    automatic = {row["surface"] for row in probe_rows}
    rest = sorted({row["surface"] for row in neighbors} - set(profanity) - automatic)
    first = capacity - len(profanity)
    groups = [sorted(profanity + rest[:first])]
    groups.extend(rest[i:i + capacity] for i in range(first, len(rest), capacity))
    return groups


def write_new(root, name, raw):
    with (root / name).open("xb") as file:
        file.write(raw)
    return {"path": name, "sha256": digest(raw)}


def subprocess_json(command, directory, label, timeout):
    with tempfile.TemporaryFile(dir=directory) as stream:
        done = subprocess.run(command, stdout=stream, stderr=subprocess.PIPE, timeout=timeout, check=False)
        require(done.returncode == 0, f"{label} failed: {done.stderr.decode(errors='replace')[:1500]}")
        size = stream.tell()
        require(0 < size <= MAX_ARTIFACT, f"{label} exceeded the result byte limit")
        stream.seek(0)
        return read_json(stream.read(size + 1))


def candidate_probes(args, repo, scratch, output):
    sha = exact_commit(repo, args.sha)
    baseline = exact_commit(repo, args.baseline)
    gate, parser, day = reviewed_parser_gate(
        scratch, {"path": args.gate, "sha256": args.gate_sha256}, repo, sha,
    )
    proposal_raw = pinned(scratch, args.proposals, args.proposals_sha256, 128 * 1024)
    proposed = proposals(proposal_raw)
    profanity_raw = git(repo, "--no-replace-objects", "show", f"{sha}:{PROFANITY}")
    profanity, witnesses = profanity_probes(profanity_raw, scratch)
    bundle = read_bundle(repo, baseline)
    binary = verified_binary(args.binary, args.binary_sha256)
    corpus, uncovered, coverage = collect_corpus(parser, scratch / "cache", day, gate["archive"])
    output.mkdir(mode=0o700)
    with tempfile.TemporaryDirectory(prefix="probe-inputs-", dir=output) as name:
        directory = Path(name)
        write_new(directory, "bundle.json", bundle)
        write_new(directory, "corpus.json", corpus)
        batch = write_new(directory, "batch.json", json_bytes({
            "proposals": proposed, "profanity": profanity, "frequency_witnesses": witnesses,
            "uncovered_titles": sorted(uncovered),
        }))
        result = subprocess_json(
            [str(binary), "--bundle", str(directory / "bundle.json"),
             "--batch", str(directory / "batch.json"), "--corpus", str(directory / "corpus.json")],
            directory, "Native collision probe scan", 900,
        )
    require(result["supported_corpus_rows"] == coverage["exact_union_surfaces"]
            and [{key: row[key] for key in ("item_id", "owner_id", "surface")}
                 for row in result["proposals"]] == proposed, "Native probe scan returned a different input")
    gaps = result["nearby_titles_with_coverage_gaps"]
    for row in gaps:
        row["reasons"] = uncovered[row["surface"]]
    for i, row in enumerate(result["proposals"]):
        row["nearby_titles_with_coverage_gaps_count"] = sum(i in gap["proposal_indexes"] for gap in gaps)
    groups = shards(result["proposals"], result["neighbors"], profanity)
    files = []
    for index, rows in enumerate(groups, 1):
        files.append({**write_new(output, f"probes-{index:04d}.json", json_bytes(rows)), "count": len(rows)})
    report = {
        "schema": "cat-v5-form-probes-1", "kit_sha": sha, "baseline": baseline,
        "baseline_bundle_sha256": digest(bundle), "native_binary_sha256": args.binary_sha256,
        "archive": gate["archive"], "gate_sha256": args.gate_sha256, "parser_sha256": gate["parser_sha256"],
        "comparator_sha256": gate["comparator_sha256"], "sample_sha256": gate["sample_sha256"],
        "proposals_sha256": args.proposals_sha256, "profanity_sha256": digest(profanity_raw),
        "frequency_source_receipt_sha256": FREQ_RECEIPT_SHA, "frequency_source_body_sha256": FREQ_BODY_SHA,
        "corpus_sha256": digest(corpus), "classified_coverage_gaps_sha256": digest(json_bytes(uncovered)),
        "native_batch_sha256": batch["sha256"], "coverage": coverage,
        "threshold": {"suggestions": .78, "fuzzy_contenders": .84, "direction": "proposal_key,probe_key"},
        "native_result": write_new(output, "native-result.json", json_bytes(result)),
        "automatic_probe_count": len(proposed), "shards": files,
    }
    return write_new(output, "manifest.json", json_bytes(report))


def aliases(raw):
    data = read_json(raw)
    return {row["id"]: set(row["aliases"]) for row in data["nodes"]}


def effective_additions(before, after):
    old, new = aliases(before), aliases(after)
    require(old.keys() == new.keys() and all(old[key] <= new[key] for key in old),
            "Resolver replay requires unchanged owners and additive aliases")
    return {(key, surface) for key in old for surface in new[key] - old[key]}


def answered_owner(answer):
    require(answer["mode"] in {"unknown", "confirm", "direct", "projection-or-fuzzy", "fuzzy-win"},
            "Unexpected Cald resolver mode")
    if answer["mode"] == "unknown":
        return ""
    owner = answer["guess"]["id"]
    require(isinstance(owner, str) and owner, "Resolved Cald probe lacks an owner")
    return owner


def replay(args, repo, scratch, output):
    manifest_path = args.manifest.absolute()
    require(manifest_path.resolve() == manifest_path and manifest_path.is_relative_to(scratch),
            "Canonical collision manifest inside campaign scratch required")
    manifest = read_json(pinned(manifest_path.parent, manifest_path.name, args.manifest_sha256, 128 * 1024))
    require(manifest["schema"] == "cat-v5-form-probes-1", "Invalid collision manifest schema")
    kit = exact_commit(repo, manifest["kit_sha"])
    baseline = exact_commit(repo, manifest["baseline"])
    candidate = exact_commit(repo, args.candidate)
    before, after = read_bundle(repo, baseline), read_bundle(repo, candidate)
    require(digest(before) == manifest["baseline_bundle_sha256"], "Collision manifest used a different baseline bundle")
    result_ref = manifest["native_result"]
    native = read_json(pinned(manifest_path.parent, result_ref["path"], result_ref["sha256"]))
    proposed = native["proposals"]
    expected = {(row["owner_id"], row["surface"]) for row in proposed}
    require(expected and len(expected) == manifest["automatic_probe_count"] == len(proposed)
            and effective_additions(before, after) == expected,
            "Candidate aliases differ from the collision proposal. Rebuild probes after dropping forms.")
    raw = git(repo, "--no-replace-objects", "show", f"{kit}:{PROFANITY}")
    require(digest(raw) == manifest["profanity_sha256"], "Replay used a different profanity list")
    profanity, _ = profanity_probes(raw, scratch)
    resolver = repo / RESOLVER_DIFF
    wrapper_raw = git(repo, "--no-replace-objects", "show", f"{kit}:{RESOLVER_DIFF}")
    require(wrapper_raw == read_artifact(repo, RESOLVER_DIFF, 128 * 1024),
            "Checkout resolver wrapper differs from the probe kit")
    binary = verified_binary(args.resolver_binary, args.resolver_binary_sha256)

    groups = shards(proposed, native["neighbors"], profanity)
    require(len(groups) == len(manifest["shards"]), "Collision shard count differs")
    output.mkdir(mode=0o700)
    reports, forbidden, targets = [], [], None
    workers = ["--workers", str(args.workers)] if args.workers != 1 else []
    for row, group in zip(manifest["shards"], groups, strict=True):
        path = manifest_path.parent / row["path"]
        require(pinned(manifest_path.parent, row["path"], row["sha256"], 512 * 1024) == json_bytes(group)
                and row["count"] == len(group), "Collision shard inventory differs")
        report = subprocess_json(
            [sys.executable, "-I", "-B", str(resolver), "--repo", str(repo), "--baseline", baseline,
             "--sha", candidate, "--binary", str(binary), "--binary-sha256", args.resolver_binary_sha256,
             "--scratch", str(output), "--probes", str(path), *workers],
            output, "Cald resolver shard", 3660,
        )
        probes = sorted(set(group) | {row["surface"] for row in proposed})
        require(report["schema"] == "cat-resolver-diff-1" and report["probes"] == probes
                and report["baseline"] == baseline and report["sha"] == candidate
                and report["before_bundle_sha256"] == digest(before)
                and report["after_bundle_sha256"] == digest(after)
                and report["binary_sha256"] == args.resolver_binary_sha256
                and report["extra_probes_sha256"] == row["sha256"]
                and report["checked_count"] == len(probes) * len(report["targets"]),
                "Cald resolver shard report differs from exact inputs")
        if targets is None:
            targets = report["targets"]
        require(targets and targets == report["targets"], "Cald shard target inventory differs")
        for change in report["changes"]:
            if change["probe"] in profanity:
                old, new = answered_owner(change["before"]), answered_owner(change["after"])
                if new and new != old:
                    forbidden.append({"probe": change["probe"], "board_id": change["board_id"],
                                      "before_owner": old, "after_owner": new})
        reports.append(write_new(output, path.stem + "-resolver.json", json_bytes(report)))
    exact = [row for row in proposed if row.get("profanity_exact")]
    report = {
        "schema": "cat-v5-form-probe-replay-1", "manifest_sha256": args.manifest_sha256,
        "kit_sha": kit, "baseline": baseline, "candidate": candidate,
        "baseline_bundle_sha256": digest(before), "candidate_bundle_sha256": digest(after),
        "resolver_binary_sha256": args.resolver_binary_sha256, "resolver_wrapper_sha256": digest(wrapper_raw),
        "profanity_sha256": digest(raw), "shard_reports": reports, "target_count": len(targets),
        "exact_profanity_matches": exact, "native_profanity_changes": native["unsafe_resolutions"],
        "cald_profanity_changes": forbidden, "unavailable_neighbors": native["unavailable_neighbors"],
        "nearby_titles_with_coverage_gaps": native["nearby_titles_with_coverage_gaps"],
    }
    report["profanity_pass"] = not (exact or native["unsafe_resolutions"] or forbidden)
    return write_new(output, "manifest.json", json_bytes(report))


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    commands = cli.add_subparsers(dest="command", required=True)
    build = commands.add_parser("build", help="build deterministic offline collision shards")
    audit = commands.add_parser("replay", help="run the private resolver diff for each bound shard")
    for command in (build, audit):
        command.add_argument("--repo", type=Path, default=Path.cwd())
        command.add_argument("--scratch", required=True, type=Path, help="private campaign root")
        command.add_argument("--output", required=True, type=Path, help="fresh subdirectory of campaign scratch")
    for key in ("sha", "baseline", "gate", "gate-sha256", "proposals", "proposals-sha256", "binary-sha256"):
        build.add_argument("--" + key, required=True)
    build.add_argument("--binary", required=True, type=Path)
    for key in ("manifest-sha256", "candidate", "resolver-binary-sha256"):
        audit.add_argument("--" + key, required=True)
    audit.add_argument("--manifest", required=True, type=Path)
    audit.add_argument("--resolver-binary", required=True, type=Path)
    audit.add_argument("--workers", type=int, choices=range(1, 17), default=1)
    args = cli.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        scratch = args.scratch.absolute()
        output = args.output.absolute()
        require(scratch.is_dir() and scratch.resolve() == scratch and output.resolve() == output
                and output.is_relative_to(scratch) and output != scratch,
                "Canonical private scratch and fresh output path required")
        result = (candidate_probes if args.command == "build" else replay)(args, repo, scratch, output)
        print(json.dumps(result, sort_keys=True))
        if args.command == "replay" and not read_json((output / result["path"]).read_bytes())["profanity_pass"]:
            return 2
    except (OSError, UnicodeError, ValueError, TypeError, KeyError, ExpatError, subprocess.SubprocessError) as exc:
        print(f"form probes: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
