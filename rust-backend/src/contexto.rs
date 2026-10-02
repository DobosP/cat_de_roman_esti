//! Server-authoritative Cald sau Rece, including reviewed projected vocabulary.
use crate::{
    ApiError,
    catalog::daily_seed,
    content::{Content, PackItem},
    graph::{self, Service as Graph},
    pack::{Pack, PickOptions},
    pyrandom::Random,
    session::Store,
};
use serde::Deserialize;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet, HashMap, VecDeque},
    sync::{Arc, Mutex},
};
#[derive(Default)]
pub struct GuessBody {
    pub text: String,
    pub confirm: Option<String>,
}
#[derive(Clone, Deserialize)]
struct Projection {
    key: String,
    label: String,
    public_id: String,
    anchor_id: String,
    rank_penalty: usize,
}
#[derive(Deserialize)]
struct Neighborhood {
    anchor_id: String,
    min_strength: f64,
    include_direct_neighbors: bool,
    exact_target_ids: Vec<String>,
}
#[derive(Deserialize)]
struct Ingredient {
    fallback_anchor_id: String,
    min_strength: f64,
}
#[derive(Deserialize)]
struct Data {
    projection_terms: Vec<Projection>,
    neighborhoods: BTreeMap<String, Neighborhood>,
    feedback_proxies: BTreeMap<String, String>,
    ingredient_policies: BTreeMap<String, Ingredient>,
    exact_pairs: Vec<Vec<String>>,
}
struct Profile {
    dist: Vec<i32>,
    weighted: Vec<f64>,
    buckets: BTreeMap<usize, Vec<f64>>,
    closer: BTreeMap<usize, usize>,
    reachable: usize,
}
struct ProfileCache {
    values: HashMap<String, Arc<Profile>>,
    fifo: VecDeque<String>,
}
#[derive(Clone)]
struct Record {
    id: String,
    label: String,
    temperature: String,
    anchor: String,
    distance: usize,
    closeness: usize,
    rank: usize,
    attempt: usize,
}
#[derive(Clone)]
struct Warm {
    label: String,
    rank: usize,
}
struct Game {
    target: String,
    difficulty: String,
    category: String,
    daily: Option<String>,
    profile: Arc<Profile>,
    guesses: BTreeMap<String, Record>,
    order: Vec<String>,
    attempts: usize,
    won: bool,
    gave_up: bool,
    category_clue: bool,
    warm_exhausted: bool,
    warm: Option<Warm>,
    clues: usize,
}
pub struct Service {
    c: Arc<Content>,
    g: Arc<Graph>,
    pack: Pack,
    data: Data,
    terms: BTreeMap<String, Projection>,
    pairs: BTreeSet<(String, String)>,
    profiles: Mutex<ProfileCache>,
    store: Store<Game>,
}
pub type Contexto = Service;
impl Service {
    pub fn new(c: Arc<Content>) -> Self {
        let data: Data =
            serde_json::from_value(c.contexto_data.clone()).expect("validated Contexto data");
        let terms = data
            .projection_terms
            .iter()
            .map(|p| (p.key.clone(), p.clone()))
            .collect();
        let pairs = data
            .exact_pairs
            .iter()
            .map(|v| (v[0].clone(), v[1].clone()))
            .collect();
        Self {
            g: Graph::new(c.clone()),
            pack: Pack::new(c.clone()),
            c,
            data,
            terms,
            pairs,
            profiles: Mutex::new(ProfileCache {
                values: HashMap::new(),
                fifo: VecDeque::new(),
            }),
            store: Store::new(),
        }
    }
    fn profile(&self, target: &str) -> Arc<Profile> {
        if let Some(p) = self
            .profiles
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .values
            .get(target)
        {
            return p.clone();
        };
        let dist = self.g.distances_to_dense(target);
        let weighted = self.g.weighted_distances_to_dense(target);
        let mut buckets: BTreeMap<usize, Vec<f64>> = BTreeMap::new();
        for (index, d) in dist.iter().copied().enumerate() {
            if d < 0 {
                continue;
            };
            buckets.entry(d as usize).or_default().push(weighted[index]);
        }
        let mut closer = BTreeMap::new();
        let mut count = 0;
        for (d, b) in &mut buckets {
            b.sort_by(f64::total_cmp);
            closer.insert(*d, count);
            count += b.len();
        }
        let p = Arc::new(Profile {
            reachable: dist.iter().filter(|d| **d >= 0).count(),
            dist,
            weighted,
            buckets,
            closer,
        });
        let mut cache = self.profiles.lock().unwrap_or_else(|e| e.into_inner());
        if let Some(old) = cache.values.get(target) {
            return old.clone();
        };
        if cache.fifo.len() >= 256 {
            let old = cache.fifo.pop_front().unwrap();
            cache.values.remove(&old);
        }
        cache.fifo.push_back(target.to_owned());
        cache.values.insert(target.to_owned(), p.clone());
        p
    }
    pub fn create(
        &self,
        seed: Option<&str>,
        difficulty: &str,
        daily: Option<&str>,
        category: &str,
    ) -> Result<Value, ApiError> {
        let difficulty = if ["usor", "greu"].contains(&difficulty) {
            difficulty
        } else {
            "normal"
        };
        if !category.is_empty() && !self.c.category_labels.contains_key(category) {
            return Err(ApiError::new(400, "Categorie necunoscută."));
        };
        let daily_seed_string = daily.map(|d| daily_seed(d, "contexto").to_string());
        let seed = daily_seed_string.as_deref().or(seed);
        let o = PickOptions {
            category: category.into(),
            difficulty: difficulty.into(),
            filtered_shelf_weights: true,
            ..Default::default()
        };
        let chosen: Option<&PackItem> = if let Some(day) = daily {
            self.pack.pick_daily("contexto", day, &o)
        } else {
            self.pack.pick_seeded("contexto", &mut rng(seed), &o)
        };
        let target = if let Some(item) = chosen {
            item.payload["target"].as_str().unwrap().to_owned()
        } else {
            self.mine(seed, difficulty, category)?
        };
        let v = Game {
            profile: self.profile(&target),
            target,
            difficulty: difficulty.into(),
            category: category.into(),
            daily: daily.map(str::to_owned),
            guesses: BTreeMap::new(),
            order: vec![],
            attempts: 0,
            won: false,
            gave_up: false,
            category_clue: false,
            warm_exhausted: false,
            warm: None,
            clues: 0,
        };
        let mut body = self.state("", &v);
        let id = self
            .store
            .create(v)
            .map_err(|_| ApiError::new(503, "Prea multe jocuri active. Încearcă din nou."))?;
        body["game_id"] = json!(id);
        Ok(body)
    }
    fn mine(
        &self,
        seed: Option<&str>,
        difficulty: &str,
        category: &str,
    ) -> Result<String, ApiError> {
        let mut pool = self.g.all_ids();
        if difficulty == "usor" {
            let high = self.g.by_salience(0.6, true);
            if !high.is_empty() {
                pool = high
            }
        } else if difficulty == "greu" {
            pool = self.g.by_salience(0., false);
            pool.truncate((pool.len() / 2).max(1));
        }
        if !category.is_empty() {
            pool.retain(|id| self.g.node(id).unwrap().category == category);
            if pool.is_empty() {
                return Err(ApiError::new(
                    503,
                    "Nu există încă jocuri pentru această categorie.",
                ));
            }
        }
        rng(seed).shuffle(&mut pool);
        let mut fallback = None;
        for id in &pool {
            let dist = self.g.distances_to(id);
            let responsive = dist.values().filter(|d| (1..=5).contains(*d)).count();
            if dist.len() >= 120 && responsive >= 40 {
                return Ok(id.clone());
            };
            if fallback.is_none() && dist.len() >= 120 {
                fallback = Some(id.clone())
            }
        }
        if let Some(id) = fallback {
            return Ok(id);
        };
        if category.is_empty() {
            pool = self.g.all_ids()
        };
        let mut best = None;
        for id in pool {
            let size = self.g.distances_to(&id).len();
            if best.as_ref().is_none_or(|(_, n)| size > *n) {
                best = Some((id, size))
            }
        }
        let (target, size) = best.expect("nonempty validated graph");
        if !category.is_empty() && size < 120 {
            return Err(ApiError::new(
                503,
                "Nu există încă jocuri pentru această categorie.",
            ));
        };
        Ok(target)
    }
    fn action<F>(&self, id: &str, f: F) -> Result<Value, ApiError>
    where
        F: FnOnce(&mut Game) -> Result<Value, ApiError>,
    {
        self.store
            .transaction(id, f)
            .unwrap_or_else(|| Err(ApiError::new(404, "Joc inexistent")))
    }
    pub fn get(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |v| Ok(self.state(id, v)))
    }
    fn feedback_anchor(&self, id: &str, target: &str, exact: bool) -> String {
        if id == target {
            return id.to_owned();
        };
        if exact
            && self.pairs.contains(&(id.into(), target.into()))
            && self.g.exists(id)
            && self.g.exists(target)
        {
            return target.into();
        };
        if let Some(p) = self
            .data
            .ingredient_policies
            .get(id)
            .filter(|_| self.g.exists(id))
        {
            if self.g.link(id, target).is_some_and(|e| {
                e.relation == "part_of"
                    && e.label_ro == "ingredient pentru"
                    && e.strength >= p.min_strength
            }) {
                return id.into();
            };
            if self.g.exists(&p.fallback_anchor_id) {
                return p.fallback_anchor_id.clone();
            }
        }
        if let Some(proxy) = self
            .data
            .feedback_proxies
            .get(id)
            .filter(|p| p.as_str() != id && self.g.exists(p))
        {
            return proxy.clone();
        };
        id.into()
    }
    fn projection_anchor(&self, p: &Projection, target: &str) -> String {
        if let Some(n) = self
            .data
            .neighborhoods
            .get(&p.key)
            .filter(|n| self.g.exists(&n.anchor_id))
        {
            if n.exact_target_ids
                .iter()
                .any(|id| id == target && self.g.exists(target))
            {
                return target.into();
            };
            if target == n.anchor_id {
                return target.into();
            };
            if n.include_direct_neighbors
                && self
                    .g
                    .link(&n.anchor_id, target)
                    .is_some_and(|e| e.strength >= n.min_strength)
            {
                return n.anchor_id.clone();
            }
        }
        p.anchor_id.clone()
    }
    fn score(&self, v: &Game, id: &str, nonwinning: bool, mut penalty: usize) -> Scored {
        let anchor = self.feedback_anchor(id, &v.target, !nonwinning);
        let index = self.g.index(&anchor);
        let mut distance =
            index.and_then(|i| (v.profile.dist[i] >= 0).then_some(v.profile.dist[i] as usize));
        let mut rank = distance.map_or(v.profile.reachable + 1, |d| {
            v.profile.closer[&d]
                + v.profile.buckets[&d].partition_point(|w| *w < v.profile.weighted[index.unwrap()])
                + 1
        });
        if nonwinning || anchor != id {
            if anchor != id {
                penalty = penalty.max(1)
            };
            rank = (rank + penalty).min(v.profile.reachable + 1).max(2);
            if distance == Some(0) {
                distance = Some(1)
            }
        }
        Scored {
            anchor,
            distance,
            rank,
        }
    }
    fn guesses(&self, v: &Game) -> Value {
        let mut rows: Vec<_> = v.guesses.values().collect();
        rows.sort_by(|a, b| {
            a.rank
                .cmp(&b.rank)
                .then(a.distance.cmp(&b.distance))
                .then(b.closeness.cmp(&a.closeness))
                .then(a.label.cmp(&b.label))
                .then(a.attempt.cmp(&b.attempt))
                .then(a.id.cmp(&b.id))
        });
        json!(
            rows.into_iter()
                .map(|r| {
                    assert!(v.won || v.gave_up || r.id != v.target, "unrevealed target");
                    record_json(r)
                })
                .collect::<Vec<_>>()
        )
    }
    fn warmer(&self, v: &Game) -> Option<Warm> {
        if v.warm.is_some() || v.warm_exhausted {
            return None;
        };
        let best = v
            .guesses
            .values()
            .map(|r| r.rank)
            .min()
            .unwrap_or(v.profile.reachable + 1);
        if best <= 2 {
            return None;
        };
        let anchors: BTreeSet<_> = v.guesses.values().map(|r| r.anchor.as_str()).collect();
        let mut rows = vec![];
        for (index, distance) in v.profile.dist.iter().enumerate() {
            if *distance < 0 {
                continue;
            };
            let id = self.g.id_at(index);
            if id == v.target {
                continue;
            };
            let sc = self.score(v, id, false, 0);
            if anchors.contains(sc.anchor.as_str()) || sc.rank <= 1 || sc.rank >= best {
                continue;
            };
            rows.push((
                sc.rank,
                self.g.salience(id),
                self.g.label(id).to_owned(),
                id.to_owned(),
            ));
        }
        rows.sort_by(|a, b| {
            a.0.cmp(&b.0)
                .then(b.1.total_cmp(&a.1))
                .then(self.g.casefold(&a.2).cmp(&self.g.casefold(&b.2)))
                .then(a.3.cmp(&b.3))
        });
        for familiar in [true, false] {
            if let Some(row) = rows.iter().find(|r| !familiar || r.1 >= 0.55) {
                return Some(Warm {
                    label: row.2.clone(),
                    rank: row.0,
                });
            }
        }
        None
    }
    fn category_clue(&self, v: &Game) -> Value {
        let category = &self.g.node(&v.target).unwrap().category;
        let label = self.c.category_labels.get(category).unwrap_or(category);
        json!({"category":{"key":category,"label":label},"message":format!("Categoria secretului: {label}.")})
    }
    fn clue_view(&self, v: &Game) -> Value {
        let kind = if v.won || v.gave_up || v.attempts < 3 {
            None
        } else if !v.category_clue && v.category.is_empty() {
            Some("category")
        } else if self.warmer(v).is_some() {
            Some("warmer")
        } else {
            None
        };
        let mut out = json!({"clues_used":v.clues,"clue_available":kind.is_some()});
        if let Some(kind) = kind {
            out["next_clue_kind"] = json!(kind)
        }
        if v.category_clue {
            out["clue"] = self.category_clue(v)
        }
        if let Some(w) = &v.warm {
            out["warm_clue"] = warm_json(w)
        }
        out
    }
    fn target(&self, v: &Game) -> Value {
        json!({"id":v.target,"label":self.g.label(&v.target),"description":self.g.description(&v.target)})
    }
    fn state(&self, id: &str, v: &Game) -> Value {
        let mut out = json!({"game_id":id,"attempts":v.attempts,"won":v.won,"gave_up":v.gave_up,"reachable_count":v.profile.reachable,"difficulty":v.difficulty,"guesses":self.guesses(v)});
        merge(&mut out, self.clue_view(v));
        if let Some(day) = &v.daily {
            out["daily"] = json!(day)
        }
        if !v.category.is_empty() {
            out["board_category"] = json!(v.category)
        }
        if v.won || v.gave_up {
            out["target"] = self.target(v)
        }
        if v.won {
            out["score"] = json!(score(v));
            out["share"] = json!(self.share(v))
        }
        out
    }
    fn share(&self, v: &Game) -> String {
        let trail: String = v
            .order
            .iter()
            .map(|id| {
                let r = &v.guesses[id];
                if r.distance == 0 {
                    "🎯"
                } else if r.closeness >= 75 {
                    "🟩"
                } else if r.closeness >= 50 {
                    "🟨"
                } else if r.closeness >= 25 {
                    "🟧"
                } else {
                    "🟥"
                }
            })
            .collect();
        let mut header = "cat_de_roman_esti · Cald sau Rece".to_owned();
        if !v.category.is_empty() {
            header.push_str(&format!(" · {}", self.c.category_labels[&v.category]))
        };
        let mut lines = vec![
            header,
            trail,
            format!(
                "{} {}",
                v.attempts,
                if v.attempts == 1 {
                    "încercare"
                } else {
                    "încercări"
                }
            ),
        ];
        if v.clues > 0 {
            lines.push(format!("indiciu x{}", v.clues))
        }
        if let Some(day) = &v.daily {
            lines.push(day.clone())
        }
        lines.join("\n")
    }
    fn unknown(&self, v: &Game, suggestions: Vec<String>) -> Value {
        let mut out = json!({"ok":false,"message":"Cuvântul nu este încă în vocabularul jocului. Nu ai pierdut nicio încercare.","suggestions":suggestions,"guesses":self.guesses(v),"attempts":v.attempts,"won":v.won,"reachable_count":v.profile.reachable});
        merge(&mut out, self.clue_view(v));
        out
    }
    fn suggested_projections(&self, text: &str) -> Vec<&Projection> {
        let key = self.g.normalize(text);
        let length = key.chars().count();
        let mut rows: Vec<_> = self
            .terms
            .iter()
            .filter_map(|(k, p)| {
                let n = k.chars().count();
                if n + length == 0 || 2. * n.min(length) as f64 / ((n + length) as f64) < 0.78 {
                    return None;
                };
                let ratio = graph::sequence_ratio(k, &key);
                (ratio >= 0.78).then_some((ratio, k, p))
            })
            .collect();
        rows.sort_by(|a, b| b.0.total_cmp(&a.0).then(b.1.cmp(a.1)));
        rows.truncate(6);
        rows.into_iter().map(|r| r.2).collect()
    }
    pub fn guess_input<F>(&self, id: &str, validate: F) -> Result<Value, ApiError>
    where
        F: FnOnce() -> Result<GuessBody, ApiError>,
    {
        self.action(id,|v|{let body=validate()?;if v.won||v.gave_up{return Err(ApiError::new(400,"Jocul s-a terminat"))};let text=body.text.trim_matches(py_space);if text.is_empty(){return Err(ApiError::new(400,"Scrie un concept"))};let mut node=self.g.resolve(text);let unresolved=self.g.reviewed_unresolved(text);let term=if node.is_none()&&!unresolved{self.terms.get(&self.g.normalize(text))}else{None};let mut corrected=false;if node.is_none()&&term.is_none(){let mut fuzzy=self.g.resolve_fuzzy(text);if fuzzy.as_ref().is_some_and(|id|id!=&v.target&&self.feedback_anchor(id,&v.target,true)==v.target){fuzzy=None};if let Some(f)=fuzzy.as_ref().filter(|f|*f!=&v.target){let digest=Sha256::digest(format!("{id}\0{f}").as_bytes());let token=format!("ctxc_{}",digest[..8].iter().map(|b|format!("{b:02x}")).collect::<String>());if body.confirm.as_deref()!=Some(&token){let label=self.g.label(f);let mut out=self.unknown(v,vec![]);out["needs_confirmation"]=json!(true);out["resolved_label"]=json!(label);out["resolved_token"]=json!(token);out["message"]=json!(format!("Am înțeles: {label}. Confirmă sau corectează."));return Ok(out)}}node=fuzzy;corrected=node.is_some();}
if node.is_none()&&term.is_none(){let mut labels=vec![];if !unresolved{for p in self.suggested_projections(text){if self.feedback_anchor(&self.projection_anchor(p,&v.target),&v.target,false)!=v.target{labels.push(p.label.clone())}}}for label in self.g.suggest(text,3){if self.g.resolve(&label).is_some_and(|id|self.feedback_anchor(&id,&v.target,true)!=v.target){labels.push(label)}}let mut suggestions=vec![];let mut seen=BTreeSet::new();for label in labels{if !seen.insert(self.g.casefold(&label))||!advisory(&self.g.normalize(text),&self.g.normalize(&label)){continue};suggestions.push(label);if suggestions.len()==3{break}}return Ok(self.unknown(v,suggestions))};let submitted=term.map_or_else(||node.as_ref().unwrap().clone(),|p|self.projection_anchor(p,&v.target));let(id,label,penalty)=term.map_or_else(||(submitted.clone(),self.g.label(&submitted).to_owned(),0),|p|(p.public_id.clone(),p.label.clone(),p.rank_penalty));let sc=self.score(v,&submitted,term.is_some(),penalty);let existing=v.guesses.get(&id);let is_new=existing.is_none();let record=Record{id:id.clone(),label,temperature:temperature(v,&sc).into(),distance:sc.distance.unwrap_or(999),closeness:closeness(v,&sc),rank:sc.rank,anchor:sc.anchor,attempt:existing.map_or(v.attempts+1,|r|r.attempt)};let found=term.is_none()&&submitted==v.target;let feedback=feedback(v,&record,is_new,found);v.guesses.insert(id.clone(),record.clone());if is_new{v.attempts+=1;v.order.push(id)}
if found{v.won=true}let mut out=json!({"ok":true,"guess":record_json(&record),"guesses":self.guesses(v),"attempts":v.attempts,"won":v.won,"reachable_count":v.profile.reachable,"feedback":feedback});merge(&mut out,self.clue_view(v));if corrected{out["message"]=json!(format!("Am înțeles: {}.",record.label))}
if v.won{out["target"]=self.target(v);out["score"]=json!(score(v));out["share"]=json!(self.share(v))}Ok(out)})
    }
    pub fn guess(&self, id: &str, text: &str, confirm: Option<&str>) -> Result<Value, ApiError> {
        self.guess_input(id, || {
            Ok(GuessBody {
                text: text.into(),
                confirm: confirm.map(str::to_owned),
            })
        })
    }
    pub fn clue(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |v| {
            if v.won || v.gave_up {
                return Err(ApiError::new(400, "Jocul s-a terminat"));
            }
            if v.attempts < 3 {
                let n = 3 - v.attempts;
                return Err(ApiError::new(
                    400,
                    &format!(
                        "Mai încearcă {n} {} înainte de indiciu.",
                        if n == 1 { "concept" } else { "concepte" }
                    ),
                ));
            }
            let mut out = json!({"ok":true});
            if !v.category_clue && v.category.is_empty() {
                v.category_clue = true;
                v.clues += 1;
                out["clue_kind"] = json!("category");
                merge(&mut out, self.category_clue(v));
            } else {
                let Some(clue) = self.warmer(v) else {
                    v.warm_exhausted = true;
                    return Err(ApiError::new(
                        400,
                        "Nu mai există un indiciu sigur mai cald.",
                    ));
                };
                v.warm = Some(clue.clone());
                v.clues += 1;
                out["clue_kind"] = json!("warmer");
                out["word"] = warm_json(&clue);
                out["message"] = json!(format!("Mai cald: {}.", clue.label));
            }
            merge(&mut out, self.state(id, v));
            Ok(out)
        })
    }
    pub fn give_up(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |v| {
            if v.won || v.gave_up {
                return Err(ApiError::new(400, "Jocul s-a terminat"));
            }
            v.gave_up = true;
            Ok(self.state(id, v))
        })
    }
}
struct Scored {
    anchor: String,
    distance: Option<usize>,
    rank: usize,
}
fn rng(seed: Option<&str>) -> Random {
    if let Some(seed) = seed {
        return Random::from_decimal(seed).expect("validated seed");
    };
    let mut raw = [0u8; 32];
    getrandom::fill(&mut raw).expect("OS entropy");
    let words: Vec<_> = raw
        .as_chunks::<4>()
        .0
        .iter()
        .map(|c| u32::from_le_bytes(*c))
        .collect();
    Random::from_words(&words)
}
fn merge(out: &mut Value, other: Value) {
    out.as_object_mut()
        .unwrap()
        .extend(other.as_object().unwrap().clone());
}
fn score(v: &Game) -> usize {
    (1000isize - 60 * (v.attempts.max(1) - 1) as isize - 120 * v.clues as isize).max(50) as usize
}
fn record_json(r: &Record) -> Value {
    json!({"id":r.id,"label":r.label,"distance":r.distance,"rank":r.rank,"temperature":r.temperature,"closeness":r.closeness,"attempt_number":r.attempt})
}
fn warm_json(v: &Warm) -> Value {
    json!({"label":v.label,"rank":v.rank,"message":format!("Mai cald: {} (#{}).",v.label,v.rank)})
}
fn closeness(v: &Game, r: &Scored) -> usize {
    let Some(d) = r.distance else { return 0 };
    if d == 0 {
        return 100;
    }
    if v.profile.reachable <= 1 {
        return 0;
    };
    (100. * (v.profile.reachable as f64 - r.rank as f64) / (v.profile.reachable - 1) as f64)
        .round_ties_even()
        .clamp(1., 99.) as usize
}
fn temperature(v: &Game, r: &Scored) -> &'static str {
    let Some(d) = r.distance else {
        return "Inghetat";
    };
    if d == 0 {
        return "Gasit";
    };
    let pct = r.rank as f64 / v.profile.reachable as f64;
    if d == 1 || pct <= 0.005 {
        "Fierbinte"
    } else if pct <= 0.03 {
        "Cald"
    } else if pct <= 0.10 {
        "Caldut"
    } else if pct <= 0.40 {
        "Rece"
    } else if pct <= 0.70 {
        "Foarte rece"
    } else {
        "Inghetat"
    }
}
fn feedback(v: &Game, r: &Record, is_new: bool, found: bool) -> Value {
    if found {
        return json!({"kind":"found","message":"Exact — ai găsit răspunsul!"});
    }
    if !is_new {
        return json!({"kind":"repeat","message":format!("Deja încercat — rămâne #{}.",r.rank)});
    }
    if v.order.is_empty() {
        return json!({"kind":"first","message":format!("Primul reper: #{}.",r.rank)});
    }
    let previous = &v.guesses[v.order.last().unwrap()];
    let best = v.guesses.values().map(|r| r.rank).min().unwrap();
    let places = |n: usize| {
        if n == 1 {
            "un loc".to_owned()
        } else {
            format!("{n} locuri")
        }
    };
    if r.rank < best {
        return json!({"kind":"new-best","message":format!("Cel mai bun: cu {} mai aproape.",places(best-r.rank)),"rank_delta":best-r.rank});
    }
    let delta = previous.rank as isize - r.rank as isize;
    let (kind, message) = if delta > 0 {
        ("warmer", format!("Mai cald cu {}.", places(delta as usize)))
    } else if delta < 0 {
        (
            "colder",
            format!("Mai rece cu {}.", places((-delta) as usize)),
        )
    } else {
        ("same", "La fel de aproape ca încercarea trecută.".into())
    };
    json!({"kind":kind,"message":message,"rank_delta":delta})
}
fn advisory(a: &str, b: &str) -> bool {
    let (aa, bb): (Vec<_>, Vec<_>) = (a.chars().collect(), b.chars().collect());
    if aa.len() == bb.len() {
        let different: Vec<_> = aa
            .iter()
            .zip(&bb)
            .enumerate()
            .filter_map(|(i, (a, b))| (a != b).then_some(i))
            .collect();
        if different.len() <= 1 {
            return true;
        }
        if different.len() == 2 {
            let (p, q) = (different[0], different[1]);
            if q == p + 1 && aa[p] == bb[q] && aa[q] == bb[p] {
                return true;
            }
        }
    }
    if bb.len() >= 3 && a.starts_with(b) && (1..=2).contains(&aa.len().saturating_sub(bb.len())) {
        return true;
    };
    graph::sequence_ratio(a, b) >= 0.82
}
fn py_space(c: char) -> bool {
    matches!(c,'\u{9}'..='\u{d}'|'\u{1c}'..='\u{20}'|'\u{85}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}')
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn pinned_validation_and_concurrent_repeats() {
        let s = Arc::new(Service::new(Arc::new(Content::load().unwrap())));
        let game = s.create(Some("17"), "normal", None, "").unwrap();
        let id = game["game_id"].as_str().unwrap().to_owned();
        let error = s
            .guess_input("missing", || panic!("validator on missing session"))
            .unwrap_err();
        assert_eq!(error.status, 404);
        let error = s
            .guess_input(&id, || {
                assert!(!s.store.delete(&id));
                Err(ApiError::new(422, "validation"))
            })
            .unwrap_err();
        assert_eq!(error.status, 422);
        let workers: Vec<_> = (0..24)
            .map(|_| {
                let s = s.clone();
                let id = id.clone();
                std::thread::spawn(move || s.guess(&id, "n_mihai_eminescu", None))
            })
            .collect();
        for w in workers {
            if let Err(e) = w.join().unwrap() {
                assert_eq!(e.status, 400)
            }
        }
        assert_eq!(s.get(&id).unwrap()["attempts"], 1);
        let _ = s.give_up(&id);
        assert_eq!(
            s.guess_input(&id, || Err(ApiError::new(422, "validation")))
                .unwrap_err()
                .status,
            422
        );
        assert!(s.profiles.lock().unwrap().values.len() <= 256);
    }
    fn normalize(v: &mut Value) {
        match v {
            Value::Object(map) => {
                for (k, v) in map {
                    if k == "game_id" {
                        *v = json!("<session>")
                    } else if k == "resolved_token" {
                        *v = json!("<confirmation>")
                    } else {
                        normalize(v)
                    }
                }
            }
            Value::Array(items) => {
                for v in items {
                    normalize(v)
                }
            }
            _ => {}
        }
    }
    #[test]
    fn python_http_sequences() {
        let c = Arc::new(Content::load().unwrap());
        let s = Service::new(c);
        let rows: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/contexto/testdata/python_games.json"
        ))
        .unwrap();
        for (row_index, row) in rows.as_array().unwrap().iter().enumerate() {
            let created = s.create(
                row["seed"].as_str(),
                row["difficulty"].as_str().unwrap(),
                row["daily"].as_str(),
                row["category"].as_str().unwrap(),
            );
            let (status, mut body) = match created {
                Ok(v) => (200, v),
                Err(e) => (e.status, json!({"detail":e.detail})),
            };
            let id = body["game_id"].as_str().unwrap_or("").to_owned();
            normalize(&mut body);
            assert_eq!(
                status as u64,
                row["create_status"].as_u64().unwrap(),
                "create {row_index}"
            );
            assert_eq!(body, row["create"], "create {row_index}");
            if status != 200 {
                continue;
            };
            let mut token = String::new();
            for (action_index, a) in row["actions"].as_array().unwrap().iter().enumerate() {
                let result = match a["kind"].as_str().unwrap() {
                    "get" => s.get(&id),
                    "guess" => s.guess(
                        &id,
                        a["text"].as_str().unwrap_or(""),
                        a["confirm"].as_str().map(|_| token.as_str()),
                    ),
                    "clue" => s.clue(&id),
                    "giveup" => s.give_up(&id),
                    _ => panic!("unknown golden action"),
                };
                let (status, mut body) = match result {
                    Ok(v) => (200, v),
                    Err(e) => (e.status, json!({"detail":e.detail})),
                };
                if let Some(value) = body["resolved_token"].as_str() {
                    token = value.into()
                }
                normalize(&mut body);
                assert_eq!(
                    status as u64,
                    a["status"].as_u64().unwrap(),
                    "row {row_index} action {action_index}"
                );
                assert_eq!(body, a["body"], "row {row_index} action {action_index}");
            }
        }
    }
}
