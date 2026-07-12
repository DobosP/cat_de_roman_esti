"""Contexto / Semantle-style word game: "Cald sau Rece".

There is a hidden SECRET target concept in the Romanian knowledge graph. The player
types concept guesses; each guess reports how CLOSE it is to the target, measured as the
directed BFS graph distance from guess to target on the shared non-distractor subgraph
(:mod:`.service`). Distance 0 means the guess IS the target — the player wins. Otherwise
the game maps the distance to a "temperature" tier (Fierbinte … Inghetat) and a 0..100
closeness score derived from how the guess ranks within the precomputed inbound-distance
distribution of all reachable concepts.

Server-authoritative: the target id is NEVER returned to the client until the game is won
or given up. Public guess views are built through a reveal gate so rank feedback stays
useful without accidentally serializing the hidden answer. Sessions live in-memory in a
:class:`SessionStore`.
"""

from __future__ import annotations

import random
from bisect import bisect_left
from dataclasses import dataclass, field

from django.urls import path
from drf_spectacular.utils import extend_schema
from pydantic import BaseModel
from rest_framework.response import Response

from ..web.http import (
    ContractAPIView,
    OptionalSessionAuth,
    http_error,
    parse_body,
    query_int,
    query_str,
)
from ._progress import excluded_pack_ids, record_finished
from .categories import CATEGORY_LABELS as _SHARED_CATEGORY_LABELS
from .categories import category_label, is_known
from .packs import get_pack
from .service import SessionStore, daily_seed, get_service

GAME_KEY = "contexto"
_DIFFICULTIES = ("usor", "normal", "greu")
_DEFAULT_DIFFICULTY = "normal"

# A target needs a large inbound-reachable set so almost every guess gets a meaningful
# directed distance to the secret.
MIN_REACHABLE = 120

# In practice almost every concept can reach most targets, so MIN_REACHABLE alone rarely
# rejects a poor target. The signal that actually makes a game feel good is the
# "responsive zone": how many guesses sit 1..5 directed hops from the target — a distance
# the player can FEEL (Fierbinte..Rece). A target whose responsive zone is tiny pushes
# almost every guess into "Inghetat", which gives flat, unsatisfying feedback. We therefore
# require a minimum responsive-zone size so a guess is likely to land somewhere with a
# real temperature gradient. (Playtested: this floor removes the degenerate long-thin-tail
# targets — e.g. n_plumb / n_emil_racovita — while keeping wide variety per difficulty.)
RESPONSIVE_MAX_HOPS = 5
MIN_RESPONSIVE = 40

# A clue should help a stuck player without making the opening trivial. It reveals only
# the target's broad KG category, never the hidden id/label/description.
MIN_CLUE_ATTEMPTS = 3
CLUE_SCORE_PENALTY = 120

CATEGORY_LABELS = _SHARED_CATEGORY_LABELS


# --------------------------------------------------------------------------- session
@dataclass
class GuessRecord:
    id: str
    label: str
    distance: int
    temperature: str
    closeness: int
    rank: int


@dataclass
class ContextoSession:
    target: str
    # directed distance (guess -> target) -> count of guesses at that distance
    dist_hist: dict[int, int]
    reachable: int
    # how many reachable nodes are STRICTLY farther than distance d (for ranking)
    farther_than: dict[int, int] = field(default_factory=dict)
    # how many reachable nodes are STRICTLY closer than distance d (rank = this + 1)
    closer_than: dict[int, int] = field(default_factory=dict)
    # graded (Dijkstra) distance for every reachable node, and — per hop bucket — the
    # sorted list of those distances. Together they refine the rank WITHIN a hop bucket so
    # a tighter (stronger-edged) path of the same hop count ranks better (ADR-0021).
    weighted_dist: dict[str, float] = field(default_factory=dict)
    sorted_weighted: dict[int, list[float]] = field(default_factory=dict)
    guesses: dict[str, GuessRecord] = field(default_factory=dict)
    # guess ids in the chronological order they were first played (for the share trail)
    order: list[str] = field(default_factory=list)
    attempts: int = 0
    won: bool = False
    gave_up: bool = False
    clue_revealed: bool = False
    clues_used: int = 0
    difficulty: str = _DEFAULT_DIFFICULTY
    daily: str | None = None
    # Player-picked board theme + curated-pack provenance (None for mined games).
    category: str | None = None
    pack_id: str | None = None

    def __post_init__(self) -> None:
        # Precompute, for each distance value, how many reachable nodes are farther.
        # closeness uses this so we don't recompute on every guess.
        total = self.reachable
        # sorted distances ascending
        cumulative = 0
        self.farther_than = {}
        self.closer_than = {}
        for d in sorted(self.dist_hist):
            count_at = self.dist_hist[d]
            self.closer_than[d] = cumulative
            # nodes farther than d = total - (nodes at distance <= d)
            self.farther_than[d] = total - (cumulative + count_at)
            cumulative += count_at


