//! Native, bounded Alchimie challenge projection, mining and authoritative actions.
use crate::{
    ApiError,
    catalog::daily_seed,
    content::Content,
    graph,
    pack::{Pack, PickOptions},
    pyrandom::Random,
    session::Store,
};
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet, HashMap, VecDeque},
    sync::{Arc, Mutex},
};

pub type Pair = [String; 2];
#[derive(Clone, Debug, PartialEq, Eq, PartialOrd, Ord, Serialize, Deserialize)]
pub struct Step {
    pub pair: Pair,
    pub results: Vec<String>,
}
pub type Route = Vec<Step>;
#[derive(Clone, Debug)]
pub struct Projection {
    pub recipes: BTreeMap<Pair, Vec<String>>,
    pub routes: Vec<Route>,
    pub par: usize,
    pub candidate_quality: Vec<[f64; 3]>,
}
fn pair(a: &str, b: &str) -> Pair {
    if a < b {
        [a.into(), b.into()]
    } else {
        [b.into(), a.into()]
    }
}
fn sorted(xs: &[String]) -> Vec<String> {
    xs.iter()
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect()
}
fn union(a: &[String], b: &[String]) -> Vec<String> {
    let mut out = Vec::with_capacity(a.len() + b.len());
    let (mut i, mut j) = (0, 0);
    while i < a.len() && j < b.len() {
        match a[i].cmp(&b[j]) {
            std::cmp::Ordering::Less => {
                out.push(a[i].clone());
                i += 1
            }
            std::cmp::Ordering::Greater => {
                out.push(b[j].clone());
                j += 1
            }
            std::cmp::Ordering::Equal => {
                out.push(a[i].clone());
                i += 1;
                j += 1
            }
        }
    }
    out.extend_from_slice(&a[i..]);
    out.extend_from_slice(&b[j..]);
    out
}

fn has(xs: &[String], id: &str) -> bool {
    xs.binary_search_by(|x| x.as_str().cmp(id)).is_ok()
}
fn diff(a: &[String], b: &[String]) -> Vec<String> {
    a.iter().filter(|x| !has(b, x)).cloned().collect()
}
fn pairs(xs: &[String]) -> Vec<Pair> {
    let mut out = vec![];
    for (i, a) in xs.iter().enumerate() {
        for b in &xs[i + 1..] {
            out.push([a.clone(), b.clone()])
        }
    }
    out
}
pub fn minimum_plan(
    owned: &[String],
    target: &str,
    recipes: &BTreeMap<Pair, Vec<String>>,
    max_actions: usize,
) -> Option<Vec<Pair>> {
    let start = sorted(owned);
    if has(&start, target) {
        return Some(vec![]);
    };
    let mut frontier = BTreeMap::from([(start.clone(), vec![])]);
    let mut seen = BTreeSet::from([start]);
    for _ in 0..max_actions {
        let mut layer = BTreeMap::new();
        for (owned, plan) in &frontier {
            for (pair, outputs) in recipes {
                if !pair.iter().all(|id| has(owned, id)) {
                    continue;
                };
                let fresh = diff(outputs, owned);
                if fresh.is_empty() {
                    continue;
                };
                let mut next_plan = plan.clone();
                next_plan.push(pair.clone());
                if has(&fresh, target) {
                    return Some(next_plan);
                };
                let state = union(owned, &fresh);
                if !seen.contains(&state) && !layer.contains_key(&state) {
                    layer.insert(state, next_plan);
                }
            }
        }
        if layer.is_empty() {
            return None;
        };
        seen.extend(layer.keys().cloned());
        frontier = layer
    }
    None
}

