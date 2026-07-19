#!/usr/bin/env python3
"""Build or check the deterministic V37 editorial board-ranking sidecar.

The score is an offline, pre-playtest priority estimate.  It combines a Romanian
familiarity proxy derived from the KG's salience field with bounded, game-specific
evidence already present in critique dossiers.  It never changes review status:
``pilot_eligible`` additionally requires an approved, payload-valid record with no
deterministic critique FAIL.

By default this command is read-only and checks both committed sidecar copies::

    PYTHONPATH=. python scripts/rank_games_pack.py

Regeneration is explicit::

    PYTHONPATH=. python scripts/rank_games_pack.py --write
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from collections.abc import Callable
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cat_de_roman_esti.wordgames.packs import (  # noqa: E402
    GAME_KINDS,
    STATUSES,
    validate_payload,
)
from cat_de_roman_esti.wordgames.service import WordGameService  # noqa: E402
from scripts import critique_pack  # noqa: E402

PACKAGE_RANKINGS = (
    _REPO_ROOT / "cat_de_roman_esti" / "fixtures" / "board_rankings_v37.json"
)
TESTS_RANKINGS = _REPO_ROOT / "tests" / "fixtures" / "board_rankings_v37.json"
RANKING_COPIES = (PACKAGE_RANKINGS, TESTS_RANKINGS)

SCHEMA_VERSION = 1
META_FIELDS = (
    "schema_version",
    "pack_sha256",
    "kg_sha256",
    "rubric_sha256",
    "counts",
)
COUNT_FIELDS = (
    "total",
    "approved",
    "pilot_eligible",
    "by_game",
    "eligible_by_game",
)
BOARD_FIELDS = (
    "id",
    "game",
    "status",
    "romanian_familiarity",
    "play_quality",
    "pilot_score",
    "rank",
    "pilot_eligible",
    "selection_weight",
)


def _bounded_score(value: float) -> int:
    """Clamp to 0..100 and round halves up, independent of Python's banker rounding."""

    bounded = max(0.0, min(100.0, float(value)))
    return int(math.floor(bounded + 0.5))


