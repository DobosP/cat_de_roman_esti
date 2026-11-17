#!/usr/bin/env python3
"""Prepare an exact Pilot 2 or Pilot 3 additive word and link transaction."""

import argparse
from contextlib import redirect_stdout
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
from urllib.parse import urlsplit

sys.dont_write_bytecode = True
SCRIPTS = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(SCRIPTS.parent),
                str(SCRIPTS), str(SCRIPTS / "landing")]
from alias_install import (
    capture, lemma_key, reviewed_parser_gate, verified_binary, verified_json,
)
from content_file_transaction import atomic_write, file_transaction
from content_registry import current_rows, dump_page_receipt
from densify_content import CATEGORIES, merge_records, rebuild_document, tier_for_salience
from import_candidates import GAME_KINDS, WordGameService, load_fixture, rederive_existing_items
from link_spans import NO_AI, check_batch, extract_blocks, read_batch, raw_title_refused, verified_body
from support import clean_source, digest, exact_commit, git, read_artifact, read_json, relative_parts, require
import frequency as frequency_lookup

KG = "cat_de_roman_esti/fixtures/kg_sample.json"
PACK = "cat_de_roman_esti/fixtures/games_pack.json"
REGISTRY = "docs/content-registry/registry.jsonl"
FREQUENCY_URL = "https://raw.githubusercontent.com/hermitdave/FrequencyWords/master/content/2018/ro/ro_50k.txt"
FULL_FREQUENCY_PATH = "frequency/ro_full.txt"
FULL_FREQUENCY_SHA256 = "a0d0993701e251e91b9047753b6032be751217a5aaba36ed879163e020e33ded"
FULL_FREQUENCY_BYTES = 15_199_764
FULL_FREQUENCY_CONTRACT = {"list": "FrequencyWords 2018 ro_full.txt",
                           "sha256": FULL_FREQUENCY_SHA256,
                           "tool": "scripts/content_v5/frequency.py"}
MAX_KG = 16 * 1024 * 1024
MAX_INPUT = 1024 * 1024
EDGE_KEYS = ("src_id", "dst_id", "relation", "bidirectional")
NODE_KEYS = {"id", "node_type", "label_ro", "category", "description", "salience"}
LINK_KEYS = {*EDGE_KEYS, "label_ro", "strength"}
WIKI_DEFINITION = re.compile(r"^#[ \t]*[^#\s:*]")


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def text(value, maximum):
    return isinstance(value, str) and bool(value.strip()) and value == value.strip() and len(value) <= maximum


def number(value, decimals, low, high):
    return (type(value) in (int, float) and low <= value <= high
            and round(value, decimals) == value)


def link_key(row):
    return tuple(row[key] for key in EDGE_KEYS)


