"""Exact, reviewed label repairs and their frozen derived-board identities.

Only labels may change.  Each correction binds the whole approved source record;
derived identity uses its historical label so a wording repair cannot select a new
partition through the diversity cap's ID tie-break.  Live payloads keep the repair.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass


@dataclass(frozen=True)
class GroupLabelCorrection:
    key: str
    before: str
    after: str
    members: tuple[str, ...]


@dataclass(frozen=True)
class PackLabelCorrection:
    item_id: str
    before_sha256: str
    groups: tuple[GroupLabelCorrection, ...]


CORRECTIONS = (
    PackLabelCorrection(
        item_id="cx_gastronomie_171",
        before_sha256="baf8750543974819f7d65cf6d3b7f09a00c2117c7448c71aeaefb7b107e9ab56",
        groups=(
            GroupLabelCorrection(
                key="g1",
                before="Localitatea e deja în meniu",
                after="Denumiri cu trimitere geografică",
                members=(
                    "n_gas_varza_a_la_cluj", "n_gas_covrigi_buzau",
                    "n_gas_baclava_dobrogeana", "n_gas_bucovina_gastronomica",
                ),
            ),
            GroupLabelCorrection(
                key="g3",
                before="Alb, sărat, din zona laptelui",
                after="Produse lactate",
                members=(
                    "n_v2gas_branza", "n_gas_telemea", "n_gas_urda",
                    "n_gas_branza_smantana",
                ),
            ),
        ),
    ),
)


def record_sha256(record: dict) -> str:
    blob = json.dumps(
        record, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def correction_state(record: dict, correction: PackLabelCorrection) -> str:
    """Accept the bound before or complete after record; refuse partial/stale edits."""
    if record.get("id") != correction.item_id or record.get("status") != "approved":
        raise ValueError(f"label correction requires approved source {correction.item_id}")
    groups = record.get("groups", {})
    labels = record.get("group_labels", {})
    states = set()
    restored = deepcopy(record)
    for group in correction.groups:
        if tuple(groups.get(group.key, ())) != group.members:
            raise ValueError(f"label correction member drift: {correction.item_id}/{group.key}")
        label = labels.get(group.key)
        if label == group.before:
            states.add("before")
        elif label == group.after:
            states.add("after")
        else:
            raise ValueError(f"label correction label drift: {correction.item_id}/{group.key}")
        restored["group_labels"][group.key] = group.before
    if len(states) != 1:
        raise ValueError(f"partial label correction: {correction.item_id}")
    if record_sha256(restored) != correction.before_sha256:
        raise ValueError(f"label correction source record drift: {correction.item_id}")
    return states.pop()


def correction_sources(pack: dict) -> dict[str, tuple[dict, str]]:
    """Find each source exactly once and verify its complete bound record."""
    ids = [row.get("id") for row in pack["conexiuni"]]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate Conexiuni source IDs in label correction input")
    sources = {row["id"]: row for row in pack["conexiuni"]}
    result = {}
    for correction in CORRECTIONS:
        if correction.item_id in result:
            raise ValueError(f"duplicate label correction: {correction.item_id}")
        if correction.item_id not in sources:
            raise ValueError(f"missing label correction source: {correction.item_id}")
        row = sources[correction.item_id]
        result[correction.item_id] = (row, correction_state(row, correction))
    return result


def corrected_pack(pack: dict) -> dict:
    """Return only the exact label delta, rejecting reapplication before any write."""
    candidate = deepcopy(pack)
    sources = correction_sources(candidate)
    for correction in CORRECTIONS:
        row, state = sources[correction.item_id]
        if state != "before":
            raise ValueError(f"label correction already applied: {correction.item_id}")
        for group in correction.groups:
            row["group_labels"][group.key] = group.after
        if correction_state(row, correction) != "after":
            raise AssertionError("label correction did not produce the exact after-state")
    return candidate


def identity_payload(game: str, source_id: str, payload: dict) -> dict:
    """Normalize only reviewed source/member/label matches for historical ID hashing."""
    corrections = [row for row in CORRECTIONS if row.item_id == source_id]
    if not corrections:
        return payload
    candidate = deepcopy(payload)
    if game == "intrusul":
        pieces = [(candidate, 3)]
    elif game == "perechi":
        pieces = [(pair, 2) for pair in candidate.get("pairs", [])]
    else:
        return payload
    for piece, size in pieces:
        members = piece.get("members", ())
        for correction in corrections:
            for group in correction.groups:
                if (
                    len(members) == len(set(members)) == size
                    and set(members) <= set(group.members)
                    and piece.get("group_label") == group.after
                ):
                    piece["group_label"] = group.before
    return candidate
