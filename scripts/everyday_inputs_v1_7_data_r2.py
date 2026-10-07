"""V1.7 R2 single employee-pay alias reconsideration; final adoption withheld.

Only this new wave batch reconsiders leafă for Salary. Historical V50/V72 sources,
all other inherited dispositions and the shared importer gate remain unchanged.
A global bare alias cannot mechanically filter homonymous intent. Exact fresh
module reviews and all prospective/native/history gates are still required.
"""

from basic_words_v33_data import BEGINNER_BENCHMARK as BEGINNER_BENCHMARK
from contexto_common_words_v72_data import (
    DEFERRED_AMBIGUOUS_TERMS as BASE_DEFERRED_AMBIGUOUS_TERMS,
)

BUILD_VERSION = "fixture-v1-7-employee-pay-input"
NOTE = (
    "V1.7 R2: one singular employee-pay input; "
    "only this batch reconsiders the archived leafă hold."
)
GAME_ITEM_IDS = ()
NEW_NODE_IDS = ()
INTUITIVE_PAIRS = ()
RECONSIDERED_HOLD_FORMS = ("leafă",)
RECONSIDERED_HOLD_OWNERS = {"leafă": "n_v4soc_salariu"}
DEFERRED_AMBIGUOUS_TERMS = tuple(
    term for term in BASE_DEFERRED_AMBIGUOUS_TERMS if term != "leafă"
)
ALIASES = {"n_v4soc_salariu": ("leafă",)}
EDGES = ()


def _validate_reconsideration_scope():
    assert len(BASE_DEFERRED_AMBIGUOUS_TERMS) == 70
    assert BASE_DEFERRED_AMBIGUOUS_TERMS.count("leafă") == 1
    index = BASE_DEFERRED_AMBIGUOUS_TERMS.index("leafă")
    expected = (
        BASE_DEFERRED_AMBIGUOUS_TERMS[:index]
        + BASE_DEFERRED_AMBIGUOUS_TERMS[index + 1 :]
    )
    assert DEFERRED_AMBIGUOUS_TERMS == expected
    assert len(DEFERRED_AMBIGUOUS_TERMS) == 69
    assert RECONSIDERED_HOLD_FORMS == ("leafă",)
    assert RECONSIDERED_HOLD_OWNERS == {"leafă": "n_v4soc_salariu"}
    assert ALIASES == {"n_v4soc_salariu": ("leafă",)}
    assert not EDGES and not NEW_NODE_IDS and not GAME_ITEM_IDS


def build_nodes_and_edges():
    _validate_reconsideration_scope()
    return {"nodes": (), "edges": EDGES, "aliases": ALIASES}