def merge_input(items, before, baseline, *, key_for=lemma_key, excluded=()):
    old = {node["id"]: node for node in before["kg_nodes"]}
    existing = {node["id"]: node for node in baseline["kg_nodes"]}
    allowed_relations = {edge["relation"] for edge in before["kg_edges"]}
    labels = {key_for(node["label_ro"]) for node in old.values()}
    labels.update(key_for(alias) for node in old.values() for alias in node.get("aliases", []))
    nodes, links, owners, reviewed_edges = [], [], {}, {}
    for item in items:
        require(set(item) == {"id", "node", "links", "source"}, "Invalid word item fields")
        node = item["node"]
        require(isinstance(node, dict) and set(node) == NODE_KEYS
                and isinstance(node["id"], str) and re.fullmatch(r"n_[a-z0-9_]{1,100}", node["id"])
                and node["node_type"] == "concept" and node["category"] in CATEGORIES
                and text(node["label_ro"], 100) and text(node["description"], 280)
                and all(ord(ch) >= 32 and ord(ch) != 127
                        for field in ("label_ro", "description") for ch in node[field])
                and number(node["salience"], 4, 0, 1), "Invalid new concept")
        label_key = key_for(node["label_ro"])
        require(label_key and node["id"] not in old and node["id"] not in owners
                and label_key not in labels, "New word ID or label already exists")
        require(label_key not in excluded, "New word matches an existing lexical exclusion")
        labels.add(label_key)
        nodes.append(node)
        owners[node["id"]] = node
    endpoints = {**old, **owners}
    used = {(*sorted((edge["src_id"], edge["dst_id"])), edge["relation"]) for edge in before["kg_edges"]}
    edges_by_word = {}
    for item in items:
        node = item["node"]
        owner = node["id"]
        batch = item["links"]
        require(isinstance(batch, list) and 4 <= len(batch) <= 8,
                f"{owner} needs four to eight links")
        neighbors, item_edges = set(), set()
        edges_by_word[owner] = item_edges
        for edge in batch:
            require(isinstance(edge, dict) and set(edge) == LINK_KEYS
                    and type(edge["bidirectional"]) is bool
                    and edge["relation"] in allowed_relations and text(edge["label_ro"], 140)
                    and number(edge["strength"], 3, 0.001, 1), f"Invalid reviewed edge for {owner}")
            src, dst, relation, _ = link_key(edge)
            require(src != dst and owner in (src, dst) and src in endpoints and dst in endpoints,
                    f"Link must connect {owner} to a known, distinct node")
            opposite = dst if src == owner else src
            neighbors.add(opposite)
            key = (*sorted((src, dst)), relation)
            require(key not in item_edges, f"Duplicate link for {owner}")
            item_edges.add(key)
            if key in reviewed_edges:
                require(edge == reviewed_edges[key], f"Two reviewed links conflict for {src} and {dst}")
                continue
            require(key not in used, f"Link already exists for {src} and {dst}")
            used.add(key)
            reviewed_edges[key] = edge
            links.append(edge)
        main_words = {endpoint for endpoint in neighbors if endpoint in existing
                      and existing[endpoint]["node_type"] == "concept"
                      and existing[endpoint]["label_ro"].isalpha()}
        same_category = {endpoint for endpoint in neighbors
                         if endpoints[endpoint]["category"] == node["category"]}
        require(len(main_words) >= 2 and len(same_category) >= 2,
                f"{owner} needs two baseline main words and two same-category neighbors")
    for key in reviewed_edges:
        require(all(key in edges_by_word[endpoint] for endpoint in key[:2] if endpoint in edges_by_word),
                "A link between two new words must appear in both frozen word reviews")
    return nodes, links


def exact_additions(before, after, nodes, links):
    old_nodes = {node["id"]: node for node in before["kg_nodes"]}
    new_nodes = {node["id"]: node for node in after["kg_nodes"]}
    require(len(new_nodes) == len(after["kg_nodes"])
            and new_nodes.keys() == old_nodes.keys() | {node["id"] for node in nodes},
            "Graph merge changed the expected node inventory")
    for node_id, old in old_nodes.items():
        require({k: v for k, v in old.items() if k != "degree"} ==
                {k: v for k, v in new_nodes[node_id].items() if k != "degree"},
                f"Graph merge altered existing node {node_id}")
    for node in nodes:
        expected = {**node, "difficulty_tier": tier_for_salience(node["salience"])}
        actual = {k: v for k, v in new_nodes[node["id"]].items() if k != "degree"}
        require(actual == expected, f"Graph merge altered frozen node {node['id']}")
    old_edges, all_edges = before["kg_edges"], after["kg_edges"]
    require(all_edges[:len(old_edges)] == old_edges and len(all_edges) == len(old_edges) + len(links)
            and len({edge["id"] for edge in all_edges}) == len(all_edges),
            "Graph merge changed old edges or failed to install every exact link")
    for expected, actual in zip(links, all_edges[len(old_edges):], strict=True):
        shape = {key: actual[key] for key in LINK_KEYS}
        shape["bidirectional"] = bool(shape["bidirectional"])
        require(shape == expected and actual["is_distractor"] == 0, "Graph merge altered a frozen link")