store: SessionStore[ContextoSession] = SessionStore()


# --------------------------------------------------------------------------- scoring
def rank_for(
    session: ContextoSession,
    distance: int | None,
    weighted_distance: float | None = None,
) -> int:
    """One-based Contexto rank for a guess; lower is better and rank 1 is the target.

    Refined rank (ADR-0021): the hop bucket sets the coarse band and the graded
    (Dijkstra) distance orders guesses WITHIN it —
    ``closer_than[d] + bisect_left(sorted_weighted[d], weighted) + 1``. Because a guess's
    own weighted distance is a member of its bucket, the offset stays in
    ``[0, len(bucket) - 1]``, so every bucket-``d`` rank is strictly less than every
    bucket-``d+1`` rank (hop ordering is preserved) while ties are broken by path tightness.
    Omitting ``weighted_distance`` falls back to the bucket's best (coarse hop) rank.
    Unreachable guesses sit one slot past the reachable set, bounded by ``reachable + 1``.
    """
    if distance is None:
        return session.reachable + 1
    base = session.closer_than.get(distance, session.reachable)
    if weighted_distance is None:
        return base + 1
    bucket = session.sorted_weighted.get(distance, ())
    return base + bisect_left(bucket, weighted_distance) + 1


def closeness_for(
    session: ContextoSession,
    distance: int | None,
    weighted_distance: float | None = None,
) -> int:
    """0..100 closeness derived from the refined rank (ADR-0021).

    ``round(100 * (reachable - rank) / (reachable - 1))``, clamped to ``[1, 99]`` for
    non-wins: the target (distance 0) alone reads 100, and an unreachable guess reads 0 so
    it stays visibly colder than the coldest reachable bucket. A near miss can no longer
    saturate to 100 (which would be ambiguous with a win).
    """
    if distance is None:
        return 0
    if distance == 0:
        return 100
    total = session.reachable
    if total <= 1:
        return 0
    rank = rank_for(session, distance, weighted_distance)
    raw = round(100 * (total - rank) / (total - 1))
    return max(1, min(99, raw))


# Warmth tiers as fractions of the refined rank over the reachable set (ADR-0021). Replaces
# the old fixed hop table, which piled ~74% of guesses into one "Rece" bucket regardless of
# target. Ordered coldest-last; the exact Romanian labels are unchanged.
def temperature_for(
    session: ContextoSession,
    distance: int | None,
    weighted_distance: float | None = None,
) -> str:
    """Map a guess to a Romanian temperature tier by its refined-rank percentile.

    ``d == 0`` -> "Gasit"; unreachable -> "Inghetat". Otherwise, with
    ``pct = rank / reachable``: a distance-1 guess or ``pct <= 0.005`` -> "Fierbinte";
    ``<= 0.03`` -> "Cald"; ``<= 0.10`` -> "Caldut"; ``<= 0.40`` -> "Rece"; else "Inghetat".
    Warmth is monotonically non-increasing in rank (hop ordering is preserved by rank_for,
    so the distance-1 override never inverts a colder-ranked guess).
    """
    if distance is None:
        return "Inghetat"
    if distance == 0:
        return "Gasit"
    total = session.reachable
    rank = rank_for(session, distance, weighted_distance)
    pct = rank / total if total else 1.0
    if distance == 1 or pct <= 0.005:
        return "Fierbinte"
    if pct <= 0.03:
        return "Cald"
    if pct <= 0.10:
        return "Caldut"
    if pct <= 0.40:
        return "Rece"
    return "Inghetat"


