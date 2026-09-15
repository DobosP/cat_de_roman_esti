"""Unscored Alchimie exploration with validated, portable discovery checkpoints.

Sessions retain the common 7200-second TTL/1000-session cap. A checkpoint contains only
at most 256 successful crafts; replay validates ownership, canonical recipes and supplies.
Goals affect guidance only. They never choose recipes, award scores or stop play.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from django.urls import path
from drf_spectacular.utils import extend_schema
from pydantic import Field
from rest_framework.response import Response

from ..web.http import ContractAPIView, http_error, parse_body
from ._session_endpoint import atomic_session
from .discovery_world import MAX_CONCEPTS, DiscoveryWorld, Identifier, Record, Sha, get_world
from .service import SessionCapacityError, SessionStore

MAX_EMPTY_PAIRS = 128


class Progress(Record):
    world_id: Identifier
    recipe_hash: Sha
    discoveries: list[list[Identifier]] = Field(max_length=MAX_CONCEPTS)


class CreateBody(Record):
    progress: Progress | None = None
    goal_id: Identifier | None = None


class PairBody(Record):
    a: Identifier
    b: Identifier


class GoalBody(Record):
    goal_id: Identifier | None


@dataclass
class ExploreSession:
    world: DiscoveryWorld
    owned: dict[str, tuple[str, str] | None] = field(default_factory=dict)
    discoveries: list[tuple[str, str]] = field(default_factory=list)
    goal_id: str | None = None
    unlocked: set[str] = field(default_factory=set)
    revision: int = 0
    hint_pair: tuple[str, str] | None = None
    hint_stage: int = 0
    # Observed failures only; never part of a portable discovery checkpoint.
    empty_pairs: dict[tuple[str, str], None] = field(default_factory=dict)

    def award_supplies(self) -> list[str]:
        supplied = []
        for unlock in self.world.catalog.unlocks:
            if unlock.id not in self.unlocked and len(self.discoveries) >= unlock.after_discoveries:
                self.unlocked.add(unlock.id)
                for concept_id in unlock.concept_ids:
                    self.owned[concept_id] = None
                    supplied.append(concept_id)
        return supplied

    def craft(self, pair: tuple[str, str]) -> tuple[str | None, bool, list[str]]:
        if pair[0] == pair[1] or not set(pair) <= self.owned.keys():
            raise http_error(400, "Alege două ingrediente diferite din colecția ta.")
        recipe = self.world.recipes.get(pair)
        if recipe is None:
            return None, False, []
        if recipe.result in self.owned:
            return recipe.result, False, []
        if len(self.discoveries) >= MAX_CONCEPTS:
            raise http_error(409, "Colecția a atins limita acestei lumi.")
        self.owned[recipe.result] = pair
        self.discoveries.append(pair)
        self.hint_pair, self.hint_stage = None, 0
        return recipe.result, True, self.award_supplies()


store: SessionStore[ExploreSession] = SessionStore()
_atomic_session = atomic_session(lambda: store, "Explorarea a expirat. Reia colecția salvată.")


def _concept(session: ExploreSession, concept_id: str) -> dict:
    return {"id": concept_id, "label": session.world.concepts[concept_id].label}


def _hint_payload(session: ExploreSession) -> dict | None:
    if session.hint_stage == 0:
        return None
    if session.hint_pair is None:
        return {"stage": "complete", "message": "Ai descoperit tot în această lume!",
                "output": None, "pair": None}
    recipe = session.world.recipes[session.hint_pair]
    label = session.world.concepts[recipe.result].label
    pair = ([_concept(session, item) for item in session.hint_pair]
            if session.hint_stage >= 2 else None)
    message = (f"Încearcă {pair[0]['label']} + {pair[1]['label']}." if pair else
               f"Poți descoperi «{label}» cu ingredientele pe care le ai.")
    return {"stage": "pair" if pair else "output", "message": message,
            "output": {"label": label}, "pair": pair}


def state_payload(game_id: str, session: ExploreSession) -> dict:
    world, owned = session.world, session.owned
    inventory = []
    for concept_id, parents in owned.items():
        concept = world.concepts[concept_id]
        uses = [(pair, recipe) for pair, recipe in world.recipes.items() if concept_id in pair]
        remaining = [(pair, recipe) for pair, recipe in uses if recipe.result not in owned]
        recipe = world.recipes.get(parents) if parents else None
        gift = next((u for u in world.catalog.unlocks if concept_id in u.concept_ids), None)
        inventory.append({
            **_concept(session, concept_id), "description": concept.description,
            "parents": [_concept(session, item) for item in parents] if parents else None,
            "explanation": recipe.explanation if recipe else gift.title if gift else None,
            "sources": recipe.sources if recipe else [],
            "status": "final" if not uses else "active" if remaining else "depleted",
            "ready": any(set(pair) <= owned.keys() for pair, _ in remaining),
        })
    pending = sorted((u for u in world.catalog.unlocks if u.id not in session.unlocked),
                     key=lambda u: u.after_discoveries)
    next_unlock = pending[0] if pending else None
    return {
        "game_id": game_id, "revision": session.revision, "mode": "explore",
        "compatible_recipe_hashes": list(world.compatible_versions),
        "empty_pairs": [list(pair) for pair in session.empty_pairs],
        "world": {
            "id": world.id, "title": world.catalog.world.title,
            "description": world.catalog.world.description,
            "total_concepts": len(world.concepts), "total_recipes": len(world.recipes),
        },
        "inventory": inventory, "discovered_count": len(session.discoveries),
        "seed_count": len(world.catalog.world.starter_ids),
        "complete": len(owned) == len(world.concepts), "goal_id": session.goal_id,
        "goals": [{"id": goal.id, "title": goal.title,
                   "label": world.concepts[goal.target].label,
                   "completed": goal.target in owned,
                   "target_id": goal.target if goal.target in owned else None}
                  for goal in world.goals.values()],
        "hint": _hint_payload(session),
        "unlocked": [{"id": u.id, "title": u.title, "after_discoveries": u.after_discoveries}
                     for u in world.catalog.unlocks if u.id in session.unlocked],
        "next_unlock": ({"title": next_unlock.title,
                         "after_discoveries": next_unlock.after_discoveries,
                         "remaining": next_unlock.after_discoveries - len(session.discoveries)}
                        if next_unlock else None),
        "progress": {"world_id": world.id, "recipe_hash": world.recipe_hash,
                     "discoveries": [list(p) for p in session.discoveries]},
    }


def restore_session(world: DiscoveryWorld, progress: Progress | None,
                    goal_id: str | None = None) -> ExploreSession:
    """Validate saves against their original rules, then preserve them in the new world."""
    session = ExploreSession(world=world, goal_id=goal_id)
    session.owned.update(dict.fromkeys(world.catalog.world.starter_ids))
    if progress is None:
        return session
    version = world.compatible_versions.get(progress.recipe_hash)
    if progress.world_id != world.id or (progress.recipe_hash != world.recipe_hash and not version):
        raise http_error(409, "Colecția aparține altei versiuni. Salvarea rămâne păstrată.")
    mechanics = version.mechanics.model_dump() if version else world.mechanics
    recipes = {tuple(r["pair"]): r["result"] for r in mechanics["recipes"]}
    owned = set(mechanics["starters"])
    crafted: set[str] = set()
    validated: list[tuple[str, str]] = []
    for raw_pair in progress.discoveries:
        if len(raw_pair) != 2:
            raise http_error(400, "Colecția salvată conține o combinație invalidă.")
        pair = tuple(sorted(raw_pair))
        if pair[0] == pair[1] or not set(pair) <= owned:
            raise http_error(400, "Colecția salvată folosește ingrediente încă nedescoperite.")
        result = recipes.get(pair)
        if result is None:
            raise http_error(400, "Colecția salvată conține o rețetă necunoscută.")
        if result not in owned:
            owned.add(result)
            crafted.add(result)
            validated.append(pair)
            for unlock in mechanics["unlocks"]:
                if len(crafted) >= unlock["after"]:
                    owned.update(unlock["concepts"])
    for pair in validated:
        session.craft(pair)
    # Compatible archives are strictly additive; no earned concept may disappear.
    if not owned <= session.owned.keys():
        raise http_error(409, "Colecția nu poate fi actualizată. Salvarea rămâne păstrată.")
    return session


def _upgrade_session(session: ExploreSession) -> None:
    """Existing tabs receive additive content before reads and mutations, atomically."""
    try:
        current = get_world()
    except (OSError, ValueError):
        return  # An already validated pinned world remains playable during a failed update.
    if current.recipe_hash == session.world.recipe_hash:
        return
    if (current.id != session.world.id
            or session.world.recipe_hash not in current.compatible_versions):
        return  # Incompatible versions require explicit migration; never replace earned results.
    fresh = restore_session(current, Progress(
        world_id=session.world.id, recipe_hash=session.world.recipe_hash,
        discoveries=[list(pair) for pair in session.discoveries],
    ), session.goal_id)
    if fresh.goal_id not in current.goals:
        fresh.goal_id = None
    session.world, session.owned = fresh.world, fresh.owned
    session.discoveries, session.unlocked = fresh.discoveries, fresh.unlocked
    session.goal_id = fresh.goal_id
    # A formerly empty pair can gain a recipe in a compatible new book.
    session.empty_pairs.clear()
    # Existing hints remain valid because every previous pair/result is preserved.
    if session.hint_pair is None:
        session.hint_stage = 0  # A previously complete collection can now explore again.
    session.revision += 1


def _useful_pair(session: ExploreSession) -> tuple[str, str] | None:
    available = [(pair, r) for pair, r in session.world.recipes.items()
                 if set(pair) <= session.owned.keys() and r.result not in session.owned]
    if not available:
        return None
    # Prefer an available step toward the optional goal. Explore elsewhere once earned.
    ancestors: set[str] = set()
    if session.goal_id:
        target = session.world.goals[session.goal_id].target
        if target not in session.owned:
            ancestors.add(target)
            while True:
                previous = len(ancestors)
                for pair, recipe in session.world.recipes.items():
                    if recipe.result in ancestors:
                        ancestors.update(pair)
                if len(ancestors) == previous:
                    break
    return min(available, key=lambda item: (item[1].result not in ancestors, item[1].id))[0]


class CreateExploreView(ContractAPIView):
    @extend_schema(operation_id="alchimie_explore_create", tags=["alchimie"])
    def post(self, request):
        body = parse_body(request, CreateBody)
        try:
            world = get_world()
        except (OSError, ValueError) as exc:
            raise http_error(503, "Lumea de explorat nu este disponibilă momentan.") from exc
        if body.goal_id is not None and body.goal_id not in world.goals:
            raise http_error(400, "Obiectiv necunoscut.")
        session = restore_session(world, body.progress, body.goal_id)
        try:
            game_id = store.create(session)
        except SessionCapacityError as exc:
            raise http_error(503, "Prea multe explorări active. Încearcă din nou.") from exc
        return Response(state_payload(game_id, session))


class GetExploreView(ContractAPIView):
    @extend_schema(operation_id="alchimie_explore_get", tags=["alchimie"])
    @_atomic_session
    def get(self, request, game_id: str, session: ExploreSession):
        _upgrade_session(session)
        return Response(state_payload(game_id, session))


class CombineExploreView(ContractAPIView):
    @extend_schema(operation_id="alchimie_explore_combine", tags=["alchimie"])
    @_atomic_session
    def post(self, request, game_id: str, session: ExploreSession):
        body = parse_body(request, PairBody)
        _upgrade_session(session)
        pair = tuple(sorted((body.a, body.b)))
        result, new, supplies = session.craft(pair)
        session.revision += 1
        if result is None:
            if pair not in session.empty_pairs:
                if len(session.empty_pairs) >= MAX_EMPTY_PAIRS:
                    session.empty_pairs.pop(next(iter(session.empty_pairs)))
                session.empty_pairs[pair] = None
            message = "Perechea nu are încă o rețetă. Încearcă alt ingredient; nu pierzi nimic."
        elif new:
            message = f"Ai descoperit {session.world.concepts[result].label}!"
        else:
            message = f"Ai deja {session.world.concepts[result].label} în colecție."
        if supplies:
            message += " Ai primit provizii noi în cămară!"
        return Response({
            **state_payload(game_id, session), "message": message,
            "discovered": [_concept(session, result)] if new else [],
            "result": _concept(session, result) if result else None,
            "supplied": [_concept(session, item) for item in supplies],
            "already_known": result is not None and not new,
        })


class HintExploreView(ContractAPIView):
    @extend_schema(operation_id="alchimie_explore_hint", tags=["alchimie"])
    @_atomic_session
    def post(self, request, game_id: str, session: ExploreSession):
        _upgrade_session(session)
        if session.hint_pair is None:
            session.hint_pair = _useful_pair(session)
        session.hint_stage = min(2, session.hint_stage + 1)
        session.revision += 1
        return Response(state_payload(game_id, session))


class GoalExploreView(ContractAPIView):
    @extend_schema(operation_id="alchimie_explore_goal", tags=["alchimie"])
    @_atomic_session
    def post(self, request, game_id: str, session: ExploreSession):
        body = parse_body(request, GoalBody)
        _upgrade_session(session)
        if body.goal_id is not None and body.goal_id not in session.world.goals:
            raise http_error(400, "Obiectiv necunoscut.")
        session.goal_id = body.goal_id
        session.hint_pair, session.hint_stage = None, 0
        session.revision += 1
        return Response(state_payload(game_id, session))


_BASE = "api/alchimie/explore"
urlpatterns = [
    path(_BASE, CreateExploreView.as_view()),
    path(f"{_BASE}/<str:game_id>", GetExploreView.as_view()),
    path(f"{_BASE}/<str:game_id>/combine", CombineExploreView.as_view()),
    path(f"{_BASE}/<str:game_id>/hint", HintExploreView.as_view()),
    path(f"{_BASE}/<str:game_id>/goal", GoalExploreView.as_view()),
]