def generate(kg, pack, nodes, links, work, native, repo, campaign):
    original = read_json(kg)
    data = read_json(kg)
    dense = {"nodes": nodes, "edges": [
        {"src": edge["src_id"], "dst": edge["dst_id"], "relation": edge["relation"],
         "label_ro": edge["label_ro"], "strength": edge["strength"], "bidirectional": edge["bidirectional"]}
        for edge in links
    ]}
    with redirect_stdout(sys.stderr):
        merged_nodes, merged_edges = merge_records(data, dense)
        result = rebuild_document(data, merged_nodes, merged_edges, f"fixture-{campaign}-words",
                                  f"Pilot {campaign.rsplit('-', 1)[1]} reviewed graph words and source-backed links.")
    exact_additions(original, data, nodes, links)
    kg_path = work / "kg_sample.json"
    kg_path.write_bytes(result.encode("utf-8"))
    capture([str(native), "validate-fixture", "--root", str(repo), "--kg", str(kg_path)],
            "Native graph validation")
    stock = read_json(pack)
    messages = []
    survivors = rederive_existing_items(stock, WordGameService(graph=load_fixture(kg_path).graph), messages)
    changes = []
    for game in GAME_KINDS:
        old = {board["id"]: board for board in stock[game]}
        new = {board["id"]: board for board in survivors[game]}
        require(new.keys() <= old.keys(), f"Unexpected new board in {game}")
        for board_id, prior in old.items():
            after = new.get(board_id)
            if after != prior:
                changes.append({"game": game, "id": board_id, "status": "removed" if after is None else "changed"})
    if changes:
        for game in GAME_KINDS:
            stock[game] = survivors[game]
        stock["meta"]["counts"] = {game: len(stock[game]) for game in GAME_KINDS}
        pack = (json.dumps(stock, ensure_ascii=False, indent=1, allow_nan=False) + "\n").encode("utf-8")
    pack_path = work / "games_pack.json"
    pack_path.write_bytes(pack)
    capture([str(native), "validate-pack", "--root", str(repo), "--kg", str(kg_path), "--pack", str(pack_path)],
            "Native pack validation")
    return kg_path.read_bytes(), pack, changes, messages


def published_outputs(repo, old_kg, old_pack, new_kg, new_pack):
    pairs = {repo / KG: (old_kg, new_kg), repo / PACK: (old_pack, new_pack),
             repo / "tests/fixtures/kg_sample.json": (old_kg, new_kg),
             repo / "tests/fixtures/games_pack.json": (old_pack, new_pack)}
    lock = repo / ".cat-content-ops.lock"
    with lock.open("xb"):
        pass
    try:
        with file_transaction(pairs) as snapshots:
            require(all(snapshots[path] == old for path, (old, _) in pairs.items()),
                    "Fixture or pack changed during preparation")
            for path, (old, new) in pairs.items():
                if new != old:
                    atomic_write(path, new)
            require(all(path.read_bytes() == new for path, (_, new) in pairs.items()),
                    "Written mirrors differ from the validated candidate")
    finally:
        lock.unlink()


def frequency_rows(root, reference):
    require(set(reference) == {"receipt", "body_sha256"}, "Invalid frequency evidence")
    ref = reference["receipt"]
    require(set(ref) == {"path", "sha256"}, "Invalid frequency receipt reference")
    file_name = digest(FREQUENCY_URL.encode("ascii")) + ".receipt.json"
    require(ref["path"] in (f"cache/{file_name}", f"legacy-cache/{file_name}"),
            "Frequency receipt is outside the permitted cache")
    raw = read_artifact(root, ref["path"], 512 * 1024)
    require(digest(raw) == ref["sha256"], "Frequency receipt hash differs")
    receipt = read_json(raw)
    body_sha = receipt["sha256"]
    require(receipt["url"] == FREQUENCY_URL and type(receipt["status"]) is int
            and receipt["status"] == 200 and body_sha == reference["body_sha256"]
            and re.fullmatch(r"[a-f0-9]{64}", body_sha) and receipt.get("body_problem", "") == "",
            "Expected complete approved FrequencyWords receipt")
    headers = receipt["headers"]
    require(isinstance(headers, dict) and all(isinstance(value, str) for value in headers.values())
            and not headers.get("content-signal") and headers.get("content-signal-present", "false") == "false"
            and not NO_AI.search(headers.get("x-robots-tag", "")) and not headers.get("location")
            and not headers.get("content-range")
            and headers.get("content-encoding", "").lower() in ("", "identity"),
            "FrequencyWords response has an ineligible source header")
    cache = ref["path"].split("/")[0]
    body = read_artifact(root, f"{cache}/{body_sha}.body", MAX_INPUT)
    require(len(body) == receipt["bytes"] and digest(body) == body_sha, "Frequency body hash differs")
    decoded = body.decode("utf-8")
    require(not raw_title_refused(decoded), "FrequencyWords response contains a refusal title")
    rows = {}
    for line in decoded.splitlines():
        word, count = line.rsplit(" ", 1)
        require(word and count.isascii() and count.isdecimal() and word not in rows,
                "Malformed FrequencyWords row")
        rows[word] = int(count)
    return rows



