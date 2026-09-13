"""A reviewed, goal-independent recipe world; never inferred from graph similarity."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from functools import cached_property, lru_cache
from pathlib import Path
from typing import Annotated
from urllib.parse import urlparse

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from .recipe_extensions import record_snapshot
from .service import get_service

CATALOG_PATH = Path(__file__).resolve().parents[1] / "fixtures/alchimie_discovery_world_v92.json"
MAX_CONCEPTS = 128
MAX_RECIPES = 512
MAX_CATALOG_BYTES = 2 * 1024 * 1024
Identifier = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=160)]
Text = Annotated[str, StringConstraints(strict=True, min_length=1, max_length=2000)]
Sha = Annotated[str, StringConstraints(pattern=r"^[a-f0-9]{64}$")]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class WorldInfo(Record):
    id: Identifier
    title: Text
    description: Text
    starter_ids: list[Identifier] = Field(min_length=2, max_length=12)


class Concept(Record):
    id: Identifier
    label: Text
    description: str
    source: str
    redistributable: bool
    snapshot: dict


class Recipe(Record):
    id: Identifier
    pair: list[Identifier] = Field(min_length=2, max_length=2)
    result: Identifier
    explanation: Text
    sources: list[Text] = Field(min_length=1, max_length=8)


class Goal(Record):
    id: Identifier
    target: Identifier
    title: Text


class Unlock(Record):
    id: Identifier
    after_discoveries: int = Field(ge=1, le=MAX_CONCEPTS)
    concept_ids: list[Identifier] = Field(min_length=1, max_length=12)
    title: Text


class Review(Record):
    role: str
    reviewer: Text
    candidate_sha256: Sha
    sha256: Sha


class MechanicRecipe(Record):
    pair: list[Identifier] = Field(min_length=2, max_length=2)
    result: Identifier


class MechanicUnlock(Record):
    after: int = Field(ge=1, le=MAX_CONCEPTS)
    concepts: list[Identifier] = Field(min_length=1, max_length=12)


class Mechanics(Record):
    starters: list[Identifier] = Field(min_length=2, max_length=12)
    recipes: list[MechanicRecipe] = Field(min_length=2, max_length=MAX_RECIPES)
    unlocks: list[MechanicUnlock] = Field(max_length=8)


class CompatibleVersion(Record):
    world_id: Identifier
    recipe_hash: Sha
    source_sha256: Sha
    mechanics: Mechanics


class Catalog(BaseModel):
    # Generator may append audit metadata. All serving records are strict.
    model_config = ConfigDict(strict=True)
    schema_version: int
    world: WorldInfo
    concepts: list[Concept] = Field(min_length=3, max_length=MAX_CONCEPTS)
    recipes: list[Recipe] = Field(min_length=2, max_length=MAX_RECIPES)
    goals: list[Goal] = Field(max_length=32)
    unlocks: list[Unlock] = Field(default_factory=list, max_length=8)
    candidate_sha256: Sha
    bindings: dict[str, Sha]
    reviews: list[Review] = Field(min_length=2, max_length=2)
    compatible_versions: list[CompatibleVersion] = Field(default_factory=list, max_length=8)


def mechanics_for(starters, recipes, unlocks) -> dict:
    """Canonical mechanics shared by current fingerprints and archived save versions."""
    return {
        "starters": sorted(starters),
        "recipes": [{"pair": list(pair), "result": result}
                    for pair, result in sorted(recipes.items())],
        "unlocks": sorted(
            [{"after": after, "concepts": sorted(ids)} for after, ids in unlocks],
            key=lambda u: (u["after"], u["concepts"]),
        ),
    }


def mechanics_hash(mechanics: dict) -> str:
    return hashlib.sha256(json.dumps(
        mechanics, sort_keys=True, separators=(",", ":"),
    ).encode()).hexdigest()


@dataclass(frozen=True)
class DiscoveryWorld:
    catalog: Catalog
    concepts: dict[str, Concept]
    recipes: dict[tuple[str, str], Recipe]
    goals: dict[str, Goal]

    @property
    def id(self) -> str:
        return self.catalog.world.id

    @cached_property
    def mechanics(self) -> dict:
        return mechanics_for(
            self.catalog.world.starter_ids,
            {pair: recipe.result for pair, recipe in self.recipes.items()},
            [(u.after_discoveries, u.concept_ids) for u in self.catalog.unlocks],
        )

    @cached_property
    def recipe_hash(self) -> str:
        """Bind portable progress to mechanics, permitting harmless copy/goal edits."""
        return mechanics_hash(self.mechanics)

    @cached_property
    def compatible_versions(self) -> dict[str, CompatibleVersion]:
        return {v.recipe_hash: v for v in self.catalog.compatible_versions}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(f"Alchimie discovery world: {message}")


def validate_world(raw: dict, *, check_graph: bool = True) -> DiscoveryWorld:
    """Validate the entire book, including reachability through automatic supplies."""
    catalog = Catalog.model_validate(raw)
    _require(catalog.schema_version == 1, "unsupported schema")
    _require({r.role for r in catalog.reviews} == {"factual", "quality"}, "review roles")
    _require(len({r.reviewer for r in catalog.reviews}) == 2, "independent reviewers")
    _require(all(r.candidate_sha256 == catalog.candidate_sha256 for r in catalog.reviews),
             "review candidate mismatch")
    _require({"kg_sha256", "rubric_sha256"} <= catalog.bindings.keys(), "source bindings")
    concepts = {c.id: c for c in catalog.concepts}
    _require(len(concepts) == len(catalog.concepts), "duplicate concept")
    supplied = set(catalog.world.starter_ids)
    _require(len(supplied) == len(catalog.world.starter_ids), "duplicate starter")
    unlock_ids: set[str] = set()
    for unlock in catalog.unlocks:
        _require(unlock.id not in unlock_ids, "duplicate unlock")
        unlock_ids.add(unlock.id)
        ids = set(unlock.concept_ids)
        _require(len(ids) == len(unlock.concept_ids) and not ids & supplied,
                 "duplicate supply")
        supplied.update(ids)
    _require(supplied <= concepts.keys()
             and len(supplied) - len(catalog.world.starter_ids) <= 48, "invalid supplies")
    recipes: dict[tuple[str, str], Recipe] = {}
    recipe_ids: set[str] = set()
    for recipe in catalog.recipes:
        pair = tuple(sorted(recipe.pair))
        _require(pair[0] != pair[1] and pair not in recipes, "duplicate or self pair")
        _require(recipe.id not in recipe_ids, "duplicate recipe id")
        recipe_ids.add(recipe.id)
        _require(set(pair) | {recipe.result} <= concepts.keys(), "unknown recipe concept")
        _require(recipe.result not in pair and recipe.result not in supplied,
                 "recipe recreates ingredient or supply")
        for source in recipe.sources:
            url = urlparse(source)
            _require(url.scheme in {"http", "https"} and bool(url.netloc), "source URL")
        recipes[pair] = recipe
    goals = {g.id: g for g in catalog.goals}
    _require(len(goals) == len(catalog.goals), "duplicate goal")
    _require(all(g.target in concepts and g.target not in supplied for g in goals.values()),
             "invalid goal target")
    _require(len({g.target for g in goals.values()}) == len(goals), "duplicate goal target")

    owned = set(catalog.world.starter_ids)
    crafted: set[str] = set()
    while True:
        previous = len(owned)
        for pair, recipe in recipes.items():
            if set(pair) <= owned and recipe.result not in owned:
                crafted.add(recipe.result)
                owned.add(recipe.result)
        for unlock in catalog.unlocks:
            if len(crafted) >= unlock.after_discoveries:
                owned.update(unlock.concept_ids)
        if len(owned) == previous:
            break
    _require(owned == concepts.keys(), "unreachable concepts or supplies")
    _require(all(len(crafted) >= u.after_discoveries for u in catalog.unlocks),
             "unreachable unlock threshold")
    _require(all(any(seed in pair for pair in recipes) for seed in supplied),
             "unused starter or supply")
    world = DiscoveryWorld(catalog, concepts, recipes, goals)
    _validate_compatibility(world)
    if check_graph:
        _check_graph(world)
    return world


def _validate_compatibility(world: DiscoveryWorld) -> None:
    """Accept only explicit additive archives, never arbitrary old fingerprints."""
    versions = world.catalog.compatible_versions
    _require(len(world.compatible_versions) == len(versions), "duplicate compatible version")
    current = world.mechanics
    for version in versions:
        old = version.mechanics.model_dump()
        old_pairs = {tuple(r.pair): r.result for r in version.mechanics.recipes}
        canonical = mechanics_for(
            old["starters"], old_pairs,
            [(u.after, u.concepts) for u in version.mechanics.unlocks],
        )
        _require(old == canonical and mechanics_hash(old) == version.recipe_hash,
                 "invalid archived mechanics fingerprint")
        _require(version.world_id == world.id and version.recipe_hash != world.recipe_hash,
                 "invalid compatible world identity")
        _require(old["starters"] == current["starters"], "changed historical starters")
        _require(len(old_pairs) == len(old["recipes"]) and all(
            pair in world.recipes and world.recipes[pair].result == result
            for pair, result in old_pairs.items()
        ), "changed historical recipe")
        _require(all(u in current["unlocks"] for u in old["unlocks"]),
                 "changed historical supplies")
        supplied = [n for u in old["unlocks"] for n in u["concepts"]]
        _require(len(supplied) == len(set(supplied)) and not set(supplied) & set(old["starters"]),
                 "duplicate historical supply")
        owned = set(old["starters"])
        crafted: set[str] = set()
        while True:
            previous = len(owned)
            for pair, result in old_pairs.items():
                if set(pair) <= owned and result not in owned:
                    owned.add(result)
                    crafted.add(result)
            for unlock in old["unlocks"]:
                if len(crafted) >= unlock["after"]:
                    owned.update(unlock["concepts"])
            if len(owned) == previous:
                break
        expected = set(old["starters"]) | set(supplied) | set(old_pairs.values())
        expected.update(n for pair in old_pairs for n in pair)
        _require(owned == expected and all(len(crafted) >= u["after"] for u in old["unlocks"]),
                 "unreachable historical mechanics")


def _check_graph(world: DiscoveryWorld) -> None:
    service = get_service()
    for concept in world.concepts.values():
        node = service.node(concept.id)
        _require(node is not None and record_snapshot(node) == concept.snapshot,
                 "concept source changed")
        # Public descriptions may contain independently reviewed world-local corrections.
        # The full original snapshot still binds every source field, including its text.
        _require((concept.label, concept.source, concept.redistributable)
                 == (node.label_ro, node.source, node.redistributable),
                 "concept presentation differs from source")


@lru_cache(maxsize=1)
def _load_world(path: str, modified_ns: int, size: int) -> DiscoveryWorld:
    del modified_ns, size  # Included in cache identity, never serialized.
    data = Path(path).read_bytes()
    _require(len(data) <= MAX_CATALOG_BYTES, "catalog too large")
    return validate_world(json.loads(data), check_graph=False)


def get_world() -> DiscoveryWorld:
    stat = CATALOG_PATH.stat()
    _require(stat.st_size <= MAX_CATALOG_BYTES, "catalog too large")
    world = _load_world(str(CATALOG_PATH), stat.st_mtime_ns, stat.st_size)
    _check_graph(world)
    return world
