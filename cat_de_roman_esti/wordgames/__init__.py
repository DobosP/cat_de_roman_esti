"""Text-only "combine words to reach a destination" mini-games over the Romanian KG.

No graph visualization: each game is a server-authoritative text game that reuses the
bundled knowledge graph (`data.load_fixture`) through the shared :mod:`.service` layer.
Three games, each a self-contained FastAPI ``APIRouter`` mounted by the BFF:

  * ``alchimie``   — Infinite-Craft-style: combine two concepts into a new one (their
                     shared KG neighbour) and keep crafting until you reach the target.
  * ``contexto``   — Contexto/Semantle-style: a hidden secret concept; each guess reports
                     how close (graph distance) you are; find it.
  * ``lant``       — word-ladder / Wiki-game-style: type a concept linked to the current
                     one and hop along real semantic edges to the target.
"""