def campaign_contract(contract, base):
    campaign = contract.get("campaign")
    require(campaign in ("v5-pilot-2", "v5-pilot-3") and contract.get("base_sha") == base,
            "Baseline differs from the active Pilot 2 or Pilot 3 contract")
    if campaign == "v5-pilot-3":
        require(contract.get("frequency") == FULL_FREQUENCY_CONTRACT,
                "Pilot 3 frequency contract differs from ADR-0235")
    return campaign


def verify_frequency(root, source, label, campaign, frequencies):
    if campaign == "v5-pilot-3":
        require(set(source) == {"list", "row"}
                and source["list"] == {"path": FULL_FREQUENCY_PATH, "sha256": FULL_FREQUENCY_SHA256},
                "Pilot 3 requires the exact ADR-0235 pinned full frequency list")
        if campaign not in frequencies:
            # Preserve the path/symlink protections and the dedicated exact-size bound.
            body = read_artifact(root, FULL_FREQUENCY_PATH, FULL_FREQUENCY_BYTES)
            require(len(body) == FULL_FREQUENCY_BYTES and digest(body) == FULL_FREQUENCY_SHA256,
                    "Pinned full frequency list bytes differ")
            frequencies[campaign] = frequency_lookup.load(root / FULL_FREQUENCY_PATH,
                                                          FULL_FREQUENCY_SHA256,
                                                          max_bytes=FULL_FREQUENCY_BYTES)
        row = frequencies[campaign].lookup(label)
        require(canonical(source["row"]) == canonical(row), "Folded frequency result differs")
        require(type(row["exact"]) is int and row["exact"] > 0 and row["status"] == "exact",
                "Positive exact word frequency required")
        return row
    require(campaign == "v5-pilot-2", "Unsupported word frequency campaign")
    # Historical Pilot 2 receipt evidence stays historical; it is never promoted to full-list proof.
    require(set(source) == {"receipt", "body_sha256", "word", "count"}
            and lemma_key(source["word"]) == lemma_key(label)
            and type(source["count"]) is int and source["count"] > 0,
            "Positive exact word frequency required")
    ref = {key: source[key] for key in ("receipt", "body_sha256")}
    key = canonical(ref)
    if key not in frequencies:
        frequencies[key] = frequency_rows(root, ref)
    require(frequencies[key].get(source["word"]) == source["count"], "Exact frequency row differs")
    return {"word": source["word"], "count": source["count"]}


def wiki_language(parser, raw):
    starts, comments, unsupported = parser.top_level_lines(raw)
    headings = list(parser.section_headings(raw, starts, comments))
    sections = [(end, headings[i + 1][0] if i + 1 < len(headings) else len(raw))
                for i, (_, end, romanian) in enumerate(headings) if romanian]
    require(len(sections) == 1, "Expected one exact Romanian lexical section")
    start, end = sections[0]
    require(unsupported >= start, "Unsupported markup before the Romanian lexical section")
    return raw[start:end], {offset - start for offset in starts if start <= offset < end}


