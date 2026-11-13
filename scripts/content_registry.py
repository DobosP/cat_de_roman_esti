#!/usr/bin/env python3
"""Seed the V4 candidate journal and check current transitions using local inputs only."""

import argparse
import ast
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from datetime import date
from pathlib import Path
from urllib.parse import unquote, urlsplit

SCHEMA = "cat-content-candidate-1"
BASELINE = "1e3a04eb70d58770315be2b65fa22759cb6cfe11"
OWNER_LOG = "docs/adr/0226-content-loop-v4.md"
CURATION_ADR = "docs/adr/0210-curation-waves-and-staged-stock-landing.md"
CURATION_REVIEW = "docs/reviews/content-loop-review-20261022.md"
CURATION_EXCLUSION_MODULES = {
    "scripts/contexto_common_words_v44_data.py",
    "scripts/basic_words_v30_data.py",
    "scripts/basic_words_v32_data.py",
    "scripts/basic_words_v33_data.py",
}
FIXTURES = "cat_de_roman_esti/fixtures"
DRAWING = "continuous/DRAWING_BOARD.md"
LEDGER = "continuous/ledger.jsonl"
BULK = "continuous/intake/bulk-001"
STOCK = "docs/content-stock"
HELD_V2 = f"{STOCK}/held-v2"
ARCHIVE = f"{STOCK}/archive/2026-10-28/source"
SHA256 = re.compile(r"[a-f0-9]{64}")
FIRST_FETCHER = re.compile(r"[a-zA-Z0-9][a-zA-Z0-9_.:-]{0,127}")
BAD_URL_ESCAPE = re.compile(r"%(?![a-fA-F0-9]{2})")
URL_ESCAPE = re.compile(r"%([a-fA-F0-9]{2})")
ESCAPED_URL_PATH = re.compile(r"[a-zA-Z0-9._~!$&'()*+,;=:@%/\[\]-]+")
AMBIGUOUS_PATH_ESCAPE = re.compile(r"%(?:2f|5c|25)", re.IGNORECASE)
UNRESERVED_URL_BYTES = b"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-._~"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
LIVE_SOURCE_HOSTS = {
    "ro.wikipedia.org",
    "ro.wiktionary.org",
    "www.wikidata.org",
    "raw.githubusercontent.com",
    "localhost:8077",
}
DUMP_ARCHIVE = re.compile(
    r"https://dumps\.wikimedia\.org/rowiktionary/([0-9]{8})/"
    r"rowiktionary-\1-pages-articles\.xml\.bz2"
)
KG_PATH = f"{FIXTURES}/kg_sample.json"
KG_BOARD_LANES = {
    "board.alchimie": "A",
    "board.conexiuni": "B",
    "board.contexto": "B",
    "board.lant": "B",
}
# Exact canonical event hashes from c6196077532532fb0a065f96a6185b9baa43f738.
# These historical sourced events predate the S2 receipt check. The prior chain
# and candidate ID are in each digest, so copying a scope or ID grants no exception.
PRE_RECEIPT_SOURCED_EVENTS = frozenset({
    "64b4209f9b9f570584714d53e171ae8383ca99145070e99e4da2a30351f4256e",
    "63ac6bb566b1a1749d89811ddf4a391fa1d02dd9acbccbf4a8e91f71bc190ab6",
    "93f066fbb47365084fe64ced857bba7ca5c507e41108cd559851b959dd40697f",
    "190fbf601e877943f59fcc5a8b429c1ce84917f4ce61ff425201fdcc0d9fadde",
    "a48fdc7f81b2214027a6196d6f744c807759402700d1cb8fc167be9b376147b7",
    "4ed09bbff29fc53f274866f4ff287bfcdd171de67170b5c30a3c30d6a089841b",
    "006eb01039e1e9ef49ea6d41898d9449d8151faf92e34c7ce45802439fb94111",
    "001ddc880b1dac584da045e19d8378bd8cf1c33ada40eec6b0765c91b62ee348",
    "6a8840436ea6a3d34d679db7d2521f78a03e3af330f8b68d3f67c91b08792c75",
    "b4772750d9399861299c7f4492455d145108eee1b4adc808ee9be84156b354de",
    "dd1765a55b79bfbb343a0148b8403f18ac7b4a0328473c2959728c972a02db9e",
    "ec6d84d4c0d25f4b2b06378d18d747142a1d226fc81425846619a2133318ce31",
    "2403c1cb27f9c308c618e9f9080313538e1c31a527e895f48c8586615af707e2",
    "b0206afe67b78df292fa3b7effab5a732df2bbba71ec8a6a479bd23e3dbf64f9",
    "eed575e91d5187e9385e19b559aa8c6dda8950950d6ac699a05a630b16e033f7",
    "fbf0b991fe1336d3d217f0054b9af8237ec2a9ac8f1c956f2dce9b74061d9af7",
    "f30d9f127518da7321d8bbd3ea235b9ab5e3a27617607500e9add94380dbdfac",
    "9b8cca976ac7b6a3f18ae3c507fd7bbfb9be31bb69d7fb86be5f5929ea8f36e6",
    "105aa7b36c20d7a6b98b3de8e74e5aa2f864d939174ac63c5c9daa879d0e2907",
    "ecd988be5cae3b4a6b989a876ecac3a15a70e1d7093ced8fdf45dce830ee8745",
    "e258793ca507e7d1c1ffb6b24f46ff3387fcf0b5dd8d5d88dc227846de0d0e84",
    "27c00caff9351db7c728fcbd3c9657c325bc1b553e6ec7f3c643e67bc094e2ed",
    "ddc8ae8f666a41337463c3ea4d917c19f74321c00abffb73592d4b3a774fbbd0",
    "9a29dddb45baddcc660fb94f7ade20d6e897353bd513270df507287a1dfa1916",
})
# These events name attempt responses whose bytes were verified against the
# canonical final-URL receipts. Preserve only the exact append-only history.
RESPONSE_RECEIPT_SOURCED_EVENTS = frozenset({
    "969a911925db7d64c4cace9164b6825f06035bb49f04f383e08ae2fb3bc4002c",
    "e638cd35586821fd0906bd5b173d519a6d0cf84451834cdf31ef4b1da8a46ce6",
    "38dbb743344efc5dd42c4d7b91485a05d40e73f0597bd879e67fcf6a648ab65e",
    "9f2d7955e15fe885eb50c1a208df2c12cceb1a844af89153e17b4eedde34a900",
    "6cb2009b422cca3693c9c131d1fb75f60561393a54f1bf5f69b3c11d3f013a95",
    "4d0486b381ae0efdc59ab7e49b96ef304b02dc0a2c436dd48c2048415e376955",
    "8663f9062797caa1e792c2fa9357fbf0a7751102fe0f1d81c1465f24a34c71ff",
    "abf52b8863630caee980633f9e5e9fc39fcbb94ce95c9bedd710e123536fe3a1",
    "319fed65958c595fd195341facda0ad2d8a4abc7bab70f69238f0f3ceedc8f09",
    "896709c5b08f9e3da8bc7704cf5dc02d178c2e4bd26e6124652bb909b4adae28",
    "8d18172c8819bb92d35faf20ebc56be20c60b59c42eec04b206b3d2418f40b2c",
    "8fc447e5ce69f61840a99cd4b2d6a73741a492d13026f8aeb8853ed08ab8d86b",
    "7fa182bed058e210f9254666a84cad5870c794ed8dd094f84fb5541c3d0122f7",
})
BOARD_PREFIX = {
    "al": "alchimie",
    "ct": "contexto",
    "cx": "conexiuni",
    "lt": "lant",
    "vi": "intrusul",
    "vp": "perechi",
}
TYPES = {
    "form",
    "synonym",
    "concept",
    "name",
    "edge",
    "alchimie.world",
    "alchimie.extension",
    *(f"board.{game}" for game in BOARD_PREFIX.values()),
}
PIPELINE = ("idea", "screened", "sourced", "authored", "reviewed", "qualified", "landed")
SIDE_STATES = {"rejected", "duplicate", "already_served", "held_recorded", "held_owner"}
STATES = {
    "ACTIVE_UNASSESSED": "idea",
    "SOURCE_NEEDED": "parked(source)",
    "COMPATIBILITY_UNRESOLVED": "parked(screen)",
    "ALREADY_SERVED": "already_served",
    "INACTIVE_ALREADY_SERVED": "already_served",
    "INACTIVE_ALREADY_SERVED_HISTORICAL": "already_served",
    "INACTIVE_HELD": "held_recorded",
    "HELD_RECORDED_EXCLUSION": "held_recorded",
    "INACTIVE_REJECTED": "rejected",
    "idea": "idea",
    "researched": "parked(screen)",
    "selected_for_refinement": "parked(screen)",
    "held": "held_recorded",
    "rejected": "rejected",
    "integrated": "already_served",
}
RETRY_WHEN = {
    "idea": "current_screen_available",
    "parked(source)": "source_prerequisite_satisfied",
    "parked(screen)": "screen_prerequisite_satisfied",
    "held_recorded": "recorded_hold_resolved",
    "held_owner": "never",
    "already_served": "serving_snapshot_changed",
    "rejected": "never",
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def encode(row):
    return json.dumps(
        row, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    )


def expect(condition, message):
    if not condition:
        raise ValueError(message)


def json_pairs(pairs):
    values = {}
    for key, value in pairs:
        expect(key not in values, f"Duplicate JSON key: {key}")
        values[key] = value
    return values


def parse(data):
    return json.loads(data, object_pairs_hook=json_pairs)


class Input:
    def __init__(self, path, data, scope):
        self.path = path
        self.data = data
        self.scope = scope
        self.sha = digest(data)
        self.text = data.decode("utf-8")

    def json(self):
        return parse(self.data)

    def ref(self, line, pointer=None):
        value = {"path": self.path, "line": line, "scope": self.scope, "sha256": self.sha}
        if pointer is not None:
            value["pointer"] = pointer
        return value

    def line(self, fragment):
        position = self.text.find(fragment)
        expect(position >= 0, f"{self.path} is missing expected text {fragment!r}")
        return self.text.count("\n", 0, position) + 1

    def json_line(self, identifier):
        # JSON may encode Romanian text either as Unicode or with escape sequences.
        match = re.search(r'"' + re.escape(identifier) + r'"', self.text)
        if match is None:
            return 1  # The JSON pointer identifies the row exactly.
        return self.text.count("\n", 0, match.start()) + 1


class Landed:
    """Read blobs from the pinned landing tree rather than from a working directory."""

    def __init__(self, repo):
        self.repo = repo
        self.blobs = {}
        paths = ("scripts", "docs/content-pool", STOCK, FIXTURES, CURATION_ADR, CURATION_REVIEW)
        for entry in self.git("ls-tree", "-rz", BASELINE, "--", *paths).split(b"\0"):
            if entry:
                metadata, path = entry.split(b"\t")
                mode, kind, object_id = metadata.decode("ascii").split()
                if mode in ("100644", "100755") and kind == "blob":
                    self.blobs[path.decode("utf-8")] = object_id

    def git(self, *args):
        return subprocess.run(
            ["git", "-C", str(self.repo), *args],
            check=True,
            capture_output=True,
        ).stdout

    def read(self, path):
        return Input(path, self.git("cat-file", "blob", self.blobs[path]), "landed")


class Seed:
    def __init__(self, root):
        self.root = root.resolve(strict=True)
        self.hashes = {}
        for line in (self.root / "SHA256SUMS").read_text(encoding="utf-8").splitlines():
            sha, path = line.split("  ./", 1)
            expect(SHA256.fullmatch(sha) and path not in self.hashes, "Invalid V3 manifest")
            self.hashes[path] = sha

    def read(self, path):
        file = (self.root / path).resolve(strict=True)
        expect(file.is_relative_to(self.root), f"V3 seed path escapes the seed root: {path}")
        expect(file.stat().st_size <= 16 * 1024 * 1024, f"Oversized V3 seed input: {path}")
        source = Input(path, file.read_bytes(), "v3-seed")
        expect(source.sha == self.hashes.get(path), f"V3 seed hash mismatch: {path}")
        return source


def authority_refs(source):
    snippets = {
        "boards": "- The 79 held Conexiuni boards stay held.",
        "sucitoare": "  - no bare *sucitoare*;",
        "ie": "  - Ie never gets *ii*/*iei*;",
        "family": "  - Mănăstire/Sucitor rows only with my explicit go.",
        "names": "  Minors are never name entries. Living persons go to my queue.",
    }
    return {key: f"{source.path}:{source.line(text)}" for key, text in snippets.items()}


def reference_text(ref):
    return f"{ref['path']}:{ref['line']}"


def legacy_ref(ref):
    return {**ref, "fetched_by_role": "legacy"}


def candidate(
    source,
    source_id,
    row_type,
    label,
    raw_state,
    ref,
    *,
    state=None,
    rule=None,
    reason=None,
    owner=None,
    sense=None,
    payload=None,
    lane=None,
):
    state = state or STATES[raw_state]
    label = label or source_id
    holds = []
    if state in {"held_owner", "held_recorded"}:
        holds.append({"kind": state.removeprefix("held_"), "ref": rule or reference_text(ref)})
    default_lanes = {"concept": "L3", "name": "L3", "edge": "L5", "form": "L7", "synonym": "L6"}
    return {
        "schema": SCHEMA,
        "event": "create",
        "id": f"{source}:{source_id}",
        "type": row_type,
        "class": "P" if row_type.startswith(("board.", "alchimie.")) else "G",
        "lane": lane or default_lanes.get(row_type, "L4"),
        "state": state,
        "retry_when": {"predicate": RETRY_WHEN[state], "ref": reference_text(ref)},
        "label_ro": label,
        "identity": {"owner_id": owner, "sense": sense},
        "payload": payload or {},
        "provenance": [legacy_ref(ref)],
        "checks": {"screen": "unassessed", "lint": "unassessed", "derived": "unassessed"},
        "reviews": [],
        "holds": holds,
        "player_benefit": "",
        "origin": {"source": ref, "id": source_id, "state": raw_state, "reason": reason},
    }


def owner_rule(record_id, owner, label, forms):
    rules = {
        "v3-n1-owner-hold-manastire": "family",
        "v3-n1-owner-hold-sucitor": "family",
        "v3-n1-prohibited-ie": "ie",
        "v3-n1-prohibited-bare-sucitoare": "sucitoare",
    }
    if record_id in rules:
        return rules[record_id]

    def key(surface):
        return unicodedata.normalize("NFC", surface).strip().casefold()

    form_keys = {key(form) for form in forms}
    if "sucitoare" in form_keys:
        return "sucitoare"
    label_key = key(label or "")
    if owner in {"n_v2art_manastire", "n_v84_food_sucitor"} or label_key in {
        "mănăstire",
        "sucitor",
    }:
        return "family"
    if (label_key == "ie" or owner == "n_v1_33_ie") and {"ii", "iei"} & form_keys:
        return "ie"
    return None


def lexical_type(kind, record_id):
    if kind in {"new_shared_concept", "new_concept"}:
        return "concept"
    if kind == "new_relation" or record_id in {"v1-2-milk-yogurt", "v1-2-photograph-photo"}:
        return "edge"
    if kind == "new_world_concept":
        return "alchimie.world"
    if kind == "new_round":
        if "outsider" in record_id or record_id == "i06-quick-01":
            return "board.intrusul"
        if "pair" in record_id or "quick" in record_id:
            return "board.perechi"
        return "board.conexiuni"
    if kind in {"label_correction", "label_repair"} or record_id.startswith("i05-repair-"):
        return "name"
    if kind in {
        "selected_sense_lexical_or_qualified_input",
        "verified_synonym",
    } or record_id.startswith("i03-lex-"):
        return "synonym"
    if kind in {
        "accepted_form",
        "accepted_form_family",
        "existing_input_family",
        "existing_owner_form_family",
        "ordinary_NA_GD_morphology_existing_owner",
        "qualified_existing_owner_input_family",
        "regional_input_family",
        None,
    }:
        return "form"
    raise ValueError(f"Unknown source kind {kind!r} on {record_id}")


def archived_stock(landed):
    inventory = f"{ARCHIVE}/docs/content-consolidation/v1-8-through-v1-32/inventory.json"
    late_pools = re.compile(r"docs/content-pool/v1-(?:3[3-9]|4[0-2])-[^/]+/pool\.json")
    paths = [inventory] + sorted(
        path for path in landed.blobs if late_pools.fullmatch(path.removeprefix(f"{ARCHIVE}/"))
    )
    stock = {}
    for path in paths:
        source = landed.read(path)
        for index, record in enumerate(source.json()["records"]):
            record_id = record["id"]
            expect(record_id not in stock, f"Duplicate archived stock ID: {record_id}")
            stock[record_id] = source.ref(source.json_line(record_id), f"/records/{index}")
    return stock


def curation_bindings(landed, declarations):
    adr = landed.read(CURATION_ADR)
    review = landed.read(CURATION_REVIEW)
    blocked = {}
    for declaration in declarations:
        if declaration["source"]["path"] in CURATION_EXCLUSION_MODULES:
            key = declaration["literal"].casefold()
            blocked.setdefault(key, []).append(declaration["source"])
    collision = landed.read("scripts/contexto_common_words_v44_data.py")
    blocked["sofa"].append(collision.ref(collision.line('("sofa", "șofa")')))
    return {
        "hold": adr.ref(adr.line("and leaves out the 10 families")),
        "review": review.ref(review.line("| SC-3 |")),
        "fresh_v133": adr.ref(adr.line("- V1.33 items need fresh research")),
        "blocked": blocked,
    }


def bulk_rows(seed, refs, recorded, stock, curation):
    ledger = seed.read(LEDGER)
    proof_line = ledger.line('"stage":"C2_N5_prior22_historical_author_metadata_rebind_verified"')
    proof_row = parse(ledger.text.splitlines()[proof_line - 1])
    proof_gaps = set(proof_row["unresolved_candidate_ids"])
    expect(
        proof_row["sequence"] == proof_line == 350 and len(proof_gaps) == 2,
        "Unexpected V3 N5 proof-gap binding",
    )
    curation_holds = {}
    v133_parked = 0
    source = seed.read(f"{BULK}/pool.jsonl")
    selection = seed.read(f"{BULK}/wave-001/selection.json")
    selected = {}
    for idx, item in enumerate(selection.json()["targets"]):
        id_ = item["candidate_id"]
        expect(id_ not in selected, f"Repeated N5 selection: {id_}")
        selected[id_] = (
            item["pool_reference"],
            selection.ref(
                selection.json_line(id_),
                f"/targets/{idx}",
            ),
        )
    controller = seed.read("continuous/state.json").json()
    expect(len(selected) == controller["active_wave"]["targets"], "N5 selection count mismatch")

    raw_counts = Counter()
    rows = []
    for line, raw_line in enumerate(source.data.splitlines(keepends=True), 1):
        raw = parse(raw_line)
        original = raw["aggregate_status"]
        raw_counts[original] += 1
        # The retired bulk intake contains one source record per identity. A different shape
        # needs its own conversion so a mixed active/held source row cannot be reopened.
        expect(len(raw["source_records"]) == 1, f"Mixed V3 bulk source scope on line {line}")
        detail = raw["source_records"][0]
        expect(detail["intake_status"] == original, f"V3 status mismatch on line {line}")
        record = detail["record"]
        source_id = record["id"]
        row_type = lexical_type(record.get("kind"), source_id)
        input_kind = detail["provenance"]["input"]
        expect(
            input_kind in {"canonical_stock", "n5_source_free_proposal"},
            f"Unexpected bulk provenance type on line {line}",
        )
        owner = raw["identity"].get("owner_id")
        forms = raw["literal_input_strings"]
        expect(
            isinstance(forms, list) and all(isinstance(x, str) for x in forms),
            f"Invalid forms on line {line}",
        )
        ref = source.ref(line)
        state = STATES[original]
        reason = detail["disposition_reason"]
        label = raw["display_labels_metadata_only"][0]
        hold_rule = owner_rule(source_id, owner, label, forms)
        historical = recorded.get(source_id)
        prior_selection = selected.pop(raw["candidate_id"], None)
        if prior_selection:
            binding, selection_ref = prior_selection
            expect(
                line == binding["line_1based"]
                and digest(raw_line) == binding["line_sha256_including_newline"],
                f"N5 selection binding mismatch on bulk line {line}",
            )
            if state == "idea":
                state = "parked(screen)"
                reason = "V3 N5 selected; exact current disposition and screen must be established."
        retry_ref = None
        if original == "ACTIVE_UNASSESSED" and record.get("wave") == "1.33" and not hold_rule:
            state = "parked(source)"
            reason = "V1.33 captures were lost. Fresh source research is required by ADR-0210."
            retry_ref = curation["fresh_v133"]
            v133_parked += 1
        if raw["candidate_id"] in proof_gaps:
            expect(
                prior_selection and original == "ACTIVE_UNASSESSED",
                f"Unbound N5 proof gap on bulk line {line}",
            )
            proof_gaps.remove(raw["candidate_id"])
            state = "parked(source)"
            reason = "V3 N5 independent source proof remains unresolved for this exact family."
            retry_ref = ledger.ref(proof_line, "/unresolved_candidate_ids")
        matched = []
        if (
            input_kind == "canonical_stock"
            and original == "ACTIVE_UNASSESSED"
            and row_type == "form"
        ):
            for key in sorted({form.casefold() for form in forms}):
                matched.extend(curation["blocked"].get(key, ()))
        if matched:
            curation_holds[source_id] = len(forms)
            state = "held_recorded"
            reason = "ADR-0210 curation hold for the exact proposed family. Owner ruling required."
            historical = {"ref": curation["hold"], "reason": reason}
        if historical and state not in {"already_served", "rejected"}:
            state = "held_recorded"
            reason = historical["reason"]
        if hold_rule:
            state = "held_owner"
        row = candidate(
            "bulk-001",
            raw["candidate_id"],
            row_type,
            label,
            original,
            ref,
            state=state,
            owner=owner,
            sense=raw["identity"].get("selected_sense"),
            reason=reason,
            rule=refs[hold_rule] if hold_rule else historical and reference_text(historical["ref"]),
            payload={"node_id": owner, "forms": forms, "held_forms": record.get("held_forms", [])},
            lane="L2",
        )
        row["origin"]["record_id"] = source_id
        row["origin"]["record_source"] = detail["source_record_id"]
        if input_kind == "canonical_stock":
            row["provenance"].append(legacy_ref(stock.pop(source_id)))
        if raw["identity"].get("unresolved_record_scope"):
            row["identity"]["unresolved_record_scope"] = raw["identity"]["unresolved_record_scope"]
        if prior_selection:
            row["provenance"].append(legacy_ref(selection_ref))
        if historical:
            row["provenance"].append(legacy_ref(historical["ref"]))
        if retry_ref:
            row["retry_when"]["ref"] = reference_text(retry_ref)
            row["provenance"].append(legacy_ref(retry_ref))
        if matched:
            row["retry_when"] = {
                "predicate": "owner_answer",
                "ref": reference_text(curation["review"]),
            }
            row["provenance"].extend(legacy_ref(ref) for ref in [curation["review"], *matched])
        rows.append(row)

    expect(not proof_gaps and v133_parked == 29, "V3 source prerequisite count mismatch")
    expect(
        len(curation_holds) == 10 and sum(curation_holds.values()) == 62,
        "ADR-0210 scoped hold accounting mismatch",
    )
    expected = controller["intake"]
    expect(source.sha == expected["pool_sha256"], "Bulk input disagrees with V3 state digest")
    expect(
        raw_counts
        == {
            "ACTIVE_UNASSESSED": expected["active_unassessed"],
            "INACTIVE_HELD": expected["held_inactive"],
            "INACTIVE_ALREADY_SERVED_HISTORICAL": expected["historically_integrated_inactive"],
            "INACTIVE_REJECTED": expected["rejected_inactive"],
        }
        and not selected
        and not stock
        and len(rows) == expected["targets"],
        "Bulk seed accounting mismatch",
    )
    return rows


def form_payload(record, novelty):
    for container, field in (
        (novelty, "forms"),
        (record, "proposed_aliases"),
        (record, "proposed_forms"),
        (record, "verified_forms"),
        (record, "planned_forms"),
        (record, "prohibited_forms"),
    ):
        values = container.get(field)
        if isinstance(values, list) and all(isinstance(value, str) for value in values):
            return values
    return []


def pool_rows(landed, refs, recorded, counts):
    for path in sorted(landed.blobs):
        if not (
            path.startswith("docs/content-pool/")
            and path.endswith("/pool.json")
            or path in {f"{HELD_V2}/c1/proposal.json", f"{HELD_V2}/c2/proposal.json"}
        ):
            continue
        source = landed.read(path)
        section = "records" if path.endswith("/pool.json") else "items"
        theme = Path(path).parent.name
        data = source.json()
        if section == "items":
            expect(len(data[section]) == data["families"], f"V2 family count mismatch: {path}")
        counts["pools" if section == "records" else "v2-proposals"] += len(data[section])
        for idx, record in enumerate(data[section]):
            record_id = record["id"]
            ref = source.ref(source.json_line(record_id), f"/{section}/{idx}")
            novelty = record.get("novelty") or {}
            kind = record.get("kind", novelty.get("kind") if isinstance(novelty, dict) else novelty)
            novelty = novelty if isinstance(novelty, dict) else {}
            label = record.get("label_ro", record.get("label"))
            owner = (
                record.get("owner_id")
                or record.get("node_id")
                or novelty.get("existing_owner_id")
                or novelty.get("proposed_node_id")
            )
            forms = form_payload(record, novelty)
            raw_state = record.get("state", "held")
            state = STATES[raw_state]
            if theme.startswith("v3-n") and raw_state == "selected_for_refinement":
                state = "already_served"  # The n1/n2/n4 local landing is in the pinned baseline.
            historical = recorded.get(record_id)
            reason = record.get("decision") or record.get("reason") or record.get("next_action")
            rule = None
            if historical and state not in {"already_served", "rejected"}:
                state, rule = "held_recorded", reference_text(historical["ref"])
            owner_hold = owner_rule(record_id, owner, label, forms)
            if owner_hold:
                state, rule = "held_owner", refs[owner_hold]
            row = candidate(
                f"pool.{theme}" if section == "records" else f"v2.{theme}",
                record_id,
                lexical_type(kind, record_id),
                label,
                raw_state,
                ref,
                state=state,
                reason=reason,
                owner=owner,
                sense=record.get("sense") or record.get("sense_hypothesis"),
                rule=rule,
                payload={"node_id": owner, "forms": forms},
            )
            if record.get("lemma"):
                row["lemma"] = record["lemma"]
            benefit = record.get("player_benefit") or record.get("playerBenefit")
            if isinstance(benefit, str):
                row["player_benefit"] = benefit
            if historical:
                row["provenance"].append(legacy_ref(historical["ref"]))
            yield row


def drawing_rows(seed):
    source = seed.read(DRAWING)
    ledger = seed.read(LEDGER)
    rows = []
    recorded = {}
    for line, text in enumerate(source.text.splitlines(), 1):
        if text.startswith("| `prospect_"):
            _, raw_id, game, step, reason, _proof, _ = text.split("|")
            record_id = raw_id.strip().strip("`")
            rows.append(
                candidate(
                    "v3-drawing",
                    record_id,
                    f"board.{game.strip().lower()}",
                    record_id,
                    "INACTIVE_HELD",
                    source.ref(line),
                    reason=f"{step.strip()}: {reason.strip()}",
                )
            )
        elif text.startswith("| `v115-") or re.match(r"^\| [^|]+\(`v1\d+-", text):
            record_id = re.search(r"`(v1\d+-[a-z_]+)`", text).group(1)
            fields = [field.strip() for field in text.strip("|").split("|")]
            label = fields[1] if fields[0].startswith("`") else fields[0]
            reason = fields[2]
            recorded[record_id] = {"ref": source.ref(line), "reason": reason}
            rows.append(
                candidate(
                    "v3-drawing",
                    record_id,
                    "form",
                    label.split(" (`")[0],
                    "INACTIVE_HELD",
                    source.ref(line),
                    reason=reason,
                    lane="L2",
                )
            )
    expect(
        len([row for row in rows if row["type"].startswith("board.")]) == 12
        and len(recorded) == 12,
        "V3 drawing board table count mismatch",
    )

    for record_id, label, row_type, marker, reason in (
        (
            "v141-cereala",
            "Cereală",
            "concept",
            "- Cereală (",
            "Cald projection key Cereale; native resolution required.",
        ),
        (
            "v141-colaj",
            "Colaj",
            "concept",
            "- Colaj (",
            "Cald projection key Colaj; native resolution required.",
        ),
        (
            "n6-cratita",
            "Cratiță",
            "form",
            "- **Cratiță",
            "N6 family held under recorded v30 exclusion.",
        ),
        (
            "n5-research-n_v2art_teatru",
            "Teatru",
            "form",
            "- **Teatru**",
            "Selected theatrical-art sense lacks whole-family plural/table evidence.",
        ),
        (
            "v142-rulada",
            "Ruladă",
            "concept",
            "Ruladă (`v142-rulada`) is a separate",
            "Prior Alchimie projection audit refused; no native or C4 pass.",
        ),
        (
            "v142-glazura",
            "Glazură",
            "concept",
            "- **B12 Glazură**",
            "Blind Cald failed on opener, final guess and ambiguous target.",
        ),
        (
            "v2-b5-panta",
            "Pantă",
            "board.alchimie",
            "- B5 Alchimie: Pantă held",
            "Ambiguous target in V2 B5.",
        ),
    ):
        ref = source.ref(source.line(marker))
        recorded[record_id] = {"ref": ref, "reason": reason}
        rows.append(
            candidate("v3-drawing", record_id, row_type, label, "INACTIVE_HELD", ref, reason=reason)
        )

    ref = ledger.ref(ledger.line('"stage":"C4_NON_CALD_COMPARE_CLOSEOUT_CARRY_RULADA"'))
    for record_id, label in (
        ("v141-vesela", "Veselă"),
        ("v142-fosila", "Fosilă"),
        ("v142-felie", "Felie"),
    ):
        reason = "V3 N3 retained whole-family hold after blind comparison."
        recorded[record_id] = {"ref": ref, "reason": reason}
        rows.append(
            candidate(
                "n3",
                record_id,
                "concept",
                label,
                "INACTIVE_HELD",
                ref,
                reason=reason,
            )
        )
    ref = source.ref(source.line("- **C1 failed novelty"))
    for record_id in ("v140-pix", "v140-frate", "v140-fiu"):
        recorded[record_id] = {
            "ref": ref,
            "reason": "Excluded from V3 N1 scope after C1 source-novelty failure.",
        }
    ref = ledger.ref(ledger.line('"stage":"N7_PERECHI_THREE_STATIC_AUTHOR_DIAGNOSTIC"'))
    for record_id in parse(ledger.text.splitlines()[ref["line"] - 1])["prospect_ids"]:
        rows.append(
            candidate(
                "n7",
                record_id,
                "board.perechi",
                record_id,
                "COMPATIBILITY_UNRESOLVED",
                ref,
                reason="V3 author-only diagnostic. Native eligibility and review unresolved.",
            )
        )
    return rows, recorded


def lexical_exclusions(landed):
    entries = []
    for path in sorted(landed.blobs):
        if not re.fullmatch(r"scripts/[^/]+_data\.py", path):
            continue
        source = landed.read(path)
        for statement in ast.parse(source.text, filename=path).body:
            if isinstance(statement, ast.Assign):
                targets = statement.targets
            elif isinstance(statement, ast.AnnAssign):
                targets = [statement.target]
            else:
                continue
            for target in targets:
                if not isinstance(target, ast.Name) or not (
                    target.id == "BLOCKED_ALIAS_FORMS" or target.id.startswith("DEFERRED_")
                ):
                    continue
                if not isinstance(statement.value, (ast.Tuple, ast.List, ast.Set)):
                    continue  # A reference/filter declares no new literal exclusion.
                for node in statement.value.elts:
                    if isinstance(node, ast.Constant) and isinstance(node.value, str):
                        entries.append(
                            {
                                "literal": node.value,
                                "constant": target.id,
                                "source": source.ref(node.lineno),
                            }
                        )
    return entries


def board_controls(landed, refs):
    def fixture(name):
        return landed.read(f"{FIXTURES}/{name}.json")

    demotions = fixture("board_demotions_v43")
    reserves = fixture("release_reserve_v1")
    demoted_ids = demotions.json()["ids"]
    release = reserves.json()
    reserve_ids = release["ids"]
    cx_demoted = {id_ for id_ in demoted_ids if id_.startswith("cx_")}
    cx_reserved = {id_ for id_ in reserve_ids if id_.startswith("cx_")}
    cx_quick_sources = {
        row["source_id"] for row in release["quick"] if row["source_id"].startswith("cx_")
    }
    protected = cx_demoted | cx_reserved | cx_quick_sources
    expect(
        len(cx_demoted) == 75 and len(cx_reserved | cx_quick_sources) == 5 and len(protected) == 79,
        "Owner-held Conexiuni membership no longer matches the seed",
    )

    controls = {}
    for file, ids, section, reason in (
        (demotions, demoted_ids, "ids", "Landed board demotion"),
        (reserves, reserve_ids, "ids", "Landed release reserve"),
        (reserves, [r["id"] for r in release["quick"]], "quick", "Landed quick-game reserve"),
    ):
        for idx, id_ in enumerate(ids):
            ref = file.ref(file.json_line(id_), f"/{section}/{idx}")
            controls.setdefault(id_, []).append((ref, reason))
    for idx, row in enumerate(release["quick"]):
        id_ = row["source_id"]
        if id_ in protected:
            ref = reserves.ref(reserves.line(f'"id": "{row["id"]}"'), f"/quick/{idx}/source_id")
            controls.setdefault(id_, []).append((ref, "Quick release reserve source dependency"))

    for name in ("contexto_demotions_v44", "contexto_impact_reserve_v69"):
        file = fixture(name)
        for idx, id_ in enumerate(file.json()["ids"]):
            ref = file.ref(file.json_line(id_), f"/ids/{idx}")
            controls.setdefault(id_, []).append((ref, "Landed Cald demotion or impact reserve"))

    rows = []
    for id_, bindings in sorted(controls.items()):
        ref, reason = bindings[0]
        row = candidate(
            "board-control",
            id_,
            f"board.{BOARD_PREFIX[id_.split('_')[0]]}",
            id_,
            "INACTIVE_HELD",
            ref,
            state="held_owner" if id_ in protected else "held_recorded",
            reason=reason,
            rule=refs["boards"] if id_ in protected else None,
            payload={"board_id": id_},
        )
        row["provenance"].extend(legacy_ref(extra) for extra, _ in bindings[1:])
        rows.append(row)

    for game in ("conexiuni", "lant"):
        file = fixture(f"{game}_rejection_tombstones")
        data = file.json()
        expect(len(data["items"]) == data["meta"]["count"], f"Stale tombstone count: {game}")
        for id_, tombstone in sorted(data["items"].items()):
            rows.append(
                candidate(
                    "tombstone",
                    id_,
                    f"board.{game}",
                    id_,
                    "rejected",
                    file.ref(file.json_line(id_), f"/items/{id_}"),
                    reason="Landed rejection retained for novelty",
                    payload={
                        "board_id": id_,
                        "record_sha256": tombstone["record_sha256"],
                    },
                )
            )
    return rows, sorted(protected)


def seed_registry(landed, seed, owner_log):
    refs = authority_refs(owner_log)
    drawn, recorded = drawing_rows(seed)
    stock = archived_stock(landed)
    stock_count = len(stock)
    declarations = lexical_exclusions(landed)
    bulk = bulk_rows(seed, refs, recorded, stock, curation_bindings(landed, declarations))
    inputs = Counter()
    pools = list(pool_rows(landed, refs, recorded, inputs))
    boards, protected = board_controls(landed, refs)
    inputs.update(
        {
            "bulk-001": len(bulk),
            "drawing-and-ledger": len(drawn),
            "unique-board-controls-and-tombstones": len(boards),
        }
    )
    rows = bulk + pools + drawn + boards
    expect(len(current_rows(rows)) == sum(inputs.values()), "Registry in/out count mismatch")
    expect(
        {
            row["origin"]["id"]
            for row in rows
            if row["state"] == "held_owner" and row["type"] == "board.conexiuni"
        }
        == set(protected),
        "Owner board hold drift",
    )
    exclusions = {
        "schema": "cat-content-exclusions-1",
        "landed_ref": BASELINE,
        "lexical_declarations": declarations,
        "board_controls": [
            {"id": row["origin"]["id"], "state": row["state"], "source": row["origin"]["source"]}
            for row in boards
        ],
        "owner_held_conexiuni": protected,
        "owner_rules": {
            "conexiuni_hold": {"ref": refs["boards"], "ids": protected},
            "bare_sucitoare": {"ref": refs["sucitoare"], "forms": ["sucitoare"]},
            "ie": {"ref": refs["ie"], "label_ro": "Ie", "forms": ["ii", "iei"]},
            "held_families": {
                "ref": refs["family"],
                "labels_ro": ["Mănăstire", "Sucitor"],
                "requires": "explicit_owner_go",
            },
            "names": {"ref": refs["names"], "minor": "excluded", "living_person": "owner_queue"},
        },
    }
    counts = {
        "inputs": inputs,
        "in": sum(inputs.values()),
        "out": len(rows),
        "states": dict(Counter(row["state"] for row in rows)),
        "archived_stock_crosswalk": stock_count,
        "lexical_declarations": len(exclusions["lexical_declarations"]),
        "conexiuni_owner_holds": len(protected),
    }
    return rows, exclusions, counts


def read_journal(path):
    with path.open("rb") as stream:
        for line, raw in enumerate(stream, 1):
            expect(raw.endswith(b"\n"), f"Unterminated journal row at line {line}")
            yield parse(raw)


def validate_record(row):
    expect(
        row["schema"] == SCHEMA and isinstance(row["id"], str) and row["id"],
        "Invalid candidate schema or id",
    )
    expect(row["type"] in TYPES, f"Unknown candidate type: {row['type']}")
    expected_class = "P" if row["type"].startswith(("board.", "alchimie.")) else "G"
    expect(row["class"] == expected_class, f"Invalid class for {row['id']}")
    state = row["state"]
    expect(
        state in PIPELINE
        or state in SIDE_STATES
        or re.fullmatch(r"(?:parked|retracted)\([^()\n]+\)", state),
        f"Unknown state on {row['id']}: {state}",
    )
    for field in ("identity", "payload", "checks", "origin"):
        expect(isinstance(row[field], dict), f"Invalid {field}: {row['id']}")
    for field in ("provenance", "reviews", "holds"):
        expect(isinstance(row[field], list), f"Invalid {field}: {row['id']}")
    for field in ("label_ro", "lane", "player_benefit"):
        expect(isinstance(row[field], str), f"Invalid {field}: {row['id']}")
    retry = row["retry_when"]
    expect(
        isinstance(retry, dict) and isinstance(retry.get("predicate"), str) and retry["predicate"],
        f"Missing retry predicate on {row['id']}",
    )
    if state in {"held_recorded", "held_owner"}:
        expect(
            any(
                hold["kind"] == state.removeprefix("held_")
                and re.fullmatch(r".+:[1-9][0-9]*", hold["ref"])
                for hold in row["holds"]
            ),
            f"Missing line binding for {state}: {row['id']}",
        )
    if state == "held_owner":
        expect(retry["predicate"] == "never", f"Retry on owner hold: {row['id']}")
    if row["event"] == "create":
        expect(
            state not in PIPELINE[1:] and not state.startswith("retracted("),
            f"New candidate cannot start in an advanced state: {row['id']}",
        )
        if row["origin"]["source"]["scope"] in {"v3-seed", "landed"}:
            expect(
                not row["reviews"]
                and all(ref["fetched_by_role"] == "legacy" for ref in row["provenance"]),
                f"Imported evidence cannot confer approval: {row['id']}",
            )


def has_retry_evidence(prior, event, evidence_root):
    prerequisite = prior["retry_when"]
    if evidence_root is None or prerequisite["predicate"] in {"owner_answer", "never"}:
        return False
    evidence = event.get("retry_evidence")
    if not isinstance(evidence, dict) or evidence.get("prerequisite") != prerequisite:
        return False
    ref, sha = evidence.get("ref"), evidence.get("sha256")
    if not isinstance(ref, str) or not isinstance(sha, str):
        return False
    match = re.fullmatch(r"([^:\\\x00\r\n]+):([1-9][0-9]*)", ref)
    if match is None or not SHA256.fullmatch(sha) or sha == "0" * 64:
        return False
    name, line = match.groups()
    if any(part in {"", ".", ".."} for part in name.split("/")):
        return False
    path = evidence_root / name
    try:
        if path.resolve(strict=True) != path or not path.is_file():
            return False
        if path.stat().st_size > 16 * 1024 * 1024:
            return False
        data = path.read_bytes()
        if digest(data) != sha:
            return False
        receipt = parse(data.splitlines()[int(line) - 1])
    except (IndexError, OSError, RuntimeError, ValueError):
        return False
    return isinstance(receipt, dict) and all(
        receipt.get(key) == value
        for key, value in {
            "candidate_id": prior["id"],
            "prerequisite": prerequisite,
            "previous_sha256": event["previous_sha256"],
            "verdict": "resolved",
        }.items()
    )


def receipt_hash(value):
    return (
        isinstance(value, str)
        and SHA256.fullmatch(value) is not None
        # Repeated halves include the usual zero and repeated-character placeholders.
        and value[:32] != value[32:]
        and value != EMPTY_SHA256
    )


def live_source_receipt(ref):
    url = ref.get("url")
    path = ref.get("path")
    if (
        not isinstance(url, str)
        or re.fullmatch(r"https://[!-~]+", url) is None
        or len(url) > 4096
        or any(char in url for char in "#\\")
        or BAD_URL_ESCAPE.search(url) is not None
        or any(
            octet != octet.upper() or int(octet, 16) in UNRESERVED_URL_BYTES
            for octet in URL_ESCAPE.findall(url)
        )
        or not isinstance(path, str)
        or any(char in path for char in "\x00\r\n")
        or re.split(r"[/\\]", path)[-1] != f"{digest(url.encode('ascii'))}.receipt.json"
        or not receipt_hash(ref.get("sha256"))
        or not receipt_hash(ref.get("body_sha256"))
        or ref["sha256"] == ref["body_sha256"]
    ):
        return False
    try:
        source = urlsplit(url)
        decoded_path = unquote(source.path, errors="strict")
    except ValueError:
        return False
    segments = decoded_path.split("/")
    # Match Go's per-rune lowercase mapping for dotted capital I.
    folded_path = decoded_path.replace("İ", "i").lower()
    # These paths are policy-only in the source client.
    terms_path = folded_path in {"/terms", "/terms-of-service", "/terms-of-use"} or folded_path.startswith(
        ("/wiki/wikipedia:termeni", "/wiki/wikționar:termeni", "/wiki/wikidata:terms_of_use")
    )
    if (
        source.netloc not in LIVE_SOURCE_HOSTS
        or decoded_path in {"", "/", "/robots.txt"}
        or terms_path
        or ESCAPED_URL_PATH.fullmatch(source.path) is None
        or (url.endswith("?") and not source.query)
        or "//" in decoded_path
        or any(segment in {".", ".."} for segment in segments)
        or any(ord(char) < 32 or ord(char) == 127 for char in decoded_path)
        or AMBIGUOUS_PATH_ESCAPE.search(source.path) is not None
    ):
        return False
    if source.netloc == "raw.githubusercontent.com":
        return (
            len(segments) >= 5
            and segments[1:3] == ["hermitdave", "FrequencyWords"]
            and bool(segments[-1])
            and "%" not in source.path
            and not source.query
        )
    return True


def dump_page_receipt(ref):
    url, title, revision = ref.get("archive_url"), ref.get("title"), ref.get("revision_id")
    archive = DUMP_ARCHIVE.fullmatch(url) if isinstance(url, str) else None
    if archive is None:
        return False
    try:
        if date.fromisoformat(archive[1]).year < 2001:
            return False
    except ValueError:
        return False
    hashes = [ref.get(key) for key in ("archive_receipt_sha256", "archive_sha256", "text_sha256")]
    return (
        ref.get("fetched_by_role") == "script"
        and isinstance(title, str)
        and bool(title.strip())
        and all(ord(char) >= 32 for char in title)
        and type(revision) is int
        and revision > 0
        and all(receipt_hash(sha) for sha in hashes)
        and len(set(hashes)) == 3
    )


def kg_board_receipt(ref, event, evidence_root):
    commit = ref.get("commit")
    origin = event["origin"]
    if (
        evidence_root is None
        or KG_BOARD_LANES.get(event["type"]) != event["lane"]
        or "model" in (origin.get("kind"), origin.get("state"))
        or origin["source"].get("scope") == "model"
        or set(ref) != {"scope", "fetched_by_role", "path", "commit", "sha256"}
        or ref.get("fetched_by_role") != "script"
        or ref.get("path") != KG_PATH
        or not isinstance(commit, str)
        or re.fullmatch(r"[a-f0-9]{40}", commit) is None
        or not receipt_hash(ref.get("sha256"))
    ):
        return False
    git = ["git", "--no-replace-objects", "-C", str(evidence_root)]
    # Resolve the actual checkout and its objects without caller Git overrides.
    env = {key: value for key, value in os.environ.items() if not key.startswith("GIT_")}
    env.update(
        GIT_ALLOW_PROTOCOL="",
        GIT_CONFIG_GLOBAL=os.devnull,
        GIT_CONFIG_NOSYSTEM="1",
        GIT_NO_LAZY_FETCH="1",
    )
    try:
        top = subprocess.check_output(
            [*git, "rev-parse", "--show-toplevel"], stderr=subprocess.DEVNULL, env=env,
        )
        if Path(os.fsdecode(top.removesuffix(b"\n"))).resolve(strict=True) != evidence_root:
            return False
        resolved = subprocess.check_output(
            [*git, "rev-parse", "--verify", f"{commit}^{{commit}}"],
            stderr=subprocess.DEVNULL, env=env,
        )
        if resolved.strip() != commit.encode("ascii"):
            return False
        entry = subprocess.check_output(
            [*git, "ls-tree", commit, "--", KG_PATH], stderr=subprocess.DEVNULL, env=env,
        )
        match = re.fullmatch(
            rb"100644 blob ([a-f0-9]{40})\t" + re.escape(KG_PATH.encode()) + rb"\n", entry,
        )
        if match is None:
            return False
        data = subprocess.check_output(
            [*git, "cat-file", "blob", match[1].decode("ascii")],
            stderr=subprocess.DEVNULL, env=env,
        )
    except (OSError, subprocess.CalledProcessError):
        return False
    return digest(data) == ref["sha256"]


def has_source_receipt(event, new_provenance, evidence_root):
    for ref in new_provenance:
        if not isinstance(ref, dict):
            continue
        if ref.get("scope") == "kg-only":
            if kg_board_receipt(ref, event, evidence_root):
                return True
            continue
        fetcher = ref.get("first_fetcher")
        if (
            ref.get("first_fetch_origin") == "v5"
            and ref.get("origin", "v5") == "v5"
            and isinstance(ref.get("scope", ""), str)
            and ref.get("scope") not in ("model", "legacy")
            and ref.get("fetched_by_role") in ("script", "factual", "quality", "critic")
            and isinstance(fetcher, str)
            and FIRST_FETCHER.fullmatch(fetcher)
            and type(ref.get("status", 200)) is int
            and ref.get("status", 200) == 200
            and ref.get("body_problem", "") == ""
            and "dump_failure" not in ref
            and (dump_page_receipt(ref) if "archive_url" in ref else live_source_receipt(ref))
        ):
            return True
    event_sha = digest(encode(event).encode("utf-8"))
    return (
        event_sha in PRE_RECEIPT_SOURCED_EVENTS or event_sha in RESPONSE_RECEIPT_SOURCED_EVENTS
    )


def current_rows(events, evidence_root=None):
    if evidence_root is not None:
        evidence_root = evidence_root.resolve(strict=True)
        expect(evidence_root.is_dir(), "Trusted evidence root must be a directory")
    rows = {}
    for event in events:
        validate_record(event)
        id_ = event["id"]
        prior = rows.get(id_)
        if event["event"] == "create":
            expect(prior is None, f"Duplicate candidate id: {id_}")
        else:
            expect(event["event"] == "transition" and prior is not None, f"Invalid event for {id_}")
            expect(prior["state"] != "held_owner", f"Owner hold is locked: {id_}")
            expect(
                event["previous_sha256"] == digest(encode(prior).encode("utf-8")),
                f"Transition predecessor mismatch: {id_}",
            )
            for field in ("identity", "type", "class", "lane", "origin"):
                expect(prior[field] == event[field], f"Transition changed {field}: {id_}")
            old_provenance = prior["provenance"]
            expect(
                event["provenance"][: len(old_provenance)] == old_provenance,
                f"Transition rewrote provenance: {id_}",
            )
            before, after = prior["state"], event["state"]
            if after in PIPELINE[1:]:
                expect(
                    before == PIPELINE[PIPELINE.index(after) - 1],
                    f"Transition skipped a gate: {id_} ({before} → {after})",
                )
            if after == "sourced":
                added = event["provenance"][len(old_provenance):]
                expect(
                    has_source_receipt(event, added, evidence_root),
                    f"Sourced transition needs a source-client, dump or eligible KG receipt: {id_}",
                )
            retry_state = before in {"held_recorded", "already_served"} or before.startswith(
                "parked("
            )
            if retry_state:
                if after == before:
                    expect(
                        prior["retry_when"] == event["retry_when"]
                        and prior["holds"] == event["holds"],
                        f"Transition rewrote a retry prerequisite: {id_}",
                    )
                else:
                    expect(
                        after == "idea" and has_retry_evidence(prior, event, evidence_root),
                        f"Release from {before} needs exact retry evidence: {id_}",
                    )
            if before == "landed":
                expect(after.startswith("retracted("), f"Landed row must be retracted: {id_}")
            if before in {"rejected", "duplicate"} or before.startswith("retracted("):
                expect(after == before, f"Terminal candidate must keep its disposition: {id_}")
        rows[id_] = event
    return rows


def write_seed(output, rows, exclusions):
    expect(not output.exists(), f"Seed output already exists: {output}")
    # Make both complete files visible together. The orchestrator is the only writer.
    with tempfile.TemporaryDirectory(prefix=".content-registry-", dir=output.parent) as temp:
        stage = Path(temp) / "output"
        stage.mkdir()
        with (stage / "registry.jsonl").open("wb") as stream:
            for row in rows:
                stream.write((encode(row) + "\n").encode("utf-8"))
        expect(
            current_rows(read_journal(stage / "registry.jsonl")) == current_rows(rows),
            "Registry JSONL round-trip mismatch",
        )
        (stage / "exclusions.json").write_bytes(
            (json.dumps(exclusions, ensure_ascii=False, sort_keys=True, indent=2) + "\n").encode(
                "utf-8"
            ),
        )
        stage.rename(output)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    seed_parser = sub.add_parser("seed", help="convert the pinned V3 seed into a new directory")
    for flag in ("--repo", "--seed", "--output"):
        seed_parser.add_argument(flag, type=Path, required=True)
    seed_parser.add_argument("--owner-log", type=Path)
    check = sub.add_parser("check", help="validate journal and count current states")
    view = sub.add_parser("view", help="emit one current row per candidate")
    for command in (check, view):
        command.add_argument("journal", type=Path)
        command.add_argument(
            "--evidence-root", type=Path, help="trusted retry and KG evidence root"
        )
    view.add_argument("--state")
    args = parser.parse_args(argv)
    try:
        if args.command == "seed":
            owner_path = args.owner_log or args.repo / OWNER_LOG
            owner = Input(OWNER_LOG, owner_path.read_bytes(), "owner-log")
            rows, exclusions, counts = seed_registry(Landed(args.repo), Seed(args.seed), owner)
            write_seed(args.output, rows, exclusions)
            print(encode(counts))
        else:
            rows = current_rows(read_journal(args.journal), args.evidence_root)
            if args.command == "check":
                print(
                    encode(
                        {
                            "current": len(rows),
                            "states": Counter(row["state"] for row in rows.values()),
                        }
                    )
                )
            else:
                sys.stdout.reconfigure(encoding="utf-8")
                for row in rows.values():
                    if args.state is None or row["state"] == args.state:
                        print(encode(row))
    except (
        KeyError,
        TypeError,
        AttributeError,
        ValueError,
        OSError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"content-registry: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
