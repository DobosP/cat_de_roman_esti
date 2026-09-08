"""Scoped V89 scorer/selector fixture for the retired dust projection's history."""

from __future__ import annotations

import json
from contextlib import contextmanager
from pathlib import Path

from cat_de_roman_esti.graph import Graph
from cat_de_roman_esti.wordgames import contexto as C
from cat_de_roman_esti.wordgames import contexto_projection as P
from cat_de_roman_esti.wordgames import packs, service
from tests.content_history import (
    before_v90_fixture,
    before_v90_pack,
    before_v90_projection_neighborhoods,
    before_v90_projection_rows,
    before_v90_rankings,
)
from tests.current_content import CURRENT_CONTENT

ROOT = Path(__file__).resolve().parents[1]


@contextmanager
def v89_contexto_snapshot(monkeypatch, *test_modules):
    """Restore exact reviewed V89 inputs only within explicitly named history tests.

    Cached live functions are never used to build the historical service or pack.
    Fresh per-instance graph caches disappear with those objects, while both live
    singletons are cleared before and after the scope. Teardown proves native V90
    dust and the actual ranked pack return, even when the historical test raises.
    """
    current_service = service.get_service
    current_pack = packs.get_pack
    current_service.cache_clear()
    current_pack.cache_clear()

    def read(filename):
        return json.loads((ROOT / "cat_de_roman_esti/fixtures" / filename).read_bytes())

    graph = before_v90_fixture(read("kg_sample.json"))
    old_service = service.WordGameService(Graph.from_records(graph["kg_nodes"], graph["kg_edges"]))
    old_rankings = before_v90_rankings(read("board_rankings_v37.json"))
    old_pack = packs.GamesPack(packs._parse_items(
        before_v90_pack(read("games_pack.json")),
        {row["id"]: row for row in old_rankings["boards"]},
    ), ranked=True)
    rows = before_v90_projection_rows([
        (t.surface, t.anchor_id, t.domain, t.rank_penalty, t.mapping_kind, t.public_id)
        for t in P.PROJECTION_TERMS
    ])
    terms = tuple(P.ProjectionTerm(*row[:5]) for row in rows)
    assert [(t.surface, t.anchor_id, t.domain, t.rank_penalty, t.mapping_kind, t.public_id)
            for t in terms] == rows
    neighborhoods = before_v90_projection_neighborhoods(P.PROJECTION_NEIGHBORHOODS)
    try:
        with monkeypatch.context() as patch:
            patch.setattr(P, "PROJECTION_TERMS", terms)
            patch.setattr(P, "PROJECTION_INDEX", {term.key: term for term in terms})
            patch.setattr(P, "PROJECTION_NEIGHBORHOODS", neighborhoods)
            patch.setattr(C, "PROJECTION_NEIGHBORHOODS", neighborhoods)
            patch.setattr(C, "get_service", lambda: old_service)
            patch.setattr(C, "get_pack", lambda: old_pack)
            patch.setattr(packs, "get_pack", lambda: old_pack)
            for module in test_modules:
                if hasattr(module, "get_service"):
                    patch.setattr(module, "get_service", lambda: old_service)
                if hasattr(module, "get_pack"):
                    patch.setattr(module, "get_pack", lambda: old_pack)
            assert old_service.resolve("praf") is None
            assert old_pack.selectable_count("contexto") == 236
            yield old_service, old_pack
    finally:
        current_service.cache_clear()
        current_pack.cache_clear()
        assert C.get_service().resolve("praf") == "n_v90_household_praf"
        assert P.resolve_projection("praf") is None
        assert packs.get_pack().selectable_count("contexto") == CURRENT_CONTENT.contexto_eligible