def verified_sources(scratch, gate_ref, repo, sha, items, campaign):
    gate, parser, day = reviewed_parser_gate(scratch, gate_ref, repo, sha)
    cache = scratch / "cache"
    require(cache.is_dir() and cache.resolve() == cache, "Canonical source cache required")
    bindings = []
    for item in items:
        source = item["source"]
        require(set(source) == {"wiktionary", "wikipedia", "frequency"}, "Invalid word evidence shape")
        dump = source["wiktionary"]
        wiki = source["wikipedia"]
        require(eligible_metadata(dump) and dump_page_receipt(dump)
                and all(dump[key] == gate["archive"][key] for key in gate["archive"])
                and lemma_key(dump["title"]) == lemma_key(item["node"]["label_ro"]),
                "Wiktionary page does not bind the word and reviewed archive")
        require(set(wiki) == {"url", "receipt_sha256", "body_sha256"}
                and urlsplit(wiki["url"]).netloc == "ro.wikipedia.org", "A live Romanian Wikipedia article is required")
        article = verified_body(cache, wiki["url"], wiki["receipt_sha256"], wiki["body_sha256"])
        require(extract_blocks(article, wiki["url"]), "Romanian Wikipedia article has no verifiable body")
        bindings.append((item, dump, wiki))
    titles = list(dict.fromkeys(dump["title"] for _, dump, _ in bindings))
    pages = parser.extract(cache, day, titles, expected_archive_sha256=gate["archive"]["archive_sha256"])
    require(not pages["missing_titles"]
            and all(pages[key] == gate["archive"][key] for key in gate["archive"]), "Word pages differ from reviewed archive")
    by_title = {page["title"]: page for page in pages["pages"]}
    archive, _ = parser.archive_receipt(cache, day)
    frequencies = {}
    for item, dump, wiki in bindings:
        page = by_title[dump["title"]]
        require(page["revision_id"] == dump["revision_id"] and page["text_sha256"] == dump["text_sha256"]
                and archive["first_fetcher"] == dump.get("first_fetcher"), "Wiktionary revision or fetcher differs")
        language, line_starts = wiki_language(parser, page["wikitext"])
        pos = re.compile(r"\{\{-(?:substantiv|adjectiv|verb|adverb|pronume|numeral|interjecție|prepoziție|conjuncție)-\|ron\}\}[ \t]*$")
        lines, offset = [], 0
        for line in language.splitlines(keepends=True):
            if offset in line_starts:
                lines.append(line.rstrip("\n"))
            offset += len(line)
        require(any(pos.fullmatch(line) for line in lines)
                and any(WIKI_DEFINITION.match(line) for line in lines),
                "No supported Romanian lexical definition in the page")
        require(not re.search(r"(?i)(?<!\w)(?:vulgar|argou|peiorativ|depreciativ|trivial)(?!\w)", language),
                "Romanian lexical section contains an excluded usage label")
        verify_frequency(scratch, item["source"]["frequency"], item["node"]["label_ro"],
                         campaign, frequencies)
    return gate, bindings


def verify_span_evidence(scratch, reference, links):
    require(set(reference) == {"path", "sha256"}, "Invalid link claims reference")
    raw = read_artifact(scratch, reference["path"], MAX_INPUT)
    require(digest(raw) == reference["sha256"], "Link claims hash differs")
    rows = read_batch(raw)
    require({link_key(row["link"]) for row in rows} == {link_key(edge) for edge in links},
            "Quote coverage differs from the exact additive links")
    result = check_batch(scratch / "cache", raw)
    require(result["status"] == "pass", "Link source span check failed")
    results = {link_key(row["link"]): row for row in result["links"]}
    require(len(results) == len(rows) and results.keys() == {link_key(row["link"]) for row in rows},
            "Verified quote output does not cover exact links")
    return digest(canonical(result)), results


def item_span_evidence(item, edge_results):
    rows = [edge_results[link_key(link)] for link in item["links"]]
    result = {"schema": "cat-v5-link-item-spans-1", "item_id": item["id"], "links": rows}
    return digest(canonical(result)), {row["url"] for row in rows}


def eligible_metadata(ref):
    return (isinstance(ref, dict) and ref.get("first_fetch_origin") == "v5"
            and ref.get("origin", "v5") == "v5" and isinstance(ref.get("scope", ""), str)
            and ref.get("scope") not in ("model", "legacy", "kg-only")
            and ref.get("fetched_by_role") in ("script", "factual", "quality", "critic")
            and type(ref.get("status", 200)) is int and ref.get("status", 200) == 200
            and ref.get("body_problem", "") == "" and "dump_failure" not in ref)


