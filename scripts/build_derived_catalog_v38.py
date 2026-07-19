#!/usr/bin/env python3
"""Build or check the private, deterministic V38 derived-game catalog.

The catalog derives two small mechanics from critique-clean V37 Conexiuni boards:

* ``intrusul``: three same-type members of one authored group and one same-type
  foreign tile with no non-distractor link to the trio;
* ``perechi``: one strong pair from each authored group, with no alternative
  strong cross-pair link on the resulting eight-tile board.

Generation is deliberately offline.  At most three diversity-first variants are
kept per source board so a prolific source cannot dominate runtime selection.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from collections import defaultdict
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    DEFAULT_PACK,
    DEFAULT_RANKINGS,
    normalized_text_sha256,
)
from scripts import critique_pack  # noqa: E402

PACKAGE_CATALOG = _ROOT / "cat_de_roman_esti" / "fixtures" / "derived_catalog_v38.json"
TEST_CATALOG = _ROOT / "tests" / "fixtures" / "derived_catalog_v38.json"
CATALOG_COPIES = (PACKAGE_CATALOG, TEST_CATALOG)

DERIVED_GAMES = ("intrusul", "perechi")
SCHEMA_VERSION = 1
FORMULA_VERSION = "v38-derived-1"
MAX_VARIANTS_PER_SOURCE = 3
STRONG_EDGE = 0.60
STARTER_EDGE = 0.70
STARTER_SALIENCE = 0.35

META_FIELDS = (
    "schema_version",
    "formula_version",
    "pack_sha256",
    "kg_sha256",
    "rubric_sha256",
    "v37_rankings_sha256",
    "counts",
)
COUNT_FIELDS = ("total", "by_game", "sources_by_game", "starter_by_game")
BOARD_FIELDS = (
    "id",
    "game",
    "source_id",
    "category",
    "difficulty",
    "romanian_familiarity",
    "play_quality",
    "standard_score",
    "starter_score",
    "starter_eligible",
    "standard_rank",
    "starter_rank",
    "payload",
)


def _bounded_score(value: float) -> int:
    return int(math.floor(max(0.0, min(100.0, float(value))) + 0.5))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _lower_quartile(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[(len(ordered) - 1) // 4] if ordered else 0.0


def _candidate_id(game: str, source_id: str, payload: dict) -> str:
    canonical = json.dumps(
        {"game": game, "source_id": source_id, "payload": payload},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    prefix = "vi" if game == "intrusul" else "vp"
    return f"{prefix}_{hashlib.sha256(canonical).hexdigest()[:20]}"


def _edge_maps(kg: dict) -> tuple[dict[str, dict[str, float]], dict[str, set[str]]]:
    strengths: dict[str, dict[str, float]] = defaultdict(dict)
    linked: dict[str, set[str]] = defaultdict(set)
    for edge in kg.get("kg_edges", []):
        if edge.get("is_distractor"):
            continue
        left = str(edge["src_id"])
        right = str(edge["dst_id"])
        strength = max(0.0, min(1.0, float(edge.get("strength") or 0.0)))
        for source, target in ((left, right), (right, left)):
            linked[source].add(target)
            strengths[source][target] = max(
                strengths[source].get(target, 0.0), strength
            )
    return strengths, linked


def _strength(strengths: dict[str, dict[str, float]], left: str, right: str) -> float:
    return strengths.get(left, {}).get(right, 0.0)


def _visible_ids(candidate: dict) -> tuple[str, ...]:
    payload = candidate["payload"]
    if candidate["game"] == "intrusul":
        return (*payload["members"], payload["intruder"])
    return tuple(node for pair in payload["pairs"] for node in pair["members"])


def _rank_and_cap(candidates: list[dict]) -> list[dict]:
    """Keep at most three variants/source, preferring new concepts before score."""

    by_source: dict[tuple[str, str], list[dict]] = defaultdict(list)
    for candidate in candidates:
        by_source[(candidate["game"], candidate["source_id"])].append(candidate)

    selected: list[dict] = []
    for source_key in sorted(by_source):
        remaining = sorted(by_source[source_key], key=lambda row: row["id"])
        used: set[str] = set()
        source_selected: list[dict] = []
        while remaining and len(source_selected) < MAX_VARIANTS_PER_SOURCE:
            remaining.sort(
                key=lambda row: (
                    -len(set(_visible_ids(row)) - used),
                    -row["standard_score"],
                    -row["play_quality"],
                    -row["romanian_familiarity"],
                    row["id"],
                )
            )
            chosen = remaining.pop(0)
            source_selected.append(chosen)
            selected.append(chosen)
            used.update(_visible_ids(chosen))

    for game in DERIVED_GAMES:
        rows = [row for row in selected if row["game"] == game]
        standard = sorted(rows, key=lambda row: (-row["standard_score"], row["id"]))
        for rank, row in enumerate(standard, 1):
            row["standard_rank"] = rank
        starter = sorted(
            (row for row in rows if row["starter_eligible"]),
            key=lambda row: (-row["starter_score"], row["id"]),
        )
        for rank, row in enumerate(starter, 1):
            row["starter_rank"] = rank

    selected.sort(
        key=lambda row: (DERIVED_GAMES.index(row["game"]), row["standard_rank"])
    )
    return selected


def _base_row(rec: dict, game: str, payload: dict, saliences: list[float]) -> dict:
    if game == "intrusul":
        familiarity = _bounded_score(100 * (0.65 * _mean(saliences) + 0.35 * min(saliences)))
    else:
        familiarity = _bounded_score(
            100
            * (
                0.50 * _mean(saliences)
                + 0.30 * _lower_quartile(saliences)
                + 0.20 * min(saliences)
            )
        )
    row = {
        "id": _candidate_id(game, str(rec["id"]), payload),
        "game": game,
        "source_id": str(rec["id"]),
        "category": str(rec["category"]),
        "difficulty": str(rec["difficulty"]),
        "romanian_familiarity": familiarity,
        "play_quality": 0,
        "standard_score": 0,
        "starter_score": 0,
        "starter_eligible": False,
        "standard_rank": 0,
        "starter_rank": None,
        "payload": payload,
    }
    return row


def _intrusul_candidates(
    records: list[dict], svc, strengths: dict[str, dict[str, float]], linked: dict[str, set[str]]
) -> list[dict]:
    rows: list[dict] = []
    for rec in records:
        groups = rec["groups"]
        labels = rec["group_labels"]
        for group_key in sorted(groups):
            group = sorted(map(str, groups[group_key]))
            for trio in itertools.combinations(group, 3):
                types = {svc.node(node_id).node_type for node_id in trio}
                if len(types) != 1:
                    continue
                inlier_strengths = [
                    _strength(strengths, left, right)
                    for left, right in itertools.combinations(trio, 2)
                ]
                if sum(value >= STRONG_EDGE for value in inlier_strengths) < 2:
                    continue
                for foreign_key in sorted(groups):
                    if foreign_key == group_key:
                        continue
                    for intruder in sorted(map(str, groups[foreign_key])):
                        if svc.node(intruder).node_type not in types:
                            continue
                        if any(intruder in linked.get(member, set()) for member in trio):
                            continue
                        payload = {
                            "members": list(trio),
                            "intruder": intruder,
                            "group_label": str(labels[group_key]),
                        }
                        visible = [*trio, intruder]
                        saliences = [float(svc.node(node_id).salience) for node_id in visible]
                        row = _base_row(rec, "intrusul", payload, saliences)
                        positive = [value for value in inlier_strengths if value >= STRONG_EDGE]
                        cohesion = 100 * (0.60 * _mean(positive) + 0.40 * min(positive))
                        coverage = 100 * len(positive) / 3
                        row["play_quality"] = _bounded_score(
                            0.55 * cohesion + 0.25 * coverage + 20.0
                        )
                        row["standard_score"] = _bounded_score(
                            0.60 * row["romanian_familiarity"]
                            + 0.40 * row["play_quality"]
                        )
                        row["starter_score"] = _bounded_score(
                            0.75 * row["romanian_familiarity"]
                            + 0.25 * row["play_quality"]
                        )
                        row["starter_eligible"] = (
                            min(saliences) >= STARTER_SALIENCE
                            and min(inlier_strengths) >= STARTER_EDGE
                        )
                        rows.append(row)
    return rows


def _perechi_candidates(
    records: list[dict], svc, strengths: dict[str, dict[str, float]]
) -> list[dict]:
    rows: list[dict] = []
    for rec in records:
        groups = rec["groups"]
        labels = rec["group_labels"]
        options: list[list[tuple[str, str, float, str]]] = []
        for group_key in sorted(groups):
            group_options = []
            for left, right in itertools.combinations(sorted(map(str, groups[group_key])), 2):
                strength = _strength(strengths, left, right)
                if strength >= STRONG_EDGE:
                    group_options.append((left, right, strength, group_key))
            options.append(group_options)
        if not all(options):
            continue
        for chosen in itertools.product(*options):
            intended = {frozenset((left, right)) for left, right, _, _ in chosen}
            visible = [node for left, right, _, _ in chosen for node in (left, right)]
            cross_strengths = [
                _strength(strengths, left, right)
                for left, right in itertools.combinations(visible, 2)
                if frozenset((left, right)) not in intended
            ]
            cross_max = max(cross_strengths, default=0.0)
            if cross_max >= STRONG_EDGE:
                continue
            payload = {
                "pairs": [
                    {
                        "members": [left, right],
                        "group_label": str(labels[group_key]),
                    }
                    for left, right, _, group_key in chosen
                ]
            }
            saliences = [float(svc.node(node_id).salience) for node_id in visible]
            intended_strengths = [strength for _, _, strength, _ in chosen]
            association = 100 * (
                0.60 * _mean(intended_strengths) + 0.40 * min(intended_strengths)
            )
            separation = 100 * max(0.0, 1.0 - cross_max / STRONG_EDGE)
            row = _base_row(rec, "perechi", payload, saliences)
            row["play_quality"] = _bounded_score(0.75 * association + 0.25 * separation)
            row["standard_score"] = _bounded_score(
                0.60 * row["romanian_familiarity"] + 0.40 * row["play_quality"]
            )
            row["starter_score"] = _bounded_score(
                0.75 * row["romanian_familiarity"] + 0.25 * row["play_quality"]
            )
            row["starter_eligible"] = (
                min(saliences) >= STARTER_SALIENCE
                and min(intended_strengths) >= STARTER_EDGE
                and cross_max == 0.0
            )
            rows.append(row)
    return rows


def generate_catalog() -> dict:
    pack, svc, _, _ = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG
    )
    rankings = json.loads(DEFAULT_RANKINGS.read_text(encoding="utf-8"))
    eligible_ids = {
        row["id"]
        for row in rankings["boards"]
        if row["game"] == "conexiuni" and row["pilot_eligible"] is True
    }
    records = [rec for rec in pack["conexiuni"] if rec["id"] in eligible_ids]
    if len(records) != 123:
        raise ValueError(f"expected 123 V37-eligible Conexiuni sources, found {len(records)}")
    kg = json.loads(critique_pack.PACKAGE_KG.read_text(encoding="utf-8"))
    strengths, linked = _edge_maps(kg)
    raw_intrusul = _intrusul_candidates(records, svc, strengths, linked)
    raw_perechi = _perechi_candidates(records, svc, strengths)
    if (len(raw_intrusul), len(raw_perechi)) != (800, 9_164):
        raise ValueError(
            "strict derivation count drift: "
            f"intrusul={len(raw_intrusul)}, perechi={len(raw_perechi)}"
        )
    rows = _rank_and_cap([*raw_intrusul, *raw_perechi])
    by_game = {game: sum(row["game"] == game for row in rows) for game in DERIVED_GAMES}
    sources_by_game = {
        game: len({row["source_id"] for row in rows if row["game"] == game})
        for game in DERIVED_GAMES
    }
    starter_by_game = {
        game: sum(row["game"] == game and row["starter_eligible"] for row in rows)
        for game in DERIVED_GAMES
    }
    if by_game != {"intrusul": 183, "perechi": 153}:
        raise ValueError(f"source-balanced cap drift: {by_game}")
    document = {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "formula_version": FORMULA_VERSION,
            "pack_sha256": normalized_text_sha256(DEFAULT_PACK),
            "kg_sha256": normalized_text_sha256(critique_pack.PACKAGE_KG),
            "rubric_sha256": normalized_text_sha256(critique_pack.RUBRIC_PATH),
            "v37_rankings_sha256": normalized_text_sha256(DEFAULT_RANKINGS),
            "counts": {
                "total": len(rows),
                "by_game": by_game,
                "sources_by_game": sources_by_game,
                "starter_by_game": starter_by_game,
            },
        },
        "boards": rows,
    }
    if tuple(document["meta"]) != META_FIELDS:
        raise AssertionError("derived catalog meta schema drifted")
    if tuple(document["meta"]["counts"]) != COUNT_FIELDS:
        raise AssertionError("derived catalog count schema drifted")
    if any(tuple(row) != BOARD_FIELDS for row in rows):
        raise AssertionError("derived catalog row schema drifted")
    return document


def render_catalog(document: dict) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, indent=1, separators=(",", ": ")) + "\n"
    ).encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args((argv or sys.argv)[1:])
    document = generate_catalog()
    expected = render_catalog(document)
    counts = document["meta"]["counts"]
    print(
        f"derived_catalog: {counts['total']} boards "
        f"({counts['by_game']['intrusul']} intrusul / "
        f"{counts['by_game']['perechi']} perechi)"
    )
    if args.write:
        for path in CATALOG_COPIES:
            path.write_bytes(expected)
            print(f"  wrote {path.relative_to(_ROOT)}")
        return 0
    errors = []
    for path in CATALOG_COPIES:
        try:
            actual = path.read_bytes()
        except OSError as exc:
            errors.append(f"cannot read {path.relative_to(_ROOT)}: {exc}")
            continue
        if actual != expected:
            errors.append(f"{path.relative_to(_ROOT)} is stale; run with --write")
    for error in errors:
        print(f"derived_catalog: ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("derived catalog GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