def _mean(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def _node_score(node: dict, salience_for: Callable[[str], float]) -> float:
    raw = node.get("salience")
    if isinstance(raw, int | float) and not isinstance(raw, bool):
        salience = float(raw)
    else:
        salience = salience_for(str(node.get("id") or ""))
    return max(0.0, min(100.0, 100.0 * salience))


def _unique_nodes(nodes: list[dict]) -> list[dict]:
    unique: dict[str, dict] = {}
    for node in nodes:
        node_id = str(node.get("id") or "")
        if node_id:
            unique.setdefault(node_id, node)
    return [unique[node_id] for node_id in sorted(unique)]


def romanian_familiarity(
    game: str,
    dossier: dict,
    salience_for: Callable[[str], float],
) -> int:
    """Romanian-familiarity proxy from only KG salience carried by dossier concepts."""

    if game == "conexiuni":
        groups = [
            [_node_score(member, salience_for) for member in group.get("members", [])]
            for group in dossier.get("groups", [])
        ]
        all_nodes = [score for group in groups for score in group]
        if not all_nodes:
            return 0
        ordered = sorted(all_nodes)
        lower_quartile = ordered[(len(ordered) - 1) // 4]
        best_group = max((_mean(group) for group in groups if group), default=0.0)
        return _bounded_score(
            0.60 * _mean(all_nodes) + 0.25 * lower_quartile + 0.15 * best_group
        )

    if game == "contexto":
        target = _node_score(dossier.get("target", {}), salience_for)
        neighbors = [
            _node_score(node, salience_for)
            for node in dossier.get("strong_neighbors", [])
        ]
        return _bounded_score(0.75 * target + 0.25 * _mean(neighbors))

    if game == "lant":
        endpoints = [
            _node_score(dossier.get("start", {}), salience_for),
            _node_score(dossier.get("target", {}), salience_for),
        ]
        intermediate = _unique_nodes(
            [
                node
                for path in dossier.get("representative_shortest_paths", [])
                for node in path.get("nodes", [])[1:-1]
            ]
        )
        route_mean = _mean([_node_score(node, salience_for) for node in intermediate])
        return _bounded_score(
            0.55 * _mean(endpoints) + 0.25 * min(endpoints) + 0.20 * route_mean
        )

    if game == "alchimie":
        seeds = [
            _node_score(node, salience_for) for node in dossier.get("seeds", [])
        ]
        if not seeds:
            return 0
        target_node = dossier.get("target", {})
        target = _node_score(target_node, salience_for)
        excluded = {
            str(target_node.get("id") or ""),
            *(str(node.get("id") or "") for node in dossier.get("seeds", [])),
        }
        intermediate = _unique_nodes(
            [
                node
                for step in dossier.get("minimum_action_recipe") or []
                for node in step.get("results", [])
                if str(node.get("id") or "") not in excluded
            ]
        )
        intermediate_mean = _mean(
            [_node_score(node, salience_for) for node in intermediate]
        )
        return _bounded_score(
            0.45 * _mean(seeds)
            + 0.20 * min(seeds)
            + 0.25 * target
            + 0.10 * intermediate_mean
        )

    raise ValueError(f"unknown game kind: {game!r}")


def _finding_count(dossier: dict, check: str) -> int:
    return sum(
        finding.get("check") == check
        for finding in dossier.get("lint_findings", [])
    )


def _semantic_strength_score(strengths: list[float]) -> float:
    if not strengths:
        return 0.0
    bounded = [max(0.0, min(1.0, float(value))) for value in strengths]
    return 100.0 * (0.60 * _mean(bounded) + 0.40 * min(bounded))


def _choice_score(value: float) -> float:
    if value <= 1:
        return 0.0
    if value == 2:
        return 70.0
    if value <= 5:
        return 100.0
    return max(50.0, 100.0 - 10.0 * (value - 5.0))


def _width_score(value: float) -> float:
    if value < 2:
        return 0.0
    if value < 3:
        return 70.0
    if value <= 6:
        return 100.0
    return max(50.0, 100.0 - 10.0 * (value - 6.0))


def _opening_ratio_score(value: float) -> float:
    ratio = max(0.0, min(1.0, float(value)))
    if ratio < 0.15:
        return 100.0 * ratio / 0.15
    if ratio <= 0.45:
        return 100.0
    return max(50.0, 100.0 - 50.0 * (ratio - 0.45) / 0.55)


def _par_score(difficulty: str, depth: object) -> float:
    if isinstance(depth, bool) or not isinstance(depth, int):
        return 0.0
    bands = {"usor": (2, 2), "normal": (2, 3), "greu": (3, 5)}
    band = bands.get(difficulty)
    if band is None:
        return 0.0
    low, high = band
    distance = max(low - depth, depth - high, 0)
    return max(0.0, 100.0 - 30.0 * distance)


def play_quality(
    game: str,
    rec: dict,
    dossier: dict,
    edge_strength: Callable[[str, str], float],
) -> int:
    """Bounded mechanic proxy from deterministic critique/dossier evidence."""

    if game == "conexiuni":
        fairness = dossier.get("fairness", {})
        unfair = len(fairness.get("unfair_tiles", []))
        contested = len(fairness.get("contested_tiles", []))
        engine_unfair = int(fairness.get("engine_unfair_raw") or 0)
        cross_edges = len(dossier.get("cross_group_strong_edges", []))
        penalty = (
            35 * unfair
            + 8 * max(0, contested - 1)
            + 4 * max(0, engine_unfair - 2)
            + 2 * max(0, cross_edges - 4)
            + 8 * _finding_count(dossier, "type_coherence")
            + 12 * _finding_count(dossier, "mirrored_groups")
            + 5 * _finding_count(dossier, "duplicate_groups")
            + 15 * _finding_count(dossier, "generic_region_link")
        )
        return _bounded_score(100.0 - penalty)

    if game == "contexto":
        target = dossier.get("target", {})
        neighbors = dossier.get("strong_neighbors", [])
        strong_count = min(100.0, 20.0 * len(neighbors))
        strong_familiarity = _mean(
            [100.0 * float(node.get("salience") or 0.0) for node in neighbors]
        )
        incoming = min(100.0, 12.5 * int(target.get("incoming_degree") or 0))
        reachable = min(100.0, 100.0 * int(dossier.get("reachable") or 0) / 120.0)
        score = (
            0.35 * strong_count
            + 0.35 * strong_familiarity
            + 0.20 * incoming
            + 0.10 * reachable
            - 15 * _finding_count(dossier, "generic_region_link")
        )
        return _bounded_score(score)

    if game == "lant":
        branch = dossier.get("branch_profile", {})
        first_hops = float(branch.get("valid_first_hops") or 0)
        min_width = float(branch.get("narrowest_shortest_path_layer") or 0)
        optimal = rec.get("optimal")
        denominator = max(1, optimal - 1) if isinstance(optimal, int) else 1
        average_width = float(
            branch.get("total_intermediate_shortest_path_nodes") or 0
        ) / denominator
        strengths = [
            float(edge.get("strength") or 0.0)
            for path in dossier.get("representative_shortest_paths", [])
            for edge in path.get("edges", [])
        ]
        score = (
            0.30 * _choice_score(first_hops)
            + 0.25 * _choice_score(min_width)
            + 0.20 * _width_score(average_width)
            + 0.25 * _semantic_strength_score(strengths)
        )
        return _bounded_score(score)

    if game == "alchimie":
        seeds = [str(node.get("id") or "") for node in dossier.get("seeds", [])]
        pair_count = math.comb(len(seeds), 2) if len(seeds) >= 2 else 0
        craft = dossier.get("craft_profile", {})
        opening_ratio = (
            float(craft.get("opening_pairs") or 0) / pair_count if pair_count else 0.0
        )
        strengths = []
        for step in dossier.get("minimum_action_recipe") or []:
            parents = [str(node.get("id") or "") for node in step.get("pair", [])]
            for result in step.get("results", []):
                result_id = str(result.get("id") or "")
                strengths.extend(edge_strength(parent, result_id) for parent in parents)
        openings = dossier.get("productive_openings", [])
        noise = (
            max(
                40.0,
                100.0
                - 10.0
                * max(
                    0.0,
                    _mean([float(item.get("result_count") or 0) for item in openings])
                    - 3.0,
                ),
            )
            if openings
            else 0.0
        )
        score = (
            0.30 * _opening_ratio_score(opening_ratio)
            + 0.30 * _semantic_strength_score(strengths)
            + 0.25 * _par_score(str(rec.get("difficulty") or ""), rec.get("target_depth"))
            + 0.15 * noise
        )
        return _bounded_score(score)

    raise ValueError(f"unknown game kind: {game!r}")


def _service_salience(svc: WordGameService, node_id: str) -> float:
    node = svc.node(node_id)
    return float(node.salience) if node is not None else 0.0


def _service_edge_strength(svc: WordGameService, source: str, target: str) -> float:
    edge = svc.link(source, target)
    return float(edge.strength) if edge is not None else 0.0


def _pilot_eligible(
    rec: dict,
    game: str,
    dossier: dict,
    svc: WordGameService,
) -> bool:
    return (
        rec.get("status") == "approved"
        and not validate_payload(rec, game, svc)
        and not any(
            finding.get("level") == "FAIL"
            for finding in dossier.get("lint_findings", [])
        )
    )


def _score_rows() -> tuple[list[dict], dict]:
    pack, svc, strong, regions = critique_pack.load_all(
        critique_pack.PACKAGE_PACK, critique_pack.PACKAGE_KG
    )
    _, _, selected = critique_pack.run(
        pack,
        svc,
        strong,
        regions,
        list(GAME_KINDS),
        set(STATUSES),
        None,
    )
    def salience_for(node_id: str) -> float:
        return _service_salience(svc, node_id)

    def edge_strength(source: str, target: str) -> float:
        return _service_edge_strength(svc, source, target)
    rows: list[dict] = []
    for game, rec, findings in selected:
        dossier = critique_pack.build_dossier(
            rec, game, svc, strong, findings, regions
        )
        familiarity = romanian_familiarity(game, dossier, salience_for)
        quality = play_quality(game, rec, dossier, edge_strength)
        rows.append(
            {
                "id": str(rec["id"]),
                "game": game,
                "status": str(rec["status"]),
                "romanian_familiarity": familiarity,
                "play_quality": quality,
                "pilot_score": _bounded_score(0.60 * familiarity + 0.40 * quality),
                "rank": 0,
                "pilot_eligible": _pilot_eligible(rec, game, dossier, svc),
                "selection_weight": 1,
            }
        )
    return rows, pack


def generate_rankings() -> dict:
    """Return the complete ranking document with deterministic order and weights."""

    rows, pack = _score_rows()
    for game in GAME_KINDS:
        game_rows = [row for row in rows if row["game"] == game]
        game_rows.sort(key=lambda row: (-row["pilot_score"], row["id"]))
        for rank, row in enumerate(game_rows, start=1):
            row["rank"] = rank

        eligible = [row for row in game_rows if row["pilot_eligible"]]
        count = len(eligible)
        if count:
            for index, row in enumerate(eligible):
                row["selection_weight"] = 5 - min(4, (5 * index) // count)

    rows.sort(key=lambda row: (GAME_KINDS.index(row["game"]), row["rank"]))
    by_game = {game: sum(row["game"] == game for row in rows) for game in GAME_KINDS}
    eligible_by_game = {
        game: sum(row["game"] == game and row["pilot_eligible"] for row in rows)
        for game in GAME_KINDS
    }
    counts = {
        "total": len(rows),
        "approved": sum(row["status"] == "approved" for row in rows),
        "pilot_eligible": sum(row["pilot_eligible"] for row in rows),
        "by_game": by_game,
        "eligible_by_game": eligible_by_game,
    }
    declared = sum(len(pack.get(game, [])) for game in GAME_KINDS)
    if counts["total"] != declared:
        raise ValueError(
            f"ranking coverage mismatch: scored {counts['total']} of {declared} records"
        )
    document = {
        "meta": {
            "schema_version": SCHEMA_VERSION,
            "pack_sha256": critique_pack.normalized_text_sha256(
                critique_pack.PACKAGE_PACK
            ),
            "kg_sha256": critique_pack.normalized_text_sha256(
                critique_pack.PACKAGE_KG
            ),
            "rubric_sha256": critique_pack.normalized_text_sha256(
                critique_pack.RUBRIC_PATH
            ),
            "counts": counts,
        },
        "boards": rows,
    }
    if tuple(document["meta"]) != META_FIELDS:
        raise AssertionError("ranking meta field order/schema drifted")
    if tuple(document["meta"]["counts"]) != COUNT_FIELDS:
        raise AssertionError("ranking count field order/schema drifted")
    if any(tuple(row) != BOARD_FIELDS for row in rows):
        raise AssertionError("ranking board field order/schema drifted")
    return document


def render_rankings(document: dict) -> bytes:
    return (
        json.dumps(document, ensure_ascii=False, indent=1, separators=(",", ": "))
        + "\n"
    ).encode("utf-8")


def _audit_summary(document: dict) -> None:
    counts = document["meta"]["counts"]
    print(
        "board_rankings: "
        f"{counts['total']} total / {counts['pilot_eligible']} pilot-eligible"
    )
    for game in GAME_KINDS:
        rows = [
            row
            for row in document["boards"]
            if row["game"] == game and row["pilot_eligible"]
        ]
        rows.sort(key=lambda row: (-row["pilot_score"], row["id"]))
        top = ", ".join(
            f"{row['id']}={row['pilot_score']}" for row in rows[:3]
        )
        print(
            f"  {game:<10} {counts['by_game'][game]:>3} total / "
            f"{counts['eligible_by_game'][game]:>3} eligible; top: {top}"
        )


def _check_copies(expected: bytes) -> list[str]:
    errors = []
    for path in RANKING_COPIES:
        try:
            actual = path.read_bytes()
        except OSError as exc:
            errors.append(f"cannot read {path.relative_to(_REPO_ROOT)}: {exc}")
            continue
        if actual != expected:
            errors.append(
                f"{path.relative_to(_REPO_ROOT)} is stale; run with --write"
            )
    if all(path.exists() for path in RANKING_COPIES):
        if PACKAGE_RANKINGS.read_bytes() != TESTS_RANKINGS.read_bytes():
            errors.append("package and tests ranking sidecars are not byte-identical")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--write",
        action="store_true",
        help="regenerate both committed sidecar copies (default: read-only check)",
    )
    args = parser.parse_args((argv or sys.argv)[1:])

    document = generate_rankings()
    rendered = render_rankings(document)
    _audit_summary(document)
    if args.write:
        for path in RANKING_COPIES:
            path.write_bytes(rendered)
            print(f"  wrote {path.relative_to(_REPO_ROOT)}")
        print("board rankings WRITTEN")
        return 0

    errors = _check_copies(rendered)
    if errors:
        for error in errors:
            print(f"board_rankings: ERROR: {error}", file=sys.stderr)
        return 1
    print("board rankings GREEN")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