def expected_source_ref(provenance, dump, wiki):
    eligible = [ref for ref in provenance if eligible_metadata(ref)]
    return (
        any(all(ref.get(key) == value for key, value in dump.items()) for ref in eligible)
        and any(ref.get("url") == wiki["url"] and ref.get("sha256") == wiki["receipt_sha256"]
                and ref.get("body_sha256") == wiki["body_sha256"] for ref in eligible)
    )


def cited_live_sources(root, references, author_thread):
    require(isinstance(references, list) and references, "A reviewer needs live independent source evidence")
    urls = set()
    for reference in references:
        require(isinstance(reference, dict) and set(reference) == {"url", "receipt_sha256", "body_sha256"},
                "Invalid reviewer article citation")
        url = reference["url"]
        body = verified_body(root / "cache", url, reference["receipt_sha256"], reference["body_sha256"])
        require(extract_blocks(body, url), "Reviewer citation has no verifiable article body")
        receipt = read_json(read_artifact(root / "cache", digest(url.encode("ascii")) + ".receipt.json", 512 * 1024))
        if receipt["first_fetcher"] != author_thread:
            urls.add(url)
    return urls


def dry_backlog(registry):
    return next((row for row in registry.values() if row["state"] == "sourced"
                 and row["type"] == "concept" and row["lane"] == "L2"
                 and row["origin"].get("state") == "ACTIVE_UNASSESSED"
                 and row["origin"].get("source", {}).get("scope") == "v3-seed"), None)


def verify_review(scratch, item, row, binding, gate_reviewer, span_sha, allowed_urls):
    fields = {"v5_word_review_binding", "v5_derived_view_sha256", "v5_independence_checks"}
    checks = row.get("checks", {})
    top_fields, nested_fields = fields & row.keys(), fields & checks.keys()
    # Early Pilot 2 journal rows stored the complete review proof under checks.
    require((top_fields == fields and not nested_fields)
            or (nested_fields == fields and not top_fields),
            "Reviewed word binding must occupy exactly one complete registry location")
    review = row if top_fields else checks
    require(set(binding) == {"author_thread", "payload_sha256", "derived_view_sha256", "reviews"}
            and binding["payload_sha256"] == digest(canonical(item))
            and review.get("v5_word_review_binding") == binding
            and review.get("v5_derived_view_sha256") == binding["derived_view_sha256"]
            and review.get("v5_independence_checks") == {
                "signed_reviews": True, "rationale_overlap_ok": True,
                "reviewer_identity_leaks_checked": True, "source_reuse_checked": True,
            }
            and re.fullmatch(r"[a-f0-9]{64}", binding["derived_view_sha256"])
            and set(binding["reviews"]) == {"critic", "factual", "quality"}
            and len({ref["path"] for ref in binding["reviews"].values()}) == 3
            and text(binding["author_thread"], 128) and binding["author_thread"] != gate_reviewer,
            "Reviewed word binding differs from the registry")
    threads = {binding["author_thread"], gate_reviewer}
    critic = verified_json(scratch, binding["reviews"]["critic"], "blind word play")
    require(critic.get("role") == "critic" and critic.get("verdict") == "pass"
            and critic.get("item_id") == item["id"] and critic.get("payload_sha256") == binding["payload_sha256"]
            and critic.get("derived_view_sha256") == binding["derived_view_sha256"]
            and text(critic.get("thread_id"), 128) and critic["thread_id"] not in threads
            and re.fullmatch(r"[a-f0-9]{64}", critic.get("transcript_sha256", "")),
            "Independent blind word play did not pass for the exact view")
    transcript = read_artifact(scratch, critic["transcript_path"], MAX_INPUT)
    require(digest(transcript) == critic["transcript_sha256"], "Blind word transcript differs")
    threads.add(critic["thread_id"])
    for role in ("factual", "quality"):
        proof = verified_json(scratch, binding["reviews"][role], f"{role} word review")
        thread = proof.get("thread_id")
        require(text(thread, 128) and thread not in threads and proof.get("role") == role
                and proof.get("verdict") == "accept" and proof.get("child_safe") is True
                and proof.get("item_id") == item["id"]
                and proof.get("payload_sha256") == binding["payload_sha256"]
                and proof.get("derived_view_sha256") == binding["derived_view_sha256"]
                and proof.get("span_result_sha256") == span_sha, f"Missing exact independent {role} word review")
        require(cited_live_sources(scratch, proof.get("sources"), binding["author_thread"]) & allowed_urls,
                f"{role} did not cite an independently fetched word or link article")
        threads.add(thread)