# --------------------------------------------------------------------------- selection
# Hot/cold emoji trail for the shareable line: coldest -> hottest, plus a bullseye.
_TRAIL_FOUND = "🎯"
_TRAIL_HOT = "🟩"
_TRAIL_WARM = "🟨"
_TRAIL_COOL = "🟧"
_TRAIL_COLD = "🟥"


def score_for(attempts: int, clues_used: int = 0) -> int:
    """Reward few attempts: optimal (1 attempt) -> 1000, never below 50."""
    attempts = max(attempts, 1)
    return max(50, 1000 - 60 * (attempts - 1) - CLUE_SCORE_PENALTY * clues_used)


def _trail_emoji(record: GuessRecord) -> str:
    """One hot/cold square per guess, based on its closeness to the secret."""
    if record.distance == 0:
        return _TRAIL_FOUND
    c = record.closeness
    if c >= 75:
        return _TRAIL_HOT
    if c >= 50:
        return _TRAIL_WARM
    if c >= 25:
        return _TRAIL_COOL
    return _TRAIL_COLD


def share_line(session: ContextoSession) -> str:
    """Wordle-style shareable line with a hot/cold emoji trail of the guesses."""
    trail = "".join(_trail_emoji(session.guesses[gid]) for gid in session.order)
    header = "cat_de_roman_esti · Cald sau Rece"
    if session.category:
        header += f" · {category_label(session.category)}"
    lines = [
        header,
        trail,
        f"{session.attempts} incercari",
    ]
    if session.clues_used:
        lines.append(f"indiciu x{session.clues_used}")
    if session.daily is not None:
        lines.append(session.daily)
    return "\n".join(lines)


