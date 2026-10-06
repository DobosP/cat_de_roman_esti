"""Generate independent native graph vectors from the production Python service."""

import difflib
import json
import random
from pathlib import Path

from cat_de_roman_esti.wordgames.service import (
    get_service,
    is_reviewed_unresolved_spelling,
    normalize,
)

svc = get_service()
ids = svc.all_ids()
randomizer = random.Random(29)
targets = [ids[i] for i in [0, 100, 500, 1000, 1700, 2200]]
texts = [
    "Ștefan cel Mare",
    "  MIHAI\x1c  EMINESCU ",
    "Mihai Eminscu",
    "intrigii",
    "intrigilor",
    "paște",
    "paștele",
    "paşte",
    "pas\u0326te",
    "paste",
    "pasta",
    " ＭＩＨＡＩ  ＥＭＩＮＥＳＣＵ ",
    "stradă",
    "Bucurest",
    "a" * 240,
    "",
    "xylophoneneexistent",
    "🥨",
    "İstanbul",
]
alphabet = "abcdșțîâă😀"
ratios = [
    [a, b, difflib.SequenceMatcher(None, a, b).ratio()]
    for a, b in [
        ("tide", "diet"),
        ("diet", "tide"),
        ("a" * 240, "b" + "a" * 240),
        ("b" + "a" * 240, "a" * 240),
        ("", ""),
    ]
]
for _ in range(60):
    a = "".join(randomizer.choice(alphabet) for _ in range(randomizer.randrange(0, 40)))
    b = "".join(randomizer.choice(alphabet) for _ in range(randomizer.randrange(0, 40)))
    ratios.append([a, b, difflib.SequenceMatcher(None, a, b).ratio()])
document = {
    "texts": [
        {
            "text": t,
            "normalized": normalize(t),
            "unresolved": is_reviewed_unresolved_spelling(t),
            "resolved": svc.resolve(t) or "",
            "fuzzy": svc.resolve_fuzzy(t) or "",
            "suggestions": svc.suggest(t),
        }
        for t in texts
    ],
    "ratios": ratios,
    "targets": [
        {
            "id": t,
            "neighbors": svc.neighbor_ids(t),
            "predecessors": svc.predecessor_ids(t),
            "from": svc.distances_from(t),
            "from_order": list(svc.distances_from(t)),
            "to": svc.distances_to(t),
            "to_order": list(svc.distances_to(t)),
            "weighted": svc.weighted_distances_to(t),
        }
        for t in targets
    ],
    "salience": svc.by_salience(minimum=0.6),
    "salience_ascending": svc.by_salience(descending=False),
}
Path(__file__).with_name("python_graph.json").write_text(
    json.dumps(document, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8"
)
