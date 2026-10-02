//! Lanțul Cuvintelor: directed routes, bounded menus and progressive paid help.
use crate::{
    ApiError,
    catalog::daily_seed,
    content::{Content, PackItem},
    graph::Service as Graph,
    pack::{Pack, PickOptions},
    pyrandom::Random,
    session::Store,
};
use serde_json::{Value, json};
use std::{
    collections::{BTreeMap, BTreeSet, HashMap, VecDeque},
    sync::{Arc, Mutex},
};
struct Game {
    start: String,
    target: String,
    difficulty: String,
    category: String,
    daily: Option<String>,
    optimal: usize,
    chain: Vec<String>,
    won: bool,
    hint_requests: usize,
    non_improving: usize,
    earned: Option<Value>,
}
impl Game {
    fn current(&self) -> &str {
        self.chain.last().unwrap()
    }
    fn moves(&self) -> usize {
        self.chain.len() - 1
    }
}
type Profiles = [[usize; 3]; 2];
type Key = (String, String, usize);
struct Cache {
    values: HashMap<Key, Profiles>,
    fifo: VecDeque<Key>,
}
pub struct Service {
    c: Arc<Content>,
    g: Arc<Graph>,
    pack: Pack,
    store: Store<Game>,
    profiles: Mutex<Cache>,
}
pub type Lant = Service;
#[derive(Clone)]
struct Pair {
    start: String,
    target: String,
    optimal: usize,
    score: f64,
}
impl Service {
    pub fn new(c: Arc<Content>) -> Self {
        Self {
            g: Graph::new(c.clone()),
            pack: Pack::new(c.clone()),
            c,
            store: Store::new(),
            profiles: Mutex::new(Cache {
                values: HashMap::new(),
                fifo: VecDeque::new(),
            }),
        }
    }
    fn action<F>(&self, id: &str, f: F) -> Result<Value, ApiError>
    where
        F: FnOnce(&mut Game) -> Result<Value, ApiError>,
    {
        self.store
            .transaction(id, f)
            .unwrap_or_else(|| Err(ApiError::new(404, "Joc inexistent")))
    }
    fn concept(&self, id: &str) -> Value {
        json!({"id":id,"label":self.g.label(id)})
    }
    fn caption(&self, a: &str, b: &str) -> &str {
        self.c
            .lant_captions
            .get(&format!("{a}\0{b}"))
            .map_or("", String::as_str)
    }
    fn short(&self, a: &str, b: &str) -> String {
        let caption = self.caption(a, b);
        let label = if caption.is_empty() {
            "legătură directă"
        } else {
            caption
        };
        if label.chars().count() <= 34 {
            return label.into();
        };
        let prefix: String = label.chars().take(33).collect();
        let head = prefix
            .rsplit_once(' ')
            .map_or(prefix.as_str(), |(head, _)| head);
        format!(
            "{}…",
            if head.is_empty() {
                prefix.as_str()
            } else {
                head
            }
        )
    }
    fn hub(&self, id: &str) -> f64 {
        (self.g.degree(id).saturating_sub(20) as f64 * 0.08).min(1.25)
    }
    fn quality(&self, current: &str, id: &str) -> f64 {
        -(self.g.link(current, id).map_or(0., |e| e.strength) * 4. + self.g.salience(id) * 1.5
            - self.hub(id))
    }
    fn quality_cmp(&self, current: &str, a: &str, b: &str) -> std::cmp::Ordering {
        self.quality(current, a)
            .total_cmp(&self.quality(current, b))
            .then(
                self.g
                    .normalize(self.g.label(a))
                    .cmp(&self.g.normalize(self.g.label(b))),
            )
            .then(a.cmp(b))
    }
    fn route_profiles(&self, start: &str, target: &str, optimal: usize) -> Profiles {
        let key = (start.into(), target.into(), optimal);
        if let Some(p) = self
            .profiles
            .lock()
            .unwrap_or_else(|e| e.into_inner())
            .values
            .get(&key)
        {
            return *p;
        };
        let from = self.g.distances_from(start);
        let to = self.g.distances_to(target);
        let budget = optimal + 2;
        let mut layers = [
            BTreeMap::<usize, usize>::new(),
            BTreeMap::<usize, usize>::new(),
        ];
        for (id, a) in from {
            if let Some(b) = to.get(&id) {
                if a + b == optimal {
                    *layers[0].entry(a).or_default() += 1
                }
                if a + b <= budget {
                    *layers[1].entry(a).or_default() += 1
                }
            }
        }
        let mut result = [[0; 3]; 2];
        for i in 0..2 {
            let first = self
                .g
                .neighbor_ids(start)
                .iter()
                .filter(|id| {
                    to.get(*id).is_some_and(|d| {
                        if i == 0 {
                            *d == optimal - 1
                        } else {
                            *d < budget
                        }
                    })
                })
                .count();
            let middle: Vec<_> = (1..optimal)
                .map(|d| layers[i].get(&d).copied().unwrap_or(0))
                .collect();
            result[i] = [
                first,
                middle.iter().min().copied().unwrap_or(1),
                middle.iter().sum(),
            ];
        }
        let mut cache = self.profiles.lock().unwrap_or_else(|e| e.into_inner());
        if cache.fifo.len() >= 512 {
            let old = cache.fifo.pop_front().unwrap();
            cache.values.remove(&old);
        }
        if !cache.values.contains_key(&key) {
            cache.fifo.push_back(key.clone());
            cache.values.insert(key, result);
        }
        result
    }
    fn distinct(
        &self,
        current: &str,
        ids: Vec<String>,
        to: &BTreeMap<String, usize>,
    ) -> Vec<String> {
        let mut ids: Vec<_> = ids
            .into_iter()
            .collect::<BTreeSet<_>>()
            .into_iter()
            .collect();
        ids.sort_by(|a, b| {
            to.get(a)
                .unwrap_or(&1_000_000)
                .cmp(to.get(b).unwrap_or(&1_000_000))
                .then(self.quality_cmp(current, a, b))
        });
        let mut seen = BTreeSet::new();
        ids.into_iter()
            .filter(|id| {
                let key = self.g.normalize(self.g.label(id));
                !key.is_empty() && seen.insert(key)
            })
            .collect()
    }
    fn shortest(&self, v: &Game, to: &BTreeMap<String, usize>) -> Vec<String> {
        let Some(d) = to.get(v.current()) else {
            return vec![];
        };
        let ids = self
            .g
            .neighbor_ids(v.current())
            .into_iter()
            .filter(|id| !v.chain.contains(id) && to.get(id).is_some_and(|n| *d > 0 && *n == d - 1))
            .collect();
        self.distinct(v.current(), ids, to)
    }
    fn near(&self, v: &Game, to: &BTreeMap<String, usize>) -> Vec<String> {
        let budget = v.optimal as isize + 2 - v.moves() as isize;
        self.g
            .neighbor_ids(v.current())
            .into_iter()
            .filter(|id| {
                !v.chain.contains(id) && to.get(id).is_some_and(|d| (*d as isize) < budget)
            })
            .collect()
    }
    fn choice(&self, current: &str, id: &str) -> Value {
        json!({"label":self.g.label(id),"relation":self.short(current,id)})
    }
    fn choice_ids(&self, v: &Game) -> Vec<String> {
        if v.won || v.moves() >= 64 {
            return vec![];
        };
        let cur = v.current();
        let to = self.g.distances_to(&v.target);
        let legal = self
            .g
            .neighbor_ids(cur)
            .into_iter()
            .filter(|id| !v.chain.contains(id) && to.contains_key(id))
            .collect();
        let safe = self.distinct(cur, legal, &to);
        let corridor = self.near(v, &to);
        let (mut on, mut detour): (Vec<_>, Vec<_>) =
            safe.into_iter().partition(|id| corridor.contains(id));
        for rows in [&mut on, &mut detour] {
            rows.sort_by(|a, b| self.quality_cmp(cur, a, b));
        }
        let shortest: Vec<_> = on
            .iter()
            .filter(|id| to.get(cur).is_some_and(|d| *d > 0 && to[*id] == d - 1))
            .cloned()
            .collect();
        let mut chosen: Vec<_> = shortest.into_iter().take(2).collect();
        for id in on {
            if chosen.len() >= 3 {
                break;
            }
            if !chosen.contains(&id) {
                chosen.push(id)
            }
        }
        let slots = 6 - chosen.len();
        chosen.extend(detour.into_iter().take(slots));
        chosen.sort_by(|a, b| {
            self.g
                .normalize(self.g.label(a))
                .cmp(&self.g.normalize(self.g.label(b)))
                .then(a.cmp(b))
        });
        chosen
    }
    fn choices(&self, v: &Game) -> Value {
        json!(
            self.choice_ids(v)
                .iter()
                .map(|id| self.choice(v.current(), id))
                .collect::<Vec<_>>()
        )
    }
    fn path(&self, v: &Game) -> Value {
        json!(
            v.chain
                .iter()
                .enumerate()
                .map(|(i, id)| {
                    let mut step = self.concept(id);
                    if i > 0 {
                        step["relation"] = json!(self.caption(&v.chain[i - 1], id))
                    }
                    step
                })
                .collect::<Vec<_>>()
        )
    }
    fn share(&self, v: &Game) -> String {
        let mut header = "cat_de_roman_esti · Lanțul Cuvintelor".to_owned();
        if !v.category.is_empty() {
            header.push_str(&format!(" · {}", self.c.category_labels[&v.category]))
        };
        format!(
            "{header}\n🔗 {}/{} salturi\n{}",
            v.moves(),
            v.optimal,
            v.daily.as_deref().unwrap_or("")
        )
    }
    fn state(&self, id: &str, v: &Game) -> Value {
        let mut out = json!({"game_id":id,"start":self.concept(&v.start),"target":{"id":v.target,"label":self.g.label(&v.target),"description":self.g.description(&v.target)},"current":self.concept(v.current()),"path":self.path(v),"moves":v.moves(),"optimal":v.optimal,"won":v.won,"difficulty":v.difficulty,"choices":self.choices(v),"backtrack_recommended":v.difficulty=="usor"&&v.non_improving>=2});
        if let Some(hint) = &v.earned {
            out["earned_hint"] = hint.clone()
        }
        if let Some(day) = &v.daily {
            out["daily"] = json!(day)
        }
        if !v.category.is_empty() {
            out["board_category"] = json!(v.category)
        }
        if v.won {
            out["score"] = json!(score(v));
            out["share"] = json!(self.share(v))
        }
        out
    }
    fn wide(&self, item: &PackItem) -> bool {
        let p = self.route_profiles(
            item.payload["start"].as_str().unwrap(),
            item.payload["target"].as_str().unwrap(),
            item.payload["optimal"].as_u64().unwrap() as usize,
        )[1];
        p[0] >= 3 && p[1] >= 3
    }
    fn curated(
        &self,
        rng: &mut Random,
        daily: Option<&str>,
        category: &str,
        difficulty: &str,
    ) -> Option<PackItem> {
        let o = PickOptions {
            category: category.into(),
            difficulty: difficulty.into(),
            ..Default::default()
        };
        let picked = if let Some(day) = daily {
            self.pack.pick_daily("lant", day, &o)
        } else {
            self.pack.pick_seeded("lant", rng, &o)
        };
        let picked = picked?;
        if difficulty != "usor" || self.wide(picked) {
            return Some(picked.clone());
        }
        if daily.is_none() && rng.randbelow(4) == 0 {
            return Some(picked.clone());
        };
        let pool: Vec<_> = self
            .pack
            .pool("lant", &o)
            .into_iter()
            .filter(|p| !self.c.pack_ranked || p.pilot_eligible)
            .cloned()
            .collect();
        let minimum = if daily.is_some() && category.is_empty() {
            8
        } else {
            3.min(pool.len())
        };
        let wide: Vec<_> = pool.iter().filter(|p| self.wide(p)).cloned().collect();
        let pool = if wide.len() >= minimum.max(1) {
            wide
        } else {
            pool
        };
        let narrowed = Pack::from_items(pool, self.c.pack_ranked);
        if let Some(day) = daily {
            narrowed.pick_daily("lant", day, &o).cloned()
        } else {
            narrowed.pick_seeded("lant", rng, &o).cloned()
        }
    }
    fn mine(&self, rng: &mut Random, category: &str, difficulty: &str) -> Result<Pair, ApiError> {
        let (lo, hi) = match difficulty {
            "usor" => (2, 3),
            "greu" => (4, 6),
            _ => (3, 4),
        };
        let pool = if category.is_empty() {
            self.g.all_ids()
        } else {
            self.g.by_category(category)
        };
        let mut candidates: Vec<_> = pool
            .iter()
            .filter(|id| self.g.degree(id) >= 2)
            .cloned()
            .collect();
        if candidates.is_empty() && category.is_empty() {
            candidates = pool
                .into_iter()
                .filter(|id| self.g.degree(id) >= 1)
                .collect()
        }
        if candidates.is_empty() {
            return Err(ApiError::new(
                503,
                if category.is_empty() {
                    "Graful nu are noduri jucabile."
                } else {
                    "Nu există încă jocuri pentru această categorie."
                },
            ));
        }
        if difficulty == "usor" {
            let salient: Vec<_> = candidates
                .iter()
                .filter(|id| self.g.salience(id) >= 0.6)
                .cloned()
                .collect();
            if salient.len() >= 8 {
                candidates = salient
            }
        }
        let endpoint: BTreeSet<_> = candidates.iter().cloned().collect();
        let weight = match difficulty {
            "usor" => 16.,
            "greu" => 2.,
            _ => 9.,
        };
        let (mut best_good, mut best_any, mut fallback): (
            Option<Pair>,
            Option<Pair>,
            Option<Pair>,
        ) = (None, None, None);
        let mut good_count = 0;
        for _ in 0..140 {
            let start = &candidates[rng.randbelow(candidates.len())];
            let (dist, order) = self.g.distances_from_ordered(start);
            let mut reachable: Vec<_> = order
                .into_iter()
                .filter(|id| {
                    (lo..=hi).contains(&dist[id]) && self.g.degree(id) >= 2 && endpoint.contains(id)
                })
                .collect();
            if reachable.is_empty() {
                continue;
            }
            rng.shuffle(&mut reachable);
            for target in reachable.into_iter().take(24) {
                let optimal = dist[&target];
                let p = self.route_profiles(start, &target, optimal);
                let salience = (self.g.salience(start) + self.g.salience(&target)) / 2.;
                let score = (p[0][1] * 10 + p[0][0] * 3 + p[0][2]) as f64 + salience * weight
                    - (self.hub(start) + self.hub(&target));
                let value = Pair {
                    start: start.clone(),
                    target,
                    optimal,
                    score,
                };
                if fallback.is_none() {
                    fallback = Some(value.clone())
                }
                if best_any.as_ref().is_none_or(|p| score > p.score) {
                    best_any = Some(value.clone())
                }
                if p[0][0] >= 2
                    && p[0][1] >= 2
                    && (difficulty != "usor" || p[1][0] >= 3 && p[1][1] >= 3)
                {
                    if best_good.as_ref().is_none_or(|p| score > p.score) {
                        best_good = Some(value)
                    }
                    good_count += 1;
                }
            }
            if good_count >= 6 {
                break;
            }
        }
        best_good.or(best_any).or(fallback).ok_or_else(|| {
            ApiError::new(
                503,
                if category.is_empty() {
                    "Nu am putut genera un lanț valid; reîncearcă."
                } else {
                    "Nu există încă jocuri pentru această categorie."
                },
            )
        })
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
        }
        let mut rng = if let Some(day) = daily {
            Random::from_u64(daily_seed(day, "lant"))
        } else {
            rng(seed)
        };
        let p = if let Some(item) = self.curated(&mut rng, daily, category, difficulty) {
            Pair {
                start: item.payload["start"].as_str().unwrap().into(),
                target: item.payload["target"].as_str().unwrap().into(),
                optimal: item.payload["optimal"].as_u64().unwrap() as usize,
                score: 0.,
            }
        } else {
            self.mine(&mut rng, category, difficulty)?
        };
        let v = Game {
            chain: vec![p.start.clone()],
            start: p.start,
            target: p.target,
            optimal: p.optimal,
            difficulty: difficulty.into(),
            category: category.into(),
            daily: daily.map(str::to_owned),
            won: false,
            hint_requests: 0,
            non_improving: 0,
            earned: None,
        };
        let mut out = self.state("", &v);
        let id = self
            .store
            .create(v)
            .map_err(|_| ApiError::new(503, "Prea multe jocuri active. Încearcă din nou."))?;
        out["game_id"] = json!(id);
        Ok(out)
    }
    pub fn get(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |v| Ok(self.state(id, v)))
    }
    fn resolve_neighbor(&self, text: &str, current: &str, target: &str) -> Option<String> {
        let primary = self.g.resolve(text);
        let key = self.g.normalize(text);
        if key.is_empty() {
            return primary;
        };
        let legal: Vec<_> = self
            .g
            .all_ids()
            .into_iter()
            .filter(|id| {
                id != current
                    && self.g.normalize(self.g.label(id)) == key
                    && self.g.link(current, id).is_some()
            })
            .collect();
        if legal.is_empty() {
            return primary;
        };
        if legal.len() == 1 {
            return Some(legal[0].clone());
        }
        self.distinct(current, legal, &self.g.distances_to(target))
            .into_iter()
            .next()
    }
    pub fn move_input<F>(&self, id: &str, validate: F) -> Result<Value, ApiError>
    where
        F: FnOnce() -> Result<String, ApiError>,
    {
        self.action(id,|v|{let text=validate()?;if v.won{let mut out=self.state(id,v);out["ok"]=json!(true);return Ok(out)}
if v.moves()>=64{return Ok(json!({"ok":false,"last_error":"Limită atinsă — folosește Înapoi."}))}
if text.trim_matches(py_space).is_empty(){return Ok(json!({"ok":false,"last_error":"Scrie un concept"}))}
if self.g.reviewed_unresolved(&text){return Ok(json!({"ok":false,"last_error":"Nu cunosc acest concept","suggestions":[]}))}let prev=v.current().to_owned();let key=self.g.normalize(&text);let visible:Vec<_>=self.choice_ids(v).into_iter().filter(|id|self.g.normalize(self.g.label(id))==key).collect();let mut guess=if visible.len()==1{Some(visible[0].clone())}else{self.resolve_neighbor(&text,&prev,&v.target)};let mut corrected=false;if guess.is_none(){guess=self.g.resolve_fuzzy(&text);corrected=guess.is_some()}let Some(guess)=guess else{let suggestions=self.g.suggest(&text,3);let message=suggestions.first().map_or_else(||"Nu cunosc acest concept".to_owned(),|label|format!("Nu cunosc acest concept. Poate căutai: {label}?"));return Ok(json!({"ok":false,"last_error":message,"suggestions":suggestions}))};let understood=if corrected{format!("Am înțeles: {}. ",self.g.label(&guess))}else{String::new()};if guess==prev{return Ok(json!({"ok":false,"last_error":format!("{understood}Ești deja aici.")}))}
if self.g.link(&prev,&guess).is_none(){return Ok(json!({"ok":false,"last_error":format!("{understood}{} nu are o legătură directă cu {}. Alege un cuvânt din listă sau cere un indiciu.",self.g.display_label(&guess),self.g.label(&prev))}))}v.chain.push(guess.clone());v.earned=None;v.won=guess==v.target;let mut notes=vec![];if corrected{notes.push(format!("Am înțeles: {}.",self.g.label(&guess)))}let to=self.g.distances_to(&v.target);let before=to.get(&prev);let after=to.get(&guess);let dead=!v.won&&after.is_none();if dead&&v.difficulty!="usor"{notes.push("Atenție: fundătură — de aici ținta nu mai e accesibilă.".into())}let progress=if ["usor","normal"].contains(&v.difficulty.as_str()){let kind=if v.won{"won"}else if dead{"dead_end"}else if before.is_none()||after<before{"closer"}else if after==before{"lateral"}else{"farther"};if ["closer","won"].contains(&kind){v.non_improving=0}else{v.non_improving=(v.non_improving+1).min(2)}let message=match kind{"closer"=>"Mai aproape de țintă.","lateral"=>"Tot cam la aceeași distanță.","farther"=>"Te-ai îndepărtat puțin.","dead_end"=>"Fundătură — folosește Înapoi.",_=>"Ai ajuns la țintă!"};Some(json!({"kind":kind,"message":message}))}else{v.non_improving=0;None};let mut out=json!({"ok":true,"current":self.concept(&guess),"relation":self.caption(&prev,&guess),"path":self.path(v),"moves":v.moves(),"won":v.won,"choices":self.choices(v),"backtrack_recommended":v.difficulty=="usor"&&v.non_improving>=2});if let Some(p)=progress{out["progress"]=p}
if dead{out["dead_end"]=json!(true)}
if !notes.is_empty(){out["message"]=json!(notes.join(" "))}
if v.won{out["score"]=json!(score(v));out["share"]=json!(self.share(v))}Ok(out)})
    }
    pub fn move_word(&self, id: &str, text: &str) -> Result<Value, ApiError> {
        self.move_input(id, || Ok(text.into()))
    }
    pub fn undo(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |v| {
            if !v.won {
                if v.chain.len() > 1 {
                    v.chain.pop();
                    v.earned = None;
                    v.won = v.current() == v.target
                }
                v.non_improving = 0
            }
            Ok(self.state(id, v))
        })
    }
    pub fn hint(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id,|v|{if v.won{return Ok(earn(v,json!({"hint":null,"message":"Ai ajuns deja la țintă."})))}
if v.moves()>=64{return Ok(earn(v,json!({"hint":null,"stage":"backtrack","message":"Limită atinsă — folosește Înapoi."})))}v.hint_requests=(v.hint_requests+1).min(3);let cur=v.current().to_owned();let to=self.g.distances_to(&v.target);let Some(remaining)=to.get(&cur).copied()else{if let Some(id)=v.chain.iter().rev().find(|id|**id!=cur&&to.contains_key(*id)){let message=format!("Fundătură — folosește Înapoi până la {}.",self.g.label(id));return Ok(earn(v,json!({"hint":null,"stage":"backtrack","message":message})))}return Ok(earn(v,json!({"hint":null,"message":"Nicio scurtătură de aici — încearcă să revii cu Înapoi."})))};let shortest=self.shortest(v,&to);let forward=if !shortest.is_empty(){shortest.clone()}else{self.distinct(&cur,self.g.neighbor_ids(&cur).into_iter().filter(|id|!v.chain.contains(id)&&to.contains_key(id)).collect(),&to)};if forward.is_empty(){let prior:BTreeSet<_>=self.g.neighbor_ids(&cur).into_iter().filter(|id|v.chain[..v.chain.len()-1].contains(id)&&to.get(id).is_some_and(|d|remaining>0&&*d==remaining-1)).collect();if let Some(id)=v.chain[..v.chain.len()-1].iter().rev().find(|id|prior.contains(*id)){let message=format!("Drumul continuă printr-un pas deja vizitat. Folosește Înapoi până la {}.",self.g.label(id));return Ok(earn(v,json!({"hint":null,"stage":"backtrack","remaining":remaining,"message":message})))}}
if let Some(best)=forward.first(){let mut out=json!({"hint":null,"remaining":1+to[best],"alternatives":forward.len()});if v.hint_requests==1{let relation=self.short(&cur,best);if relation!="legătură directă"{out["stage"]=json!("direction");out["relation"]=json!(relation);out["message"]=json!(format!("Direcție: caută o legătură „{relation}”."));return Ok(earn(v,out))}v.hint_requests=2}
if v.hint_requests==2{let near=if shortest.is_empty(){forward.clone()}else{let mut ids=shortest;ids.extend(self.near(v,&to));self.distinct(&cur,ids,&to)};let choices:Vec<_>=near.iter().take(2).map(|id|self.choice(&cur,id)).collect();let labels:Vec<_>=near.iter().take(2).map(|id|self.g.label(id).to_owned()).collect();let lead=if choices.len()==1{"O variantă utilă: "}else{"Variante utile: "};out["stage"]=json!("alternatives");out["alternatives_choices"]=json!(choices);out["alternatives_labels"]=json!(labels);out["message"]=json!(format!("{lead}{}.",labels.join(", ")));return Ok(earn(v,out))}out["stage"]=json!("hop");out["hint"]=self.concept(best);out["relation"]=json!(self.short(&cur,best));out["message"]=json!(format!("Un salt bun: {}.",self.g.label(best)));return Ok(earn(v,out))}Ok(earn(v,json!({"hint":null,"message":"Niciun indiciu disponibil."})))})
    }
}
fn earn(v: &mut Game, payload: Value) -> Value {
    if !v.won {
        v.earned = Some(payload.clone())
    }
    payload
}
fn score(v: &Game) -> usize {
    (1000. * v.optimal as f64 / v.moves().max(1).max(v.optimal) as f64)
        .round_ties_even()
        .max(100.) as usize
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
fn py_space(c: char) -> bool {
    matches!(c,'\u{9}'..='\u{d}'|'\u{1c}'..='\u{20}'|'\u{85}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}')
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn pinned_validation_and_concurrent_hint_stages() {
        let s = Arc::new(Service::new(Arc::new(Content::load().unwrap())));
        let game = s.create(Some("17"), "normal", None, "").unwrap();
        let id = game["game_id"].as_str().unwrap().to_owned();
        assert_eq!(
            s.move_input("missing", || panic!("validator on missing session"))
                .unwrap_err()
                .status,
            404
        );
        assert_eq!(
            s.move_input(&id, || {
                assert!(!s.store.delete(&id));
                Err(ApiError::new(422, "validation"))
            })
            .unwrap_err()
            .status,
            422
        );
        let workers: Vec<_> = (0..24)
            .map(|_| {
                let s = s.clone();
                let id = id.clone();
                std::thread::spawn(move || s.hint(&id).unwrap())
            })
            .collect();
        for w in workers {
            w.join().unwrap();
        }
        s.store.transaction(&id, |v| {
            assert_eq!(v.hint_requests, 3);
            assert_eq!(v.moves(), 0);
        });
        assert!(s.profiles.lock().unwrap().values.len() <= 512);
    }
    fn normalize(v: &mut Value) {
        match v {
            Value::Object(map) => {
                for (k, v) in map {
                    if k == "game_id" {
                        *v = json!("<session>")
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
            "../../go-backend/internal/lant/testdata/python_games.json"
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
            for (action_index, a) in row["actions"].as_array().unwrap().iter().enumerate() {
                let result = match a["kind"].as_str().unwrap() {
                    "get" => s.get(&id),
                    "move" => s.move_word(&id, a["text"].as_str().unwrap()),
                    "hint" => s.hint(&id),
                    "undo" => s.undo(&id),
                    _ => panic!("unknown golden action"),
                };
                let (status, mut body) = match result {
                    Ok(v) => (200, v),
                    Err(e) => (e.status, json!({"detail":e.detail})),
                };
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