def _difficulty_pool(svc, difficulty: str, category: str | None = None) -> list[str]:
    """Candidate target ids for a difficulty tier (before the reachability filter).

    usor  -> high-salience, well-known targets (salience >= 0.6).
    greu  -> low-salience / obscure targets (the bottom of the salience order).
    normal-> the full pool (the historical default; any reachable concept).

    ``normal`` keeps the original ``all_ids`` candidate set so the long-standing
    seeded instances stay stable; only ``usor``/``greu`` bias the selection.
    An explicit ``category`` intersects any tier with that category's members.
    """
    if difficulty == "usor":
        high = svc.by_salience(minimum=0.6)
        pool = high or svc.all_ids()
    elif difficulty == "greu":
        # obscure: lowest salience first, restricted to the less-prominent half so a
        # "greu" target is genuinely off the beaten path.
        by_sal = svc.by_salience(descending=True)  # high -> low
        obscure = list(reversed(by_sal))
        pool = obscure[: max(1, len(obscure) // 2)] or obscure
    else:
        # normal: the historical default candidate set.
        pool = svc.all_ids()
    if category is not None:
        members = set(svc.by_category(category))
        pool = [nid for nid in pool if nid in members]
    return pool


def _responsive_count(dist: dict[str, int]) -> int:
    """How many reachable concepts sit in the player-perceptible temperature band.

    These are the guesses that can reach the target in 1..RESPONSIVE_MAX_HOPS hops —
    i.e. everything that comes back warmer than "Inghetat". A larger band means guesses
    spread across more tiers and the game feels responsive instead of flatly frozen.
    """
    return sum(1 for d in dist.values() if 1 <= d <= RESPONSIVE_MAX_HOPS)


def _is_good_target(dist: dict[str, int]) -> bool:
    """A target is good if it is both broadly reachable and has a real warm band."""
    return len(dist) >= MIN_REACHABLE and _responsive_count(dist) >= MIN_RESPONSIVE


def _build_session(
    target: str,
    difficulty: str,
    daily: str | None,
    *,
    category: str | None = None,
    pack_id: str | None = None,
) -> ContextoSession:
    svc = get_service()
    # Runtime guesses are scored with distance(guess, target), so the histogram must use
    # that same direction. On one-way edges, distances_from(target) answers the opposite
    # question and produces internally inconsistent ranks/closeness.
    dist = svc.distances_to(target)
    # Graded distance over the SAME reachable set (ADR-0021): one O(N log N) pass at create.
    wdist = svc.weighted_distances_to(target)
    hist: dict[int, int] = {}
    buckets: dict[int, list[float]] = {}
    for nid, d in dist.items():
        hist[d] = hist.get(d, 0) + 1
        # Reachability is identical to the hop BFS; fall back to the hop count only if a
        # node were ever missing from the Dijkstra map (it is not, in practice).
        buckets.setdefault(d, []).append(wdist.get(nid, float(d)))
    for values in buckets.values():
        values.sort()
    return ContextoSession(
        target=target,
        dist_hist=hist,
        reachable=len(dist),
        weighted_dist=wdist,
        sorted_weighted=buckets,
        difficulty=difficulty,
        daily=daily,
        category=category,
        pack_id=pack_id,
    )


def _pick_target(
    seed: int | None,
    difficulty: str = _DEFAULT_DIFFICULTY,
    daily: str | None = None,
    category: str | None = None,
) -> ContextoSession:
    """Choose a solvable, *satisfying* secret target of the requested difficulty.

    Selection is deterministic for a given seed (so the daily challenge is stable) and
    enforces two quality floors so no degenerate instance ships:

    * reachability (``MIN_REACHABLE``) — almost every guess gets a real distance; and
    * a responsive warm band (``MIN_RESPONSIVE``) — enough concepts land at 1..5 hops
      that guesses spread across temperatures instead of all reading "Inghetat".

    We walk the seeded-shuffled candidate pool and take the FIRST target that clears both
    floors. Taking the first (rather than the best) keeps the per-seed variety wide while
    still guaranteeing quality. Fallbacks degrade gracefully: relax to reachability-only,
    then to the single most inbound-reachable node, so a game is always returned.
    """
    svc = get_service()
    rng = random.Random(seed)
    candidates = _difficulty_pool(svc, difficulty, category)
    if category is not None and not candidates:
        raise http_error(503, "Nu exista inca jocuri pentru aceasta categorie.")
    # Deterministic ordering: for daily/seeded runs the pool order is fixed, then a
    # seeded shuffle picks within it -> same date+difficulty => same target.
    candidates = list(candidates)
    rng.shuffle(candidates)

    fallback: str | None = None  # first node clearing reachability but not the warm band
    for nid in candidates:
        dist = svc.distances_to(nid)
        if not _is_good_target(dist):
            if fallback is None and len(dist) >= MIN_REACHABLE:
                fallback = nid
            continue
        return _build_session(nid, difficulty, daily, category=category)

    if fallback is not None:
        return _build_session(fallback, difficulty, daily, category=category)
    if category is not None:
        # A category pool stays within itself: never silently swap in an off-theme
        # target when the theme cannot make a playable game.
        best_in_cat = max(candidates, key=lambda n: len(svc.distances_to(n)))
        if len(svc.distances_to(best_in_cat)) >= MIN_REACHABLE:
            return _build_session(best_in_cat, difficulty, daily, category=category)
        raise http_error(503, "Nu exista inca jocuri pentru aceasta categorie.")
    # Last resort: nothing in this tier met even the reachability floor — take the
    # most inbound-reachable node so we still return a solvable game.
    best = max(svc.all_ids(), key=lambda n: len(svc.distances_to(n)))
    return _build_session(best, difficulty, daily)


# --------------------------------------------------------------------------- schemas
class GuessBody(BaseModel):
    text: str


def _guess_payload(record: GuessRecord, *, reveal: bool, target: str) -> dict:
    """Public guess view, guarded against pre-reveal target serialization."""
    if not reveal and record.id == target:
        raise RuntimeError("refusing to serialize the Contexto target before reveal")
    return {
        "id": record.id,
        "label": record.label,
        "distance": record.distance,
        "rank": record.rank,
        "temperature": record.temperature,
        "closeness": record.closeness,
    }


def _sorted_guesses(session: ContextoSession, *, reveal: bool) -> list[dict]:
    """Past guesses serialized best-first (smallest rank, then highest closeness)."""
    records = sorted(
        session.guesses.values(),
        key=lambda g: (g.rank, g.distance, -g.closeness, g.label),
    )
    return [_guess_payload(g, reveal=reveal, target=session.target) for g in records]


def _clue_payload(session: ContextoSession) -> dict:
    svc = get_service()
    node = svc.node(session.target)
    category = node.category if node is not None else ""
    label = CATEGORY_LABELS.get(category, category)
    return {
        "category": {"key": category, "label": label},
        "message": f"Categoria secretului: {label}.",
    }


def _state(game_id: str, session: ContextoSession) -> dict:
    reveal = session.won or session.gave_up
    body: dict = {
        "game_id": game_id,
        "attempts": session.attempts,
        "won": session.won,
        "gave_up": session.gave_up,
        "reachable_count": session.reachable,
        "difficulty": session.difficulty,
        "clues_used": session.clues_used,
        "clue_available": (
            not session.won
            and not session.gave_up
            and not session.clue_revealed
            and session.attempts >= MIN_CLUE_ATTEMPTS
        ),
        "guesses": _sorted_guesses(session, reveal=reveal),
    }
    if session.daily is not None:
        body["daily"] = session.daily
    if session.category:
        body["board_category"] = session.category
    if session.clue_revealed:
        body["clue"] = _clue_payload(session)
    if reveal:
        svc = get_service()
        body["target"] = {
            "id": session.target,
            "label": svc.label(session.target),
            "description": svc.description(session.target),
        }
    if session.won:
        body["score"] = score_for(session.attempts, session.clues_used)
        body["share"] = share_line(session)
    return body


# --------------------------------------------------------------------------- endpoints
class CreateGameView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="contexto_create_game", tags=["contexto"])
    def post(self, request):
        """Start a game. Optional ``?category=`` prefers a curated target for that
        theme and otherwise mines within the category; the daily prefers a curated
        target whenever one is approved (ADR-0011). For a signed-in player, curated
        instances they have already finished are excluded (dailies are exempt)."""
        seed = query_int(request, "seed")
        difficulty = query_str(request, "difficulty", _DEFAULT_DIFFICULTY)
        daily = query_str(request, "daily")
        category = query_str(request, "category")
        if difficulty not in _DIFFICULTIES:
            difficulty = _DEFAULT_DIFFICULTY
        if category is not None and not is_known(category):
            raise http_error(400, "Categorie necunoscuta.")
        if daily is not None:
            seed = daily_seed(daily, GAME_KEY)
            curated = get_pack().pick_daily(
                GAME_KEY, daily, category=category, difficulty=difficulty
            )
        else:
            curated = get_pack().pick_seeded(
                GAME_KEY,
                random.Random(seed),
                category=category,
                difficulty=difficulty,
                exclude_ids=excluded_pack_ids(request, GAME_KEY),
            )
        if curated is not None:
            # session.category echoes only a player-REQUESTED theme. A curated daily
            # stays themeless: exposing the theme for free would spoil the paid clue.
            session = _build_session(
                str(curated.payload["target"]),
                difficulty,
                daily,
                category=category,
                pack_id=curated.id,
            )
        else:
            session = _pick_target(seed, difficulty, daily, category)
        game_id = store.create(session)
        return Response(_state(game_id, session))


class GetGameView(ContractAPIView):
    @extend_schema(operation_id="contexto_get_game", tags=["contexto"])
    def get(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        return Response(_state(game_id, session))


class GuessView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="contexto_guess", tags=["contexto"])
    def post(self, request, game_id: str):
        body = parse_body(request, GuessBody)
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        if session.won or session.gave_up:
            raise http_error(400, "Jocul s-a terminat")

        svc = get_service()
        text = (body.text or "").strip()
        if not text:
            raise http_error(400, "Scrie un concept")

        node_id = svc.resolve(text)
        corrected = False
        if node_id is None:
            # Confident auto-accept (ADR-0022): a high-confidence, unambiguous near-miss
            # is played as the corrected concept — attempts count normally, and if the
            # correction IS the target that is a legitimate win (a typo'd answer is still
            # the answer). Anything weaker falls through to the advisory suggestions.
            node_id = svc.resolve_fuzzy(text)
            corrected = node_id is not None
        if node_id is None:
            # Unknown concept: do NOT count it as an attempt. Offer fuzzy "did you mean"
            # hints, but NEVER one that resolves to the hidden target (ADR-0009/0021).
            suggestions = [
                label
                for label in svc.suggest(text)
                if svc.resolve(label) != session.target
            ]
            message = "Nu cunosc acest concept"
            if suggestions:
                message = f"Nu cunosc acest concept. Poate cautai: {suggestions[0]}?"
            return Response(
                {
                    "ok": False,
                    "message": message,
                    "suggestions": suggestions,
                    "guesses": _sorted_guesses(session, reveal=False),
                    "attempts": session.attempts,
                    "won": session.won,
                    "reachable_count": session.reachable,
                    "clues_used": session.clues_used,
                    "clue_available": (
                        not session.clue_revealed
                        and session.attempts >= MIN_CLUE_ATTEMPTS
                    ),
                }
            )

        distance = svc.distance(node_id, session.target)
        weighted = session.weighted_dist.get(node_id)
        temperature = temperature_for(session, distance, weighted)
        closeness = closeness_for(session, distance, weighted)
        rank = rank_for(session, distance, weighted)
        # distance is None when the guess is in a disconnected part of the graph — we still
        # store it (as the coldest possible) so a repeated guess shows the same verdict.
        stored_distance = distance if distance is not None else 999

        record = GuessRecord(
            id=node_id,
            label=svc.label(node_id),
            distance=stored_distance,
            temperature=temperature,
            closeness=closeness,
            rank=rank,
        )
        is_new = node_id not in session.guesses
        session.guesses[node_id] = record
        if is_new:
            session.attempts += 1
            session.order.append(node_id)

        if distance == 0:
            session.won = True
            record_finished(request, GAME_KEY, session.pack_id)
        reveal = session.won or session.gave_up

        result: dict = {
            "ok": True,
            "guess": _guess_payload(record, reveal=reveal, target=session.target),
            "guesses": _sorted_guesses(session, reveal=reveal),
            "attempts": session.attempts,
            "won": session.won,
            "reachable_count": session.reachable,
            "clues_used": session.clues_used,
            "clue_available": (
                not session.won
                and not session.clue_revealed
                and session.attempts >= MIN_CLUE_ATTEMPTS
            ),
        }
        if corrected:
            # Tell the player what we understood. On a non-win the corrected node can
            # never be the target (correction == target implies distance 0, a win), so
            # this message cannot leak the hidden answer (ADR-0009).
            result["message"] = f"Am înțeles: {record.label}."
        if session.clue_revealed:
            result["clue"] = _clue_payload(session)
        if session.won:
            result["target"] = {
                "id": session.target,
                "label": svc.label(session.target),
                "description": svc.description(session.target),
            }
            result["score"] = score_for(session.attempts, session.clues_used)
            result["share"] = share_line(session)
        return Response(result)


class ClueView(ContractAPIView):
    @extend_schema(operation_id="contexto_clue", tags=["contexto"])
    def post(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        if session.won or session.gave_up:
            raise http_error(400, "Jocul s-a terminat")
        if session.attempts < MIN_CLUE_ATTEMPTS and not session.clue_revealed:
            need = MIN_CLUE_ATTEMPTS - session.attempts
            raise http_error(
                400,
                f"Mai incearca {need} concepte inainte de indiciu.",
            )
        if not session.clue_revealed:
            session.clue_revealed = True
            session.clues_used += 1
        return Response({"ok": True, **_clue_payload(session), **_state(game_id, session)})


class GiveUpView(ContractAPIView):
    authentication_classes = [OptionalSessionAuth]

    @extend_schema(operation_id="contexto_give_up", tags=["contexto"])
    def post(self, request, game_id: str):
        session = store.get(game_id)
        if session is None:
            raise http_error(404, "Joc inexistent")
        session.gave_up = True
        record_finished(request, GAME_KEY, session.pack_id)
        return Response(_state(game_id, session))


_BASE = "api/wordgames/contexto"
urlpatterns = [
    path(f"{_BASE}/games", CreateGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>", GetGameView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/guess", GuessView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/clue", ClueView.as_view()),
    path(f"{_BASE}/games/<str:game_id>/giveup", GiveUpView.as_view()),
]