fn quality(g: &graph::Service, route: &Route) -> (f64, f64, usize) {
    let mut strengths = vec![];
    let mut degree = 0;
    for step in route {
        for output in &step.results {
            degree = degree.max(g.degree(output));
            for parent in &step.pair {
                strengths.push(g.link(parent, output).map_or(0., |e| e.strength))
            }
        }
    }
    if strengths.is_empty() {
        return (0., 0., 0);
    };
    (
        strengths.iter().copied().fold(f64::INFINITY, f64::min),
        compensated_sum(&strengths) / strengths.len() as f64,
        degree,
    )
}
#[derive(Clone)]
struct Parent {
    previous: Arc<[usize]>,
    pair: [usize; 2],
    fresh: Arc<[usize]>,
}
fn integer_union(a: &[usize], b: &[usize]) -> Arc<[usize]> {
    let mut out = Vec::with_capacity(a.len() + b.len());
    let (mut i, mut j) = (0, 0);
    while i < a.len() && j < b.len() {
        if a[i] < b[j] {
            out.push(a[i]);
            i += 1
        } else if a[i] > b[j] {
            out.push(b[j]);
            j += 1
        } else {
            out.push(a[i]);
            i += 1;
            j += 1
        }
    }
    out.extend_from_slice(&a[i..]);
    out.extend_from_slice(&b[j..]);
    out.into()
}
fn indexed_route(
    g: &graph::Service,
    raw: &[([usize; 2], Arc<[usize]>)],
    seeds: &[usize],
    target: usize,
) -> Option<Route> {
    let mut required = BTreeSet::from([target]);
    let mut selected = vec![];
    for (pair, fresh) in raw.iter().rev() {
        let outputs: Vec<_> = fresh
            .iter()
            .filter(|id| required.contains(*id))
            .copied()
            .collect();
        if outputs.is_empty() || outputs.len() > 2 {
            return None;
        };
        for id in &outputs {
            required.remove(id);
        }
        for id in pair {
            if seeds.binary_search(id).is_err() {
                required.insert(*id);
            }
        }
        selected.push(Step {
            pair: [g.id_at(pair[0]).to_owned(), g.id_at(pair[1]).to_owned()],
            results: outputs.iter().map(|id| g.id_at(*id).to_owned()).collect(),
        })
    }
    if !required.is_empty() {
        return None;
    };
    selected.reverse();
    Some(selected)
}
pub fn build_projection(
    g: &graph::Service,
    seeds: &[String],
    target: &str,
    category: &str,
) -> Option<Projection> {
    // Numeric indices follow the graph's ID-sorted order, retaining Python's
    // exact tuple ordering while each immutable inventory is allocated only once.
    let target_index = g.index(target)?;
    let mut seed_indices: Vec<_> = seeds
        .iter()
        .map(|id| g.index(id))
        .collect::<Option<Vec<_>>>()?;
    seed_indices.sort_unstable();
    seed_indices.dedup();
    let start: Arc<[usize]> = seed_indices.into();
    let mut frontier = BTreeSet::from([Arc::clone(&start)]);
    let mut seen = frontier.clone();
    let mut parents: BTreeMap<Arc<[usize]>, Parent> = BTreeMap::new();
    let mut candidates: Vec<Route> = vec![];
    let mut candidate_set = BTreeSet::new();
    let (mut minimum, mut count, mut exhausted) = (0, 1, false);
    let mut pair_results: HashMap<[usize; 2], Arc<[usize]>> = HashMap::new();
    for action in 1..=6 {
        if minimum > 0 && action > minimum + 2 {
            break;
        };
        let mut layer = BTreeSet::new();
        for owned in &frontier {
            'pairs: for (i, &a) in owned.iter().enumerate() {
                for &b in &owned[i + 1..] {
                    let pair = [a, b];
                    let results = if let Some(r) = pair_results.get(&pair) {
                        Arc::clone(r)
                    } else {
                        let ids: Vec<_> = g
                            .common_neighbors(g.id_at(a), g.id_at(b), category)
                            .iter()
                            .filter_map(|id| g.index(id))
                            .collect();
                        let r: Arc<[usize]> = ids.into();
                        if pair_results.len() < 4096 {
                            pair_results.insert(pair, Arc::clone(&r));
                        };
                        r
                    };
                    if results.is_empty() {
                        continue;
                    }
                    let fresh_values: Vec<_> = results
                        .iter()
                        .filter(|id| owned.binary_search(id).is_err())
                        .copied()
                        .collect();
                    if fresh_values.is_empty() {
                        continue;
                    };
                    let fresh: Arc<[usize]> = fresh_values.into();
                    if fresh.binary_search(&target_index).is_ok() {
                        if minimum == 0 {
                            minimum = action
                        };
                        let mut raw = vec![(pair, Arc::clone(&fresh))];
                        let mut state = Arc::clone(owned);
                        while state != start {
                            let p = &parents[&state];
                            raw.push((p.pair, Arc::clone(&p.fresh)));
                            state = Arc::clone(&p.previous)
                        }
                        raw.reverse();
                        if let Some(route) = indexed_route(g, &raw, &start, target_index)
                            && candidate_set.insert(route.clone())
                        {
                            candidates.push(route)
                        };
                        if candidates.len() >= 128 {
                            exhausted = true;
                            break 'pairs;
                        };
                        continue;
                    }
                    let state = integer_union(owned, &fresh);
                    if seen.contains(&state) || layer.contains(&state) {
                        continue;
                    };
                    count += 1;
                    if count > 50000 {
                        exhausted = true;
                        break 'pairs;
                    };
                    parents.insert(
                        Arc::clone(&state),
                        Parent {
                            previous: Arc::clone(owned),
                            pair,
                            fresh,
                        },
                    );
                    layer.insert(state);
                }
            }
            if exhausted {
                break;
            }
        }
        if exhausted || layer.is_empty() {
            break;
        };
        seen.extend(layer.iter().cloned());
        frontier = layer;
    }
    if minimum == 0 || candidates.is_empty() {
        return None;
    };
    // Decorate once, matching Python sort(key=...). Graph work in a sort
    // comparator multiplies cold recipe-search cost without changing the answer.
    let mut decorated: Vec<_> = candidates
        .into_iter()
        .map(|route| {
            let q = quality(g, &route);
            (route, q)
        })
        .collect();
    decorated.sort_by(|(a, (amin, aavg, ad)), (b, (bmin, bavg, bd))| {
        a.len()
            .cmp(&b.len())
            .then_with(|| bmin.total_cmp(amin))
            .then_with(|| bavg.total_cmp(aavg))
            .then(ad.cmp(bd))
            .then(a.cmp(b))
    });
    let candidate_quality = decorated
        .iter()
        .map(|(r, (low, avg, _))| [r.len() as f64, *low, *avg])
        .collect();
    let mut projection = Projection {
        recipes: BTreeMap::new(),
        routes: vec![],
        par: minimum,
        candidate_quality,
    };
    for (route, (low, _, _)) in decorated {
        if !projection.routes.is_empty() && low < 0.55 {
            continue;
        };
        let mut merged = projection.recipes.clone();
        let mut compatible = true;
        for step in &route {
            if let Some(existing) = merged.get(&step.pair)
                && existing.len() == 1
                && step.results.len() == 1
                && existing != &step.results
            {
                compatible = false;
                break;
            };
            let output = union(
                merged.get(&step.pair).map_or(&[], Vec::as_slice),
                &step.results,
            );
            if output.len() > 2 {
                compatible = false;
                break;
            };
            merged.insert(step.pair.clone(), output);
        }
        if !compatible {
            continue;
        };
        if !projection.routes.is_empty()
            && route.iter().all(|step| {
                step.results.iter().all(|id| {
                    projection
                        .recipes
                        .get(&step.pair)
                        .is_some_and(|outputs| has(outputs, id))
                })
            })
        {
            continue;
        };
        let mut projected: BTreeSet<_> = seeds.iter().cloned().collect();
        for (pair, outputs) in &merged {
            projected.extend(pair.clone());
            projected.extend(outputs.clone());
        }
        if merged.len() > 24 || projected.len() > 32 {
            continue;
        };
        projection.recipes = merged;
        projection.routes.push(route);
        if projection.routes.len() >= 4 {
            break;
        }
    }
    if projection.routes.is_empty()
        || minimum_plan(seeds, target, &projection.recipes, 6).is_none_or(|p| p.len() != minimum)
    {
        return None;
    };
    Some(projection)
}
fn sample(rng: &mut Random, population: &[String], k: usize) -> Vec<String> {
    let mut out = vec![];
    let mut set_size = 21;
    if k > 5 {
        let mut power = 4;
        while power < k * 3 {
            power *= 4
        }
        set_size += power
    };
    if population.len() <= set_size {
        let mut pool = population.to_vec();
        for i in 0..k {
            let j = rng.randbelow(population.len() - i);
            out.push(pool[j].clone());
            pool[j] = pool[population.len() - i - 1].clone();
        }
    } else {
        let mut selected = BTreeSet::new();
        for _ in 0..k {
            let mut j = rng.randbelow(population.len());
            while selected.contains(&j) {
                j = rng.randbelow(population.len())
            }
            selected.insert(j);
            out.push(population[j].clone());
        }
    };
    out
}
struct GameSession {
    seeds: Vec<String>,
    target: String,
    difficulty: String,
    daily: String,
    category: String,
    owned: BTreeMap<String, Option<Pair>>,
    order: Vec<String>,
    moves: usize,
    fruitless_streak: usize,
    fruitless_total: usize,
    hints_used: usize,
    earned_hint: Option<Value>,
    projection: Arc<Projection>,
    attempted: BTreeSet<Pair>,
}
impl GameSession {
    fn new(
        seeds: Vec<String>,
        target: String,
        projection: Arc<Projection>,
        difficulty: &str,
        daily: &str,
        category: &str,
    ) -> Self {
        let mut game = Self {
            seeds: seeds.clone(),
            target,
            difficulty: difficulty.into(),
            daily: daily.into(),
            category: category.into(),
            owned: BTreeMap::new(),
            order: vec![],
            moves: 0,
            fruitless_streak: 0,
            fruitless_total: 0,
            hints_used: 0,
            earned_hint: None,
            projection,
            attempted: BTreeSet::new(),
        };
        for id in seeds {
            game.add(id, None)
        }
        game
    }
    fn add(&mut self, id: String, p: Option<Pair>) {
        if !self.owned.contains_key(&id) {
            self.order.push(id.clone());
            self.owned.insert(id, p);
        }
    }
    fn won(&self) -> bool {
        self.owned.contains_key(&self.target)
    }
    fn score(&self) -> usize {
        1000usize
            .saturating_sub(
                120 * self
                    .moves
                    .saturating_sub(self.fruitless_total + self.projection.par)
                    + 150 * self.hints_used,
            )
            .max(100)
    }
}
type CacheKey = (Vec<String>, String, String);
#[derive(Default)]
struct Cache {
    entries: BTreeMap<CacheKey, Option<Arc<Projection>>>,
    order: VecDeque<CacheKey>,
}
pub struct Alchimie {
    content: Arc<Content>,
    graph: Arc<graph::Service>,
    pack: Pack,
    store: Store<GameSession>,
    cache: Mutex<Cache>,
}
impl Alchimie {
    pub fn new(content: Arc<Content>) -> Self {
        Self {
            graph: graph::Service::new(Arc::clone(&content)),
            pack: Pack::new(Arc::clone(&content)),
            content,
            store: Store::new(),
            cache: Mutex::new(Cache::default()),
        }
    }
    fn projection(
        &self,
        seeds: &[String],
        target: &str,
        category: &str,
    ) -> Option<Arc<Projection>> {
        let key = (seeds.to_vec(), target.into(), category.into());
        {
            let mut cache = self.cache.lock().unwrap_or_else(|e| e.into_inner());
            if let Some(value) = cache.entries.get(&key).cloned() {
                cache.order.retain(|k| k != &key);
                cache.order.push_back(key);
                return value;
            }
        };
        let value = build_projection(&self.graph, seeds, target, category)
            .and_then(|p| self.extend(p, seeds, target, category))
            .map(Arc::new);
        let mut cache = self.cache.lock().unwrap_or_else(|e| e.into_inner());
        if !cache.entries.contains_key(&key)
            && cache.entries.len() >= 512
            && let Some(old) = cache.order.pop_front()
        {
            cache.entries.remove(&old);
        };
        cache.order.retain(|k| k != &key);
        cache.order.push_back(key.clone());
        cache.entries.insert(key, value.clone());
        value
    }
    fn extend(
        &self,
        core: Projection,
        seeds: &[String],
        target: &str,
        category: &str,
    ) -> Option<Projection> {
        let recipes: Vec<_> = core
            .recipes
            .iter()
            .map(|(pair, results)| Step {
                pair: pair.clone(),
                results: results.clone(),
            })
            .collect();
        let record = json!({"seeds":seeds,"target":target,"category":category,"par":core.par,"recipes":recipes,"routes":core.routes});
        for board in self.content.recipe_extensions["boards"]
            .as_array()
            .into_iter()
            .flatten()
        {
            if board["core"] != record {
                continue;
            };
            for (id, expected) in board["nodes"].as_object().into_iter().flatten() {
                if self
                    .graph
                    .node(id)
                    .and_then(|n| serde_json::to_value(n).ok())
                    .as_ref()
                    != Some(expected)
                {
                    return Some(core);
                }
            }
            for expected in board["edges"]
                .as_object()
                .into_iter()
                .flat_map(|m| m.values())
            {
                if self
                    .graph
                    .link(expected["src_id"].as_str()?, expected["dst_id"].as_str()?)
                    .and_then(|e| serde_json::to_value(e).ok())
                    .as_ref()
                    != Some(expected)
                {
                    return Some(core);
                }
            }
            let mut merged = core.clone();
            for addition in board["additions"].as_array().into_iter().flatten() {
                let p = pair(addition["pair"][0].as_str()?, addition["pair"][1].as_str()?);
                let result = addition["result"].as_str()?;
                if !has(&self.graph.common_neighbors(&p[0], &p[1], category), result) {
                    return Some(core);
                };
                merged.recipes.insert(p, vec![result.into()]);
            }
            if minimum_plan(seeds, target, &merged.recipes, core.par)
                .is_none_or(|p| p.len() != core.par)
            {
                return None;
            };
            return Some(merged);
        }
        Some(core)
    }
    fn closure(&self, seeds: &[String], category: &str) -> (BTreeMap<String, usize>, Vec<String>) {
        let mut generation: BTreeMap<_, _> = seeds.iter().map(|id| (id.clone(), 0)).collect();
        let mut order = seeds.to_vec();
        let mut owned = sorted(seeds);
        for depth in 1.. {
            let mut fresh = vec![];
            let mut found = BTreeSet::new();
            for p in pairs(&owned) {
                for id in self.graph.common_neighbors(&p[0], &p[1], category) {
                    if !has(&owned, &id) && found.insert(id.clone()) {
                        generation.insert(id.clone(), depth);
                        order.push(id.clone());
                        fresh.push(id);
                    }
                }
            }
            if fresh.is_empty() {
                break;
            };
            owned = union(&owned, &sorted(&fresh))
        }
        (generation, order)
    }
    fn grow(
        &self,
        rng: &mut Random,
        k: usize,
        pool: &[String],
        category: &str,
    ) -> Option<Vec<String>> {
        let starts: Vec<_> = pool
            .iter()
            .filter(|id| self.graph.degree(id) >= 3)
            .cloned()
            .collect();
        if starts.is_empty() || pool.len() < k {
            return None;
        };
        let mut owned = vec![starts[rng.randbelow(starts.len())].clone()];
        let mut attempts = 0;
        while owned.len() < k && attempts < 4000 {
            attempts += 1;
            let candidate = pool[rng.randbelow(pool.len())].clone();
            if owned.contains(&candidate) {
                continue;
            };
            let creates = owned.len() < 2
                || owned.iter().any(|id| {
                    self.graph
                        .common_neighbors(&candidate, id, category)
                        .iter()
                        .any(|result| result != &candidate && !owned.contains(result))
                });
            if creates {
                owned.push(candidate)
            }
        }
        (owned.len() == k).then_some(owned)
    }
    fn mine(
        &self,
        rng: &mut Random,
        difficulty: &str,
        daily: &str,
        category: &str,
    ) -> Result<GameSession, ApiError> {
        let (min_gen, max_gen, seed_min, seed_max) = match difficulty {
            "usor" => (2, 2, 6, 7),
            "greu" => (3, 5, 5, 5),
            _ => (2, 3, 5, 7),
        };
        let mut category = category.to_owned();
        if category.is_empty() {
            let usable: Vec<_> = self
                .content
                .category_labels
                .keys()
                .filter(|c| self.graph.by_category(c).len() >= 11)
                .cloned()
                .collect();
            if !usable.is_empty() {
                category = usable[rng.randbelow(usable.len())].clone()
            }
        };
        let in_scope = |id: &str| {
            category.is_empty() || self.graph.node(id).is_some_and(|n| n.category == category)
        };
        let mut pool: Vec<_> = self
            .graph
            .by_salience(0.4, true)
            .into_iter()
            .filter(|id| self.graph.degree(id) >= 2 && in_scope(id))
            .collect();
        if pool.len() < seed_max {
            pool = self
                .graph
                .all_ids()
                .into_iter()
                .filter(|id| self.graph.degree(id) >= 2 && in_scope(id))
                .collect()
        };
        if !category.is_empty() && pool.len() < seed_min {
            return Err(ApiError::new(
                503,
                "Nu există încă jocuri pentru această categorie.",
            ));
        };
        let finish = |seeds: Vec<String>, target: String| {
            self.projection(&seeds, &target, &category)
                .map(|p| GameSession::new(seeds, target, p, difficulty, daily, &category))
        };
        let mut relaxed = None;
        for _ in 0..400 {
            if pool.len() < seed_min {
                break;
            };
            let k = seed_min + rng.randbelow(seed_max.min(pool.len()) - seed_min + 1);
            let Some(seeds) = self.grow(rng, k, &pool, &category) else {
                continue;
            };
            let (generation, order) = self.closure(&seeds, &category);
            let mut candidates: Vec<_> = order
                .into_iter()
                .filter(|id| {
                    generation[id] >= min_gen
                        && generation[id] <= max_gen
                        && self.graph.salience(id) >= 0.4
                })
                .collect();
            if difficulty == "greu" {
                let deepest = candidates
                    .iter()
                    .map(|id| generation[id])
                    .max()
                    .unwrap_or(0);
                candidates.retain(|id| generation[id] == deepest)
            };
            if candidates.is_empty() {
                continue;
            };
            let target = candidates[rng.randbelow(candidates.len())].clone();
            let Some(game) = finish(seeds.clone(), target) else {
                continue;
            };
            let openings = pairs(&sorted(&seeds))
                .iter()
                .filter(|p| {
                    game.projection
                        .recipes
                        .get(*p)
                        .is_some_and(|out| !diff(out, &sorted(&seeds)).is_empty())
                })
                .count();
            if openings >= 2 {
                return Ok(game);
            };
            if relaxed.is_none() {
                relaxed = Some(game)
            }
        }
        if let Some(game) = relaxed {
            return Ok(game);
        };
        let fallback: Vec<_> = self
            .graph
            .all_ids()
            .into_iter()
            .filter(|id| self.graph.degree(id) >= 2 && in_scope(id))
            .collect();
        let seeds = sample(rng, &fallback, seed_max.min(fallback.len()));
        let (generation, order) = self.closure(&seeds, &category);
        let mut deep: Vec<_> = order.into_iter().filter(|id| generation[id] >= 2).collect();
        if deep.is_empty() {
            return Err(ApiError::new(
                if category.is_empty() { 500 } else { 503 },
                if category.is_empty() {
                    "Nu am putut genera un joc solvabil."
                } else {
                    "Nu există încă jocuri pentru această categorie."
                },
            ));
        };
        rng.shuffle(&mut deep);
        for target in deep {
            if let Some(game) = finish(seeds.clone(), target) {
                return Ok(game);
            }
        }
        Err(ApiError::new(
            503,
            "Nu există încă o țintă rezolvabilă în cel mult 6 mutări.",
        ))
    }
    pub fn create(
        &self,
        seed: Option<&str>,
        daily: &str,
        category: &str,
        difficulty: &str,
    ) -> Result<Value, ApiError> {
        let difficulty = if ["usor", "normal", "greu"].contains(&difficulty) {
            difficulty
        } else {
            "normal"
        };
        if !category.is_empty() && !self.content.category_labels.contains_key(category) {
            return Err(ApiError::new(400, "Categorie necunoscută."));
        };
        let mut rng = if !daily.is_empty() {
            Random::from_u64(daily_seed(daily, "alchimie"))
        } else if let Some(seed) = seed {
            Random::from_decimal(seed)
                .ok_or_else(|| ApiError::new(422, "seed trebuie să fie un număr întreg."))?
        } else {
            let mut bytes = [0; 32];
            getrandom::fill(&mut bytes)
                .map_err(|_| ApiError::new(503, "Jocul nu a putut fi creat. Încearcă din nou."))?;
            let words: Vec<_> = bytes
                .as_chunks::<4>()
                .0
                .iter()
                .map(|b| u32::from_le_bytes(*b))
                .collect();
            Random::from_words(&words)
        };
        let options = PickOptions {
            category: category.into(),
            difficulty: difficulty.into(),
            ..Default::default()
        };
        let item = if daily.is_empty() {
            self.pack.pick_seeded("alchimie", &mut rng, &options)
        } else {
            self.pack.pick_daily("alchimie", daily, &options)
        };
        let game = if let Some(item) = item {
            let seeds: Vec<String> = item.payload["seeds"]
                .as_array()
                .unwrap()
                .iter()
                .map(|id| id.as_str().unwrap().to_owned())
                .collect();
            let target = item.payload["target"].as_str().unwrap();
            let p = self
                .projection(&seeds, target, &item.category)
                .filter(|p| p.par == item.payload["target_depth"].as_u64().unwrap() as usize)
                .ok_or_else(|| {
                    ApiError::new(503, "Jocul ales nu are o proiecție de rețete validă.")
                })?;
            GameSession::new(seeds, target.into(), p, difficulty, daily, &item.category)
        } else {
            self.mine(&mut rng, difficulty, daily, category)?
        };
        let id = self
            .store
            .create(game)
            .map_err(|_| ApiError::new(503, "Prea multe jocuri active. Încearcă din nou."))?;
        self.get(&id)
    }
    fn concept(&self, id: &str) -> Value {
        json!({"id":id,"label":self.graph.label(id)})
    }
    fn state(&self, id: &str, g: &GameSession) -> Value {
        let owned = sorted(&g.order);
        let recent: BTreeSet<_> = g.order[g.order.len().saturating_sub(8)..].iter().collect();
        let mut useful = BTreeSet::new();
        let mut ready = BTreeSet::new();
        for (pair, outputs) in &g.projection.recipes {
            if diff(outputs, &owned).is_empty() {
                continue;
            };
            useful.extend(pair.iter().filter(|id| g.owned.contains_key(*id)).cloned());
            if pair.iter().all(|id| g.owned.contains_key(id)) {
                ready.extend(pair.clone())
            }
        }
        let inventory:Vec<_>=g.order.iter().map(|cid|{let parents=&g.owned[cid];let mut links=vec![];if let Some(pair)=parents{for parent in sorted(pair){if parent==*cid||!g.owned.contains_key(&parent){continue};let Some(e)=self.graph.link(&parent,cid)else{continue};if e.is_distractor||e.label_ro.trim().is_empty()||!((e.src==parent&&e.dst==*cid)||(e.src==*cid&&e.dst==parent)){continue};links.push(json!({"source":self.concept(&e.src),"target":self.concept(&e.dst),"label":e.label_ro}));}};json!({"id":cid,"label":self.graph.label(cid),"parents":parents.as_ref().map(|p|[self.concept(&p[0]),self.concept(&p[1])]),"links":links,"recent":recent.contains(cid),"useful":useful.contains(cid),"ready":ready.contains(cid),"depleted":!useful.contains(cid)})}).collect();
        let active = inventory.iter().filter(|x| x["depleted"] == false).count();
        let mut state = json!({"game_id":id,"target":{"id":if g.won(){Some(&g.target)}else{None},"label":self.graph.label(&g.target),"description":self.graph.description(&g.target),"revealed":g.won()},"inventory":inventory,"inventory_summary":{"active":active,"depleted":g.order.len()-active,"total":g.order.len()},"discovered_count":g.order.len().saturating_sub(g.seeds.len()),"seed_count":g.seeds.len(),"moves":g.moves,"attempted_count":g.attempted.len(),"difficulty":g.difficulty,"target_depth":g.projection.par,"won":g.won(),"hints_used":g.hints_used,"hint_stage":if g.hints_used==0{"output"}else{"pair"},"hint_available":!g.won()&&g.fruitless_streak>=2,"recipe_summary":{"pairs":g.projection.recipes.len(),"routes":g.projection.routes.len(),"max_results":g.projection.recipes.values().map(Vec::len).max().unwrap_or(0)}});
        if let Some(h) = &g.earned_hint {
            state["earned_hint"] = h.clone()
        };
        if !g.daily.is_empty() {
            state["daily"] = json!(g.daily)
        };
        if !g.category.is_empty() {
            state["board_category"] = json!(g.category)
        };
        if g.won() {
            state["score"] = json!(g.score());
            let mut header = "cat_de_roman_esti · Alchimie".to_owned();
            if !g.category.is_empty() {
                header.push_str(" · ");
                header.push_str(&self.content.category_labels[&g.category])
            };
            let perfect = g.moves - g.fruitless_total <= g.projection.par && g.hints_used == 0;
            let mut share = format!(
                "{header}\n⚗️ {} {} · {} pct {}",
                g.moves,
                if g.moves == 1 {
                    "combinație"
                } else {
                    "combinații"
                },
                g.score(),
                if perfect { "✨" } else { "⚗️" }
            );
            if g.hints_used > 0 {
                share.push_str(&format!("\n💡 x{}", g.hints_used))
            };
            if !g.daily.is_empty() {
                share.push('\n');
                share.push_str(&g.daily)
            };
            state["share"] = json!(share)
        };
        state
    }
    fn transact(
        &self,
        id: &str,
        work: impl FnOnce(&mut GameSession) -> Result<Value, ApiError>,
    ) -> Result<Value, ApiError> {
        self.store
            .transaction(id, work)
            .ok_or_else(|| ApiError::new(404, "Joc inexistent."))?
    }
    pub fn get(&self, id: &str) -> Result<Value, ApiError> {
        self.transact(id, |g| Ok(self.state(id, g)))
    }
    pub fn combine(&self, id: &str, a: &str, b: &str) -> Result<Value, ApiError> {
        self.combine_input(id, || Ok((a.to_owned(), b.to_owned())))
    }
    pub fn combine_input(
        &self,
        id: &str,
        input: impl FnOnce() -> Result<(String, String), ApiError>,
    ) -> Result<Value, ApiError> {
        self.transact(id, |g| {
            let (a, b) = input()?;
            let (a, b) = (py_strip(&a), py_strip(&b));
            let key = pair(a, b);
            if g.won() {
                let mut p = self.state(id, g);
                p["discovered"] = json!([]);
                p["already_tried"] =
                    json!(!a.is_empty() && !b.is_empty() && a != b && g.attempted.contains(&key));
                p["message"] = json!("Jocul s-a terminat — ai obținut deja ținta.");
                return Ok(p);
            };
            if !g.owned.contains_key(a) || !g.owned.contains_key(b) {
                return Err(ApiError::new(
                    400,
                    "Ambele concepte trebuie să fie în inventar.",
                ));
            };
            if a == b {
                return Err(ApiError::new(400, "Alege două concepte diferite."));
            };
            if g.attempted.contains(&key) {
                let mut p = self.state(id, g);
                p["discovered"] = json!([]);
                p["already_tried"] = json!(true);
                p["message"] = json!("Deja încercată · fără cost. Schimbă un ingredient.");
                return Ok(p);
            };
            if g.attempted.len() >= 496 {
                return Err(ApiError::new(
                    409,
                    "Limita de experimente a jocului a fost atinsă.",
                ));
            };
            g.earned_hint = None;
            g.attempted.insert(key.clone());
            g.moves += 1;
            let discovered = diff(
                g.projection.recipes.get(&key).map_or(&[], Vec::as_slice),
                &sorted(&g.order),
            );
            for id in &discovered {
                g.add(id.clone(), Some([a.into(), b.into()]))
            }
            if discovered.is_empty() {
                g.fruitless_streak += 1;
                g.fruitless_total += 1
            } else {
                g.fruitless_streak = 0
            };
            let mut message = if discovered.is_empty() {
                let known = g.projection.recipes.get(&key).cloned().unwrap_or_default();
                if known.is_empty() {
                    "Perechea nu are o rețetă în această rundă. Fără penalizare.".to_owned()
                } else {
                    format!(
                        "Ai deja rezultatul: {}. Fără penalizare.",
                        known
                            .iter()
                            .map(|id| self.graph.label(id))
                            .collect::<Vec<_>>()
                            .join(", ")
                    )
                }
            } else if has(&discovered, &g.target) {
                format!("Ai descoperit ținta: {}!", self.graph.label(&g.target))
            } else if discovered.len() == 1 {
                format!("Ai descoperit: {}.", self.graph.label(&discovered[0]))
            } else {
                format!(
                    "Ai descoperit {} concepte: {}.",
                    discovered.len(),
                    discovered
                        .iter()
                        .map(|id| self.graph.label(id))
                        .collect::<Vec<_>>()
                        .join(", ")
                )
            };
            if discovered.is_empty() && g.fruitless_total >= 4 {
                message.push(' ');
                message.push_str(
                    [
                        "Încearcă perechi din aceeași temă.",
                        "Combină un element descoperit cu unul de start.",
                        "Indiciul te poate debloca.",
                    ][(g.fruitless_total - 4) % 3],
                )
            };
            let mut p = self.state(id, g);
            p["discovered"] = json!(
                discovered
                    .iter()
                    .map(|id| self.concept(id))
                    .collect::<Vec<_>>()
            );
            p["already_tried"] = json!(false);
            p["message"] = json!(message);
            Ok(p)
        })
    }
    pub fn hint(&self, id: &str) -> Result<Value, ApiError> {
        self.transact(id, |g| {
            if g.won() {
                return Err(ApiError::new(400, "Jocul s-a terminat deja."));
            };
            if g.fruitless_streak < 2 {
                let need = 2 - g.fruitless_streak;
                return Err(ApiError::new(
                    400,
                    &format!(
                        "Mai încearcă {need} {} înainte de un indiciu.",
                        if need == 1 {
                            "combinație"
                        } else {
                            "combinații"
                        }
                    ),
                ));
            };
            let plan = minimum_plan(&g.order, &g.target, &g.projection.recipes, 6);
            g.fruitless_streak = 0;
            let Some(pair) = plan.and_then(|p| p.first().cloned()) else {
                g.earned_hint = None;
                let mut p = self.state(id, g);
                p["hint"] = Value::Null;
                p["hint_kind"] = json!("none");
                p["hint_output"] = Value::Null;
                p["message"] = json!("Niciun indiciu disponibil acum.");
                return Ok(p);
            };
            g.hints_used += 1;
            let mut cue = json!({"hint":null,"hint_output":null});
            if g.hints_used == 1 {
                let outputs: Vec<_> = g
                    .projection
                    .recipes
                    .get(&pair)
                    .into_iter()
                    .flatten()
                    .filter(|id| *id != &g.target && !g.owned.contains_key(*id))
                    .collect();
                if let Some(output) = outputs.first() {
                    let label = self.graph.label(output);
                    cue["hint_kind"] = json!("output");
                    cue["hint_output"] = json!({"label":label});
                    cue["message"] = json!(format!("Indiciu: caută mai întâi «{label}»."))
                } else {
                    cue["hint_kind"] = json!("category");
                    cue["message"] = json!(if g.category.is_empty() {
                        "Indiciu: ținta e la un pas; caută o pereche utilă.".to_owned()
                    } else {
                        format!(
                            "Indiciu: ținta e aproape. Rămâi în tema {}.",
                            self.content.category_labels[&g.category]
                        )
                    })
                }
            } else {
                cue["hint"] = json!([self.concept(&pair[0]), self.concept(&pair[1])]);
                cue["hint_kind"] = json!("pair");
                cue["message"] = json!(format!(
                    "Indiciu: combină {} + {}.",
                    self.graph.label(&pair[0]),
                    self.graph.label(&pair[1])
                ))
            };
            g.earned_hint = Some(cue.clone());
            let mut p = self.state(id, g);
            for (k, v) in cue.as_object().unwrap() {
                p[k] = v.clone()
            }
            Ok(p)
        })
    }
    pub fn reset(&self, id: &str) -> Result<Value, ApiError> {
        self.transact(id, |g| {
            g.owned.clear();
            g.order.clear();
            g.moves = 0;
            g.fruitless_streak = 0;
            g.fruitless_total = 0;
            g.hints_used = 0;
            g.earned_hint = None;
            g.attempted.clear();
            for id in g.seeds.clone() {
                g.add(id, None)
            }
            Ok(self.state(id, g))
        })
    }
}