def verify_registry(scratch, document, registry, bindings, gate, edge_results, dry):
    items = document["items"]
    judgments = document["judgments"]
    item_ids = {item["id"] for item in items}
    require(len(item_ids) == len(items), "Duplicate word registry IDs")
    if dry:
        first = dry_backlog(registry)
        require(first and len(items) == 1 and first["id"] in item_ids and judgments == {},
                "Dry run requires the first sourced backlog word and no reviews")
    else:
        require(set(judgments) == item_ids, "Independent word reviews must cover every item")
    for item, dump, wiki in bindings:
        row = registry.get(item["id"])
        require(row and row["type"] == "concept" and row["state"] == ("sourced" if dry else "reviewed")
                and not row["holds"] and row["identity"].get("owner_id") == item["node"]["id"]
                and lemma_key(row["label_ro"]) == lemma_key(item["node"]["label_ro"])
                and row["checks"].get("v5_word_source_sha256") == digest(canonical(item))
                and expected_source_ref(row["provenance"], dump, wiki),
                "Word is missing its exact unheld registry and source binding")
        for dep in row.get("dependencies", []):
            require(dep in item_ids or registry.get(dep, {}).get("state") == "landed", f"Unlanded word dependency {dep}")
        group = row.get("co_landing_group")
        if group:
            require({r["id"] for r in registry.values() if r.get("co_landing_group") == group} <= item_ids,
                    "Partial word co-landing group")
        if not dry:
            item_span_sha, allowed_urls = item_span_evidence(item, edge_results)
            allowed_urls.add(wiki["url"])
            verify_review(scratch, item, row, judgments[item["id"]], gate["reviewer_thread"],
                          item_span_sha, allowed_urls)


def native_label_authority(repo, kg, sha):
    bundle = read_json(git(repo, "--no-replace-objects", "show", f"{sha}:go-backend/internal/content/bundled.json"))
    require(bundle["sources"]["kg_sample.json"] == digest(kg.replace(b"\r\n", b"\n").replace(b"\r", b"\n")),
            "Native bundle graph binding differs from the current fixture")
    mapping = bundle["normalization_map"]

    def key_for(value):
        return " ".join("".join(mapping.get(char, char) for char in value).split())

    exclusions = read_json(git(repo, "--no-replace-objects", "show", f"{sha}:docs/content-registry/exclusions.json"))
    excluded = {key_for(row["literal"]) for row in exclusions["lexical_declarations"]
                if isinstance(row.get("literal"), str)}
    excluded.update(key_for(form) for rule in exclusions["owner_rules"].values() for form in rule.get("forms", []))
    return key_for, excluded


def read_pair(repo, primary, mirror):
    raw = read_artifact(repo, primary, MAX_KG)
    require(raw == read_artifact(repo, mirror, MAX_KG), f"Source mirrors differ for {primary}")
    return raw


