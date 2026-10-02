//! Goal-independent discovery gameplay and validated portable craft histories.
use crate::{ApiError, content::Content, session::Store};
use serde::Deserialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::Arc,
};

type Pair = [String; 2];
fn pair(a: &str, b: &str) -> Pair {
    if a < b {
        [a.into(), b.into()]
    } else {
        [b.into(), a.into()]
    }
}
#[derive(Clone, Deserialize)]
struct Concept {
    id: String,
    label: String,
    description: String,
}
#[derive(Clone, Deserialize)]
struct Recipe {
    id: String,
    pair: Pair,
    result: String,
    explanation: String,
    sources: Vec<String>,
}
#[derive(Clone, Deserialize)]
struct Goal {
    id: String,
    target: String,
    title: String,
}
#[derive(Clone, Deserialize)]
struct Unlock {
    id: String,
    after_discoveries: usize,
    concept_ids: Vec<String>,
    title: String,
}
#[derive(Clone, Deserialize)]
struct Info {
    id: String,
    title: String,
    description: String,
    starter_ids: Vec<String>,
}
#[derive(Clone, Deserialize)]
struct Version {
    world_id: String,
    recipe_hash: String,
    mechanics: Value,
}
#[derive(Clone, Deserialize)]
struct World {
    world: Info,
    concepts: Vec<Concept>,
    recipes: Vec<Recipe>,
    goals: Vec<Goal>,
    unlocks: Vec<Unlock>,
    compatible_versions: Vec<Version>,
    recipe_hash: String,
    mechanics: Value,
    #[serde(skip)]
    by_concept: BTreeMap<String, Concept>,
    #[serde(skip)]
    by_pair: BTreeMap<Pair, Recipe>,
    #[serde(skip)]
    by_goal: BTreeMap<String, Goal>,
    #[serde(skip)]
    versions: BTreeMap<String, Version>,
}
impl World {
    fn decode(value: &Value) -> Result<Arc<Self>, String> {
        let mut w: Self = serde_json::from_value(value.clone()).map_err(|e| e.to_string())?;
        if w.world.id.is_empty()
            || !(3..=256).contains(&w.concepts.len())
            || !(2..=512).contains(&w.recipes.len())
            || w.unlocks.len() > 12
            || w.compatible_versions.len() > 16
        {
            return Err("invalid bounded discovery world".into());
        }
        for r in &mut w.recipes {
            r.pair.sort();
        }
        for version in &w.compatible_versions {
            if version.world_id != w.world.id || version.recipe_hash == w.recipe_hash {
                return Err("invalid compatible world identity".into());
            }
        }
        w.by_concept = w
            .concepts
            .iter()
            .map(|c| (c.id.clone(), c.clone()))
            .collect();
        w.by_goal = w.goals.iter().map(|g| (g.id.clone(), g.clone())).collect();
        w.versions = w
            .compatible_versions
            .iter()
            .map(|v| (v.recipe_hash.clone(), v.clone()))
            .collect();
        for r in &w.recipes {
            if r.pair[0] >= r.pair[1]
                || !w.by_concept.contains_key(&r.pair[0])
                || !w.by_concept.contains_key(&r.pair[1])
                || !w.by_concept.contains_key(&r.result)
            {
                return Err("invalid recipe".into());
            }
            w.by_pair.insert(r.pair.clone(), r.clone());
        }
        if w.by_pair.len() != w.recipes.len() || w.by_concept.len() != w.concepts.len() {
            return Err("duplicate discovery records".into());
        }
        let hash = format!(
            "{:x}",
            Sha256::digest(crate::content::canonical_json(&w.mechanics))
        );
        if hash != w.recipe_hash {
            return Err("mechanics hash mismatch".into());
        };
        Ok(Arc::new(w))
    }
}
struct ExploreSession {
    world: Arc<World>,
    owned: BTreeMap<String, Option<Pair>>,
    order: Vec<String>,
    discoveries: Vec<Pair>,
    goal_id: Option<String>,
    unlocked: BTreeSet<String>,
    revision: usize,
    hint_pair: Option<Pair>,
    hint_stage: usize,
    empty_pairs: Vec<Pair>,
}
impl ExploreSession {
    fn fresh(world: Arc<World>, goal_id: Option<String>) -> Self {
        let starters = world.world.starter_ids.clone();
        let mut s = Self {
            world,
            owned: BTreeMap::new(),
            order: vec![],
            discoveries: vec![],
            goal_id,
            unlocked: BTreeSet::new(),
            revision: 0,
            hint_pair: None,
            hint_stage: 0,
            empty_pairs: vec![],
        };
        for id in starters {
            s.add(id, None)
        }
        s
    }
    fn add(&mut self, id: String, parents: Option<Pair>) {
        if !self.owned.contains_key(&id) {
            self.order.push(id.clone())
        };
        self.owned.insert(id, parents);
    }
    fn award(&mut self) -> Vec<String> {
        let mut supplied = vec![];
        for u in self.world.unlocks.clone() {
            if !self.unlocked.contains(&u.id) && self.discoveries.len() >= u.after_discoveries {
                self.unlocked.insert(u.id);
                for id in u.concept_ids {
                    self.add(id.clone(), None);
                    supplied.push(id);
                }
            }
        }
        supplied
    }
    fn craft(&mut self, pair: Pair) -> Result<(Option<String>, bool, Vec<String>), ApiError> {
        if pair[0] == pair[1] || !pair.iter().all(|id| self.owned.contains_key(id)) {
            return Err(ApiError::new(
                400,
                "Alege două ingrediente diferite din colecția ta.",
            ));
        };
        let Some(recipe) = self.world.by_pair.get(&pair) else {
            return Ok((None, false, vec![]));
        };
        let result = recipe.result.clone();
        if self.owned.contains_key(&result) {
            return Ok((Some(result), false, vec![]));
        };
        if self.discoveries.len() >= 256 {
            return Err(ApiError::new(409, "Colecția a atins limita acestei lumi."));
        };
        self.add(result.clone(), Some(pair.clone()));
        self.discoveries.push(pair);
        self.hint_pair = None;
        self.hint_stage = 0;
        Ok((Some(result), true, self.award()))
    }
    fn concept(&self, id: &str) -> Value {
        json!({"id":id,"label":self.world.by_concept[id].label})
    }
    fn hint(&self) -> Value {
        if self.hint_stage == 0 {
            return Value::Null;
        };
        let Some(pair) = &self.hint_pair else {
            return json!({"stage":"complete","message":"Ai descoperit tot în această lume!","output":null,"pair":null});
        };
        let label = &self.world.by_concept[&self.world.by_pair[pair].result].label;
        let (stage, message, pair) = if self.hint_stage >= 2 {
            (
                "pair",
                format!(
                    "Încearcă {} + {}.",
                    self.world.by_concept[&pair[0]].label, self.world.by_concept[&pair[1]].label
                ),
                json!([self.concept(&pair[0]), self.concept(&pair[1])]),
            )
        } else {
            (
                "output",
                format!("Poți descoperi «{label}» cu ingredientele pe care le ai."),
                Value::Null,
            )
        };
        json!({"stage":stage,"message":message,"output":{"label":label},"pair":pair})
    }
    fn state(&self, id: &str) -> Value {
        let inventory:Vec<_>=self.order.iter().map(|cid|{let c=&self.world.by_concept[cid];let parents=&self.owned[cid];let uses:Vec<_>=self.world.recipes.iter().filter(|r|r.pair.contains(cid)).collect();let remaining:Vec<_>=uses.iter().filter(|r|!self.owned.contains_key(&r.result)).collect();let recipe=parents.as_ref().and_then(|p|self.world.by_pair.get(p));let gift=self.world.unlocks.iter().find(|u|u.concept_ids.contains(cid));json!({"id":cid,"label":c.label,"description":c.description,"parents":parents.as_ref().map(|p|[self.concept(&p[0]),self.concept(&p[1])]),"explanation":recipe.map(|r|&r.explanation).or_else(||gift.map(|u|&u.title)),"sources":recipe.map(|r|r.sources.clone()).unwrap_or_default(),"status":if uses.is_empty(){"final"}else if !remaining.is_empty(){"active"}else{"depleted"},"ready":remaining.iter().any(|r|r.pair.iter().all(|id|self.owned.contains_key(id)))})}).collect();
        let next = self
            .world
            .unlocks
            .iter()
            .filter(|u| !self.unlocked.contains(&u.id))
            .min_by_key(|u| u.after_discoveries);
        let goals:Vec<_>=self.world.goals.iter().map(|g|{let done=self.owned.contains_key(&g.target);json!({"id":g.id,"title":g.title,"label":self.world.by_concept[&g.target].label,"completed":done,"target_id":if done{Some(&g.target)}else{None}})}).collect();
        let unlocked: Vec<_> = self
            .world
            .unlocks
            .iter()
            .filter(|u| self.unlocked.contains(&u.id))
            .map(|u| json!({"id":u.id,"title":u.title,"after_discoveries":u.after_discoveries}))
            .collect();
        let hashes: Vec<_> = self
            .world
            .compatible_versions
            .iter()
            .map(|v| &v.recipe_hash)
            .collect();
        json!({"game_id":id,"revision":self.revision,"mode":"explore","compatible_recipe_hashes":hashes,"empty_pairs":self.empty_pairs,"world":{"id":self.world.world.id,"title":self.world.world.title,"description":self.world.world.description,"total_concepts":self.world.concepts.len(),"total_recipes":self.world.recipes.len()},"inventory":inventory,"discovered_count":self.discoveries.len(),"seed_count":self.world.world.starter_ids.len(),"complete":self.owned.len()==self.world.concepts.len(),"goal_id":self.goal_id,"goals":goals,"hint":self.hint(),"unlocked":unlocked,"next_unlock":next.map(|u|json!({"title":u.title,"after_discoveries":u.after_discoveries,"remaining":u.after_discoveries-self.discoveries.len()})),"progress":{"world_id":self.world.world.id,"recipe_hash":self.world.recipe_hash,"discoveries":self.discoveries}})
    }
    fn useful(&self) -> Option<Pair> {
        let mut ancestors = BTreeSet::new();
        if let Some(goal) = &self.goal_id {
            let target = &self.world.by_goal[goal].target;
            if !self.owned.contains_key(target) {
                ancestors.insert(target.clone());
                loop {
                    let before = ancestors.len();
                    for r in &self.world.recipes {
                        if ancestors.contains(&r.result) {
                            ancestors.extend(r.pair.clone())
                        }
                    }
                    if before == ancestors.len() {
                        break;
                    }
                }
            }
        };
        self.world
            .recipes
            .iter()
            .filter(|r| {
                r.pair.iter().all(|id| self.owned.contains_key(id))
                    && !self.owned.contains_key(&r.result)
            })
            .min_by_key(|r| (!ancestors.contains(&r.result), &r.id))
            .map(|r| r.pair.clone())
    }
}
fn restore(
    world: Arc<World>,
    progress: Option<&Value>,
    goal: Option<String>,
) -> Result<ExploreSession, ApiError> {
    let mut s = ExploreSession::fresh(Arc::clone(&world), goal);
    let Some(p) = progress.filter(|v| !v.is_null()) else {
        return Ok(s);
    };
    let hash = p["recipe_hash"].as_str().unwrap_or("");
    let version = world.versions.get(hash);
    if p["world_id"] != world.world.id || (hash != world.recipe_hash && version.is_none()) {
        return Err(ApiError::new(
            409,
            "Colecția aparține altei versiuni. Salvarea rămâne păstrată.",
        ));
    };
    let mechanics = version.map_or(&world.mechanics, |v| &v.mechanics);
    let mut owned: BTreeSet<String> = mechanics["starters"]
        .as_array()
        .unwrap()
        .iter()
        .map(|id| id.as_str().unwrap().to_owned())
        .collect();
    let recipes: BTreeMap<Pair, String> = mechanics["recipes"]
        .as_array()
        .unwrap()
        .iter()
        .map(|r| {
            (
                pair(
                    r["pair"][0].as_str().unwrap(),
                    r["pair"][1].as_str().unwrap(),
                ),
                r["result"].as_str().unwrap().to_owned(),
            )
        })
        .collect();
    let mut crafted = BTreeSet::new();
    let mut validated = vec![];
    let discoveries = p["discoveries"]
        .as_array()
        .ok_or_else(|| ApiError::new(400, "Colecția salvată conține o combinație invalidă."))?;
    for raw in discoveries {
        let raw = raw
            .as_array()
            .filter(|xs| xs.len() == 2)
            .ok_or_else(|| ApiError::new(400, "Colecția salvată conține o combinație invalidă."))?;
        let a = raw[0]
            .as_str()
            .ok_or_else(|| ApiError::new(400, "Colecția salvată conține o combinație invalidă."))?;
        let b = raw[1]
            .as_str()
            .ok_or_else(|| ApiError::new(400, "Colecția salvată conține o combinație invalidă."))?;
        if a == b || !owned.contains(a) || !owned.contains(b) {
            return Err(ApiError::new(
                400,
                "Colecția salvată folosește ingrediente încă nedescoperite.",
            ));
        };
        let pair = pair(a, b);
        let result = recipes
            .get(&pair)
            .ok_or_else(|| ApiError::new(400, "Colecția salvată conține o rețetă necunoscută."))?;
        if owned.insert(result.clone()) {
            crafted.insert(result.clone());
            validated.push(pair);
            for u in mechanics["unlocks"].as_array().unwrap() {
                if crafted.len() >= u["after"].as_u64().unwrap() as usize {
                    owned.extend(
                        u["concepts"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .map(|id| id.as_str().unwrap().to_owned()),
                    )
                }
            }
        }
    }
    for pair in validated {
        s.craft(pair)?;
    }
    if !owned.iter().all(|id| s.owned.contains_key(id)) {
        return Err(ApiError::new(
            409,
            "Colecția nu poate fi actualizată. Salvarea rămâne păstrată.",
        ));
    };
    Ok(s)
}

pub struct Explorer {
    world: Option<Arc<World>>,
    store: Store<ExploreSession>,
}
impl Explorer {
    pub fn new(content: Arc<Content>) -> Self {
        Self {
            world: World::decode(&content.discovery_world).ok(),
            store: Store::new(),
        }
    }
    pub fn create(&self, progress: Option<&Value>, goal: Option<&str>) -> Result<Value, ApiError> {
        let world = self
            .world
            .as_ref()
            .ok_or_else(|| ApiError::new(503, "Lumea de explorat nu este disponibilă momentan."))?;
        if goal.is_some_and(|id| !world.by_goal.contains_key(id)) {
            return Err(ApiError::new(400, "Obiectiv necunoscut."));
        };
        let session = restore(Arc::clone(world), progress, goal.map(str::to_owned))?;
        let id = self
            .store
            .create(session)
            .map_err(|_| ApiError::new(503, "Prea multe explorări active. Încearcă din nou."))?;
        self.get(&id)
    }
    fn transact(
        &self,
        id: &str,
        work: impl FnOnce(&mut ExploreSession) -> Result<Value, ApiError>,
    ) -> Result<Value, ApiError> {
        self.store
            .transaction(id, work)
            .ok_or_else(|| ApiError::new(404, "Explorarea a expirat. Reia colecția salvată."))?
    }
    pub fn get(&self, id: &str) -> Result<Value, ApiError> {
        self.transact(id, |s| Ok(s.state(id)))
    }
    pub fn combine(&self, id: &str, a: &str, b: &str) -> Result<Value, ApiError> {
        self.combine_input(id, || Ok((a.to_owned(), b.to_owned())))
    }
    pub fn combine_input(
        &self,
        id: &str,
        input: impl FnOnce() -> Result<(String, String), ApiError>,
    ) -> Result<Value, ApiError> {
        self.transact(id, |s| {
            let (a, b) = input()?;
            let pair = pair(&a, &b);
            let (result, new, supplies) = s.craft(pair.clone())?;
            s.revision += 1;
            let mut message = if let Some(result) = &result {
                if new {
                    format!("Ai descoperit {}!", s.world.by_concept[result].label)
                } else {
                    format!("Ai deja {} în colecție.", s.world.by_concept[result].label)
                }
            } else {
                if !s.empty_pairs.contains(&pair) {
                    if s.empty_pairs.len() >= 128 {
                        s.empty_pairs.remove(0);
                    };
                    s.empty_pairs.push(pair)
                };
                "Perechea nu are încă o rețetă. Încearcă alt ingredient; nu pierzi nimic.".into()
            };
            if !supplies.is_empty() {
                message.push_str(" Ai primit provizii noi în cămară!")
            };
            let mut state = s.state(id);
            state["message"] = json!(message);
            state["discovered"] = if new {
                json!([s.concept(result.as_ref().unwrap())])
            } else {
                json!([])
            };
            state["result"] = result
                .as_ref()
                .map(|id| s.concept(id))
                .unwrap_or(Value::Null);
            state["supplied"] = json!(supplies.iter().map(|id| s.concept(id)).collect::<Vec<_>>());
            state["already_known"] = json!(result.is_some() && !new);
            Ok(state)
        })
    }
    pub fn hint(&self, id: &str) -> Result<Value, ApiError> {
        self.transact(id, |s| {
            if s.hint_pair.is_none() {
                s.hint_pair = s.useful()
            };
            s.hint_stage = (s.hint_stage + 1).min(2);
            s.revision += 1;
            Ok(s.state(id))
        })
    }
    pub fn goal(&self, id: &str, goal: Option<&str>) -> Result<Value, ApiError> {
        self.goal_input(id, || Ok(goal.map(str::to_owned)))
    }
    pub fn goal_input(
        &self,
        id: &str,
        input: impl FnOnce() -> Result<Option<String>, ApiError>,
    ) -> Result<Value, ApiError> {
        self.transact(id, |s| {
            let goal = input()?;
            if goal
                .as_ref()
                .is_some_and(|id| !s.world.by_goal.contains_key(id))
            {
                return Err(ApiError::new(400, "Obiectiv necunoscut."));
            };
            s.goal_id = goal;
            s.hint_pair = None;
            s.hint_stage = 0;
            s.revision += 1;
            Ok(s.state(id))
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    fn golden() -> Value {
        serde_json::from_str(include_str!(
            "../../go-backend/internal/alchimie/testdata/python_parity.json"
        ))
        .unwrap()
    }
    fn load() -> Explorer {
        let s = Explorer::new(Arc::new(Content::load().unwrap()));
        assert!(s.world.is_some());
        s
    }
    fn digest(mut state: Value) -> String {
        state["game_id"] = json!("<session>");
        format!(
            "{:x}",
            Sha256::digest(crate::content::canonical_json(&state))
        )
    }
    #[test]
    fn all_crafts_supply_tiers_goals_hints_completion_parity() {
        let s = load();
        let mut id = String::new();
        for (index, r) in golden()["explore"].as_array().unwrap().iter().enumerate() {
            let p = match r["action"].as_str().unwrap() {
                "create" => {
                    let p = s.create(None, r["goal"].as_str()).unwrap();
                    id = p["game_id"].as_str().unwrap().into();
                    p
                }
                "hint" => s.hint(&id).unwrap(),
                "combine" => s
                    .combine(&id, r["a"].as_str().unwrap(), r["b"].as_str().unwrap())
                    .unwrap(),
                x => panic!("unexpected action {x}"),
            };
            assert_eq!(
                digest(p),
                r["hash"].as_str().unwrap(),
                "step{index} {}",
                r["action"]
            );
        }
    }
    #[test]
    fn current_and_every_archived_mechanics_restore_parity() {
        let s = load();
        for (index, r) in golden()["restores"].as_array().unwrap().iter().enumerate() {
            let p = s.create(Some(&r["progress"]), r["goal"].as_str()).unwrap();
            assert_eq!(digest(p), r["hash"].as_str().unwrap(), "restore{index}");
        }
    }
    #[test]
    fn restore_cannot_invent_or_allocate_and_missing_lookup_precedes_validation() {
        let s = load();
        let world = s.world.as_ref().unwrap();
        let p = json!({"world_id":world.world.id,"recipe_hash":world.recipe_hash,"discoveries":[["unknown","other"]]});
        assert_eq!(s.create(Some(&p), None).unwrap_err().status, 400);
        assert_eq!(s.store.len(), 0);
        let mut called = false;
        assert_eq!(
            s.combine_input("missing", || {
                called = true;
                Ok(("a".into(), "b".into()))
            })
            .unwrap_err()
            .status,
            404
        );
        assert!(!called);
        assert_eq!(
            s.goal_input("missing", || {
                called = true;
                Ok(None)
            })
            .unwrap_err()
            .status,
            404
        );
        assert!(!called);
    }
}

#[cfg(test)]
mod edge_tests {
    use super::*;
    #[test]
    fn goals_change_only_guidance_and_observation_fifo_stays_bounded() {
        let s = Explorer::new(Arc::new(Content::load().unwrap()));
        let initial = s.create(None, None).unwrap();
        let id = initial["game_id"].as_str().unwrap();
        let world = s.world.as_ref().unwrap();
        for goal in &world.goals {
            let p = s.goal(id, Some(&goal.id)).unwrap();
            assert_eq!(p["hint"], Value::Null);
            assert_eq!(p["progress"], initial["progress"])
        }
        s.store.transaction(id, |g| {
            for c in g.world.concepts.clone() {
                g.add(c.id, None)
            }
        });
        let mut misses = vec![];
        'outer: for (i, a) in world.concepts.iter().enumerate() {
            for b in &world.concepts[i + 1..] {
                let p = pair(&a.id, &b.id);
                if !world.by_pair.contains_key(&p) {
                    misses.push(p);
                    if misses.len() == 129 {
                        break 'outer;
                    }
                }
            }
        }
        let mut state = Value::Null;
        for p in &misses {
            state = s.combine(id, &p[0], &p[1]).unwrap()
        }
        let observed = state["empty_pairs"].as_array().unwrap();
        assert_eq!(observed.len(), 128);
        assert_eq!(observed[0], json!(misses[1]));
        assert_eq!(observed[127], json!(misses[128]));
    }
}
