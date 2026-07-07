"""Category taxonomy for the word games — the single source of truth.

Two kinds of category:

* ``serious`` — the 8 KG-contract categories the fixture has always carried
  (labels kept byte-identical to the historical per-game maps).
* ``pop`` — the curated pop-culture categories added for the curated games layer
  (ADR-0011). They become playable as soon as the fixture carries nodes tagged
  with them and/or the curated games pack ships approved instances for them.

Game modules, the meta endpoint, the curated pack loader and the pack validator
all derive from this module so a category can never be "known" in one place and
unknown in another.
"""

from __future__ import annotations

# key -> (display label, kind). Order here is the presentation order.
CATEGORIES: dict[str, tuple[str, str]] = {
    # pop culture — the viral shelf
    "muzica": ("Muzică", "pop"),
    "film_tv": ("Film & Seriale", "pop"),
    "meme_net": ("Internet & Meme", "pop"),
    "sport": ("Sport", "pop"),
    "viata_de_roman": ("Viața de român", "pop"),
    "gastronomie": ("Gastronomie", "pop"),
    # serious — labels byte-identical to the pre-existing per-game maps
    "arta_cultura": ("Arta & Cultura", "serious"),
    "geografie": ("Geografie", "serious"),
    "istorie": ("Istorie", "serious"),
    "limba": ("Limba", "serious"),
    "literatura": ("Literatura", "serious"),
    "personalitati": ("Personalitati", "serious"),
    "societate": ("Societate", "serious"),
    "stiinta": ("Stiinta", "serious"),
}

CATEGORY_LABELS: dict[str, str] = {key: label for key, (label, _kind) in CATEGORIES.items()}


def category_label(key: str) -> str:
    """Display label for a category key (unknown keys echo back unchanged)."""
    return CATEGORY_LABELS.get(key, key)


def category_kind(key: str) -> str | None:
    entry = CATEGORIES.get(key)
    return entry[1] if entry else None


def is_known(key: str) -> bool:
    return key in CATEGORIES


def known_keys() -> tuple[str, ...]:
    return tuple(CATEGORIES)