def main(argv=None):
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--repo", type=Path, required=True)
    cli.add_argument("--sha", required=True, help="Exact clean candidate commit")
    cli.add_argument("--baseline", required=True, help="Exact active campaign contract base commit")
    cli.add_argument("--scratch", type=Path, required=True)
    cli.add_argument("--input", required=True, help="Word and link manifest relative to scratch")
    cli.add_argument("--input-sha256", required=True)
    cli.add_argument("--cat-content", type=Path, required=True)
    cli.add_argument("--cat-content-sha256", required=True)
    mode = cli.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run-out", help="New directory relative to scratch for the one-word candidate")
    mode.add_argument("--write", action="store_true", help="Install the independently reviewed S7 batch")
    args = cli.parse_args(argv)
    try:
        repo = args.repo.resolve(strict=True)
        scratch = args.scratch.absolute()
        require(scratch.is_dir() and scratch.resolve() == scratch and not scratch.is_relative_to(repo),
                "Canonical scratch outside the worktree required")
        sha = exact_commit(repo, args.sha)
        base = exact_commit(repo, args.baseline)
        clean_source(repo, sha)
        require(git(repo, "symbolic-ref", "-q", "HEAD").strip() == b"refs/heads/content/v5",
                "Link installation requires content/v5")
        require(not git(repo, "merge-base", "--is-ancestor", base, sha), "Pilot baseline must precede the candidate")
        contract = read_json(read_artifact(scratch, "contract.json", 64 * 1024))
        campaign = campaign_contract(contract, base)
        raw = read_artifact(scratch, args.input, MAX_INPUT)
        require(digest(raw) == args.input_sha256, "Word manifest SHA-256 differs")
        document = read_json(raw)
        require(set(document) == {"schema", "items", "gate", "claims", "judgments"}
                and document["schema"] == "cat-v5-link-install-1" and isinstance(document["items"], list)
                and 0 < len(document["items"]) <= 20, "Invalid word and link manifest")
        items = document["items"]
        kg = read_pair(repo, KG, "tests/fixtures/kg_sample.json")
        pack = read_pair(repo, PACK, "tests/fixtures/games_pack.json")
        baseline = read_json(git(repo, "--no-replace-objects", "show", f"{base}:{KG}"))
        registry_raw = read_artifact(repo, REGISTRY, 64 * 1024 * 1024)
        require(registry_raw.endswith(b"\n"), "Registry journal has an incomplete tail")
        registry = current_rows((read_json(line) for line in registry_raw.split(b"\n")[:-1]), repo)
        key_for, excluded = native_label_authority(repo, kg, sha)
        nodes, links = merge_input(items, read_json(kg), baseline, key_for=key_for, excluded=excluded)
        span_sha, edge_results = verify_span_evidence(scratch, document["claims"], links)
        gate, bindings = verified_sources(scratch, document["gate"], repo, sha, items, campaign)
        dry = args.dry_run_out is not None
        verify_registry(scratch, document, registry, bindings, gate, edge_results, dry)
        native = verified_binary(args.cat_content, args.cat_content_sha256)
        with tempfile.TemporaryDirectory(prefix="link-install-", dir=scratch) as name:
            prepared = Path(name)
            new_kg, new_pack, changes, messages = generate(kg, pack, nodes, links, prepared, native, repo, campaign)
        clean_source(repo, sha)
        outputs = {"kg_sha256": digest(new_kg), "pack_sha256": digest(new_pack)}
        if dry:
            parts = relative_parts(args.dry_run_out)
            parent = scratch.joinpath(*parts[:-1])
            require(parent.is_dir() and parent.resolve() == parent, "Canonical output parent required")
            destination = parent / parts[-1]
            require(not destination.exists() and not destination.is_symlink(), "Dry-run output already exists")
            with tempfile.TemporaryDirectory(prefix=".dry-link-", dir=parent) as name:
                folder = Path(name) / "candidate"
                folder.mkdir()
                (folder / "kg_sample.json").write_bytes(new_kg)
                (folder / "games_pack.json").write_bytes(new_pack)
                os.rename(folder, destination)
            outputs.update(kg=str(destination / "kg_sample.json"), pack=str(destination / "games_pack.json"))
        else:
            published_outputs(repo, kg, pack, new_kg, new_pack)
        report = {"schema": "cat-v5-link-install-result-1", "base_sha": base, "candidate_sha": sha,
                  "kg_before_sha256": digest(kg), "pack_before_sha256": digest(pack),
                  "input_sha256": args.input_sha256, "registry_sha256": digest(registry_raw),
                  "span_result_sha256": span_sha, "gate_sha256": document["gate"]["sha256"],
                  "item_span_sha256": {item["id"]: item_span_evidence(item, edge_results)[0] for item in items},
                  "dry_run": dry, "words": [item["id"] for item in items], "links": len(links),
                  "outputs": outputs, "pack_changes": changes, "pack_messages": messages}
        print(json.dumps(report, sort_keys=True, ensure_ascii=True, allow_nan=False))
    except (KeyError, TypeError, AttributeError, OSError, ValueError, RecursionError, subprocess.SubprocessError) as exc:
        cli.exit(2, f"link install: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