fn py_strip(text: &str) -> &str {
    text.trim_matches(|r:char|matches!(r,'\u{0009}'..='\u{000d}'|'\u{001c}'..=' '|'\u{0085}'|'\u{00a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}'))
}

// Preserve CPython's compensated float sum, including recipe-quality tie rounding.
fn compensated_sum(values: &[f64]) -> f64 {
    let (mut total, mut correction) = (0.0_f64, 0.0_f64);
    for &x in values {
        let next = total + x;
        if total.abs() >= x.abs() {
            correction += (total - next) + x
        } else {
            correction += (x - next) + total
        };
        total = next
    }
    if correction != 0. && correction.is_finite() {
        total += correction
    };
    total
}

#[cfg(test)]
mod tests {
    use super::*;
    use sha2::{Digest, Sha256};
    fn golden() -> Value {
        serde_json::from_str(include_str!(
            "../../go-backend/internal/alchimie/testdata/python_parity.json"
        ))
        .unwrap()
    }
    fn load() -> Alchimie {
        Alchimie::new(Arc::new(Content::load().unwrap()))
    }
    fn strings(v: &Value) -> Vec<String> {
        v.as_array()
            .unwrap()
            .iter()
            .map(|x| x.as_str().unwrap().to_owned())
            .collect()
    }
    fn projected(p: Option<&Projection>) -> Value {
        let Some(p) = p else { return Value::Null };
        let recipes: Vec<_> = p
            .recipes
            .iter()
            .map(|(pair, results)| json!({"pair":pair,"results":results}))
            .collect();
        let quality: Vec<_> = p
            .candidate_quality
            .iter()
            .map(|q| json!([q[0] as usize, q[1], q[2]]))
            .collect();
        json!({"recipes":recipes,"routes":p.routes,"par":p.par,"candidate_quality":quality})
    }
    fn digest(mut state: Value) -> String {
        state["game_id"] = json!("<session>");
        format!(
            "{:x}",
            Sha256::digest(crate::content::canonical_json(&state))
        )
    }
    #[test]
    fn all_approved_curated_complete_projection_parity() {
        let s = load();
        for r in golden()["curated"].as_array().unwrap() {
            let p = s.projection(
                &strings(&r["seeds"]),
                r["target"].as_str().unwrap(),
                r["category"].as_str().unwrap(),
            );
            assert_eq!(
                projected(p.as_deref()),
                r["projection"],
                "curated {}",
                r["id"]
            );
        }
    }
    #[test]
    fn mined_seed_difficulty_parity() {
        let s = load();
        for r in golden()["mined"].as_array().unwrap() {
            let mut rng = Random::from_u64(r["seed"].as_u64().unwrap());
            let g = s
                .mine(&mut rng, r["difficulty"].as_str().unwrap(), "", "")
                .unwrap();
            assert_eq!(g.seeds, strings(&r["seeds"]));
            assert_eq!(g.target, r["target"].as_str().unwrap());
            assert_eq!(g.category, r["category"].as_str().unwrap());
            let p = projected(Some(&g.projection));
            for key in ["recipes", "routes", "par"] {
                assert_eq!(p[key], r[key], "seed {} field {key}", r["seed"])
            }
            assert_eq!(s.state("<session>", &g), r["state"]);
        }
    }
    #[test]
    fn scored_journeys_terminal_read_only_and_reset_parity() {
        let s = load();
        for steps in golden()["challenge_journeys"].as_array().unwrap() {
            let mut id = String::new();
            for (index, r) in steps.as_array().unwrap().iter().enumerate() {
                let p = match r["action"].as_str().unwrap() {
                    "create" => {
                        let seed = r["seed"].to_string();
                        let p = s.create(Some(&seed), "", "", "normal").unwrap();
                        id = p["game_id"].as_str().unwrap().into();
                        p
                    }
                    "combine" => s
                        .combine(&id, r["a"].as_str().unwrap(), r["b"].as_str().unwrap())
                        .unwrap(),
                    "hint" => s.hint(&id).unwrap(),
                    "reset" => s.reset(&id).unwrap(),
                    x => panic!("unexpected action {x}"),
                };
                assert_eq!(
                    digest(p),
                    r["hash"].as_str().unwrap(),
                    "step {index} {}",
                    r["action"]
                );
            }
            s.store.delete(&id);
        }
    }
    #[test]
    fn missing_lookup_precedes_body_validation_and_python_strip() {
        let s = load();
        let mut called = false;
        let e = s
            .combine_input("missing", || {
                called = true;
                Ok(("a".into(), "b".into()))
            })
            .unwrap_err();
        assert_eq!(e.status, 404);
        assert!(!called);
        assert_eq!(py_strip("\u{001c} \u{2007} id \u{001f}"), "id");
    }
}

#[cfg(test)]
mod edge_tests {
    use super::*;
    #[test]
    fn reviewed_additions_decline_changed_node_provenance() {
        let original = Alchimie::new(Arc::new(Content::load().unwrap()));
        let core = &original.content.recipe_extensions["boards"][0]["core"];
        let seeds: Vec<_> = core["seeds"]
            .as_array()
            .unwrap()
            .iter()
            .map(|id| id.as_str().unwrap().to_owned())
            .collect();
        let target = core["target"].as_str().unwrap();
        let category = core["category"].as_str().unwrap();
        let baseline = build_projection(&original.graph, &seeds, target, category).unwrap();
        let extended = original
            .extend(baseline.clone(), &seeds, target, category)
            .unwrap();
        assert!(extended.recipes.len() > baseline.recipes.len());
        let mut content = Content::load().unwrap();
        content
            .nodes
            .iter_mut()
            .find(|n| n.id == seeds[0])
            .unwrap()
            .source
            .push_str("-metadata-drift");
        let changed = Alchimie::new(Arc::new(content));
        let declined = changed
            .extend(baseline.clone(), &seeds, target, category)
            .unwrap();
        assert_eq!(declined.recipes, baseline.recipes);
    }
}
