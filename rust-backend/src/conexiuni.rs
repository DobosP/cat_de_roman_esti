//! Reviewed Conexiuni boards, exact bounded graph mining, and redacted clues.
use crate::ApiError;
use crate::catalog::daily_seed;
use crate::content::{Content, PackItem};
use crate::graph;
use crate::pack::{Pack, PickOptions};
use crate::pyrandom::Random;
use crate::session::{Store, StoreError};
use num_bigint::BigInt;
use serde_json::{Value, json};
use std::collections::{BTreeMap, BTreeSet};
use std::sync::{Arc, OnceLock};
struct GameSession {
    groups: BTreeMap<String, Vec<String>>,
    order: Vec<String>,
    solved: Vec<String>,
    lives: usize,
    mistakes: usize,
    won: bool,
    lost: bool,
    difficulty: String,
    daily: String,
    category: String,
    labels: BTreeMap<String, String>,
    clues: Vec<Value>,
    clued: Vec<String>,
    clues_used: usize,
    history: Vec<Vec<String>>,
}
struct RankedSet {
    categories: Vec<String>,
    entanglement: f64,
}
pub struct Conexiuni {
    data: Arc<Content>,
    graph: Arc<graph::Service>,
    pack: Pack,
    store: Store<GameSession>,
    ranked: OnceLock<Vec<RankedSet>>,
}
fn fail(status: u16, detail: &str) -> ApiError {
    ApiError::new(status, detail)
}
fn list(value: &Value) -> Option<Vec<String>> {
    value
        .as_array()?
        .iter()
        .map(|value| value.as_str().map(str::to_owned))
        .collect()
}
fn new_session(
    groups: BTreeMap<String, Vec<String>>,
    order: Vec<String>,
    difficulty: &str,
    daily: &str,
    category: &str,
    labels: BTreeMap<String, String>,
) -> GameSession {
    GameSession {
        groups,
        order,
        solved: Vec::new(),
        lives: 4,
        mistakes: 0,
        won: false,
        lost: false,
        difficulty: difficulty.to_owned(),
        daily: daily.to_owned(),
        category: category.to_owned(),
        labels,
        clues: Vec::new(),
        clued: Vec::new(),
        clues_used: 0,
        history: Vec::new(),
    }
}
fn python_sum(values: &[f64]) -> f64 {
    let (mut hi, mut lo) = (0_f64, 0_f64);
    for &x in values {
        let t = hi + x;
        if hi.abs() >= x.abs() {
            lo += (hi - t) + x;
        } else {
            lo += (x - t) + hi;
        }
        hi = t;
    }
    hi + lo
}
fn seeded(seed: Option<&str>) -> Result<Random, ApiError> {
    if let Some(seed) = seed {
        let value: BigInt = seed
            .parse()
            .map_err(|_| fail(422, "seed trebuie să fie un număr întreg."))?;
        Ok(Random::new(&value))
    } else {
        let mut bytes = [0u8; 32];
        getrandom::fill(&mut bytes)
            .map_err(|_| fail(503, "Jocul nu a putut fi creat. Încearcă din nou."))?;
        Ok(Random::from_words(
            &bytes
                .as_chunks::<4>()
                .0
                .iter()
                .map(|part| u32::from_le_bytes(*part))
                .collect::<Vec<_>>(),
        ))
    }
}
fn owner<'a>(game: &'a GameSession, id: &str) -> Option<&'a str> {
    game.groups
        .iter()
        .find(|(_, members)| members.iter().any(|member| member == id))
        .map(|(cat, _)| cat.as_str())
}
fn clue_available(game: &GameSession) -> bool {
    !game.won
        && !game.lost
        && game.clues_used < 2
        && game.mistakes >= 2 + game.clues_used
        && game.solved.len() < game.groups.len()
}
fn pattern(label: &str, ranges: &[[u32; 2]]) -> String {
    let mut out = String::new();
    let mut start = true;
    for ch in label.chars() {
        let code = ch as u32;
        let index = ranges.partition_point(|range| range[1] < code);
        if ranges.get(index).is_some_and(|range| range[0] <= code) {
            if start {
                out.extend(ch.to_uppercase());
                start = false;
            } else {
                out.push('_');
            }
        } else {
            out.push(ch);
            start = ch.is_whitespace() || matches!(ch, '\u{1c}'..='\u{1f}');
        }
    }
    out
}
impl Conexiuni {
    pub fn new(data: Arc<Content>) -> Self {
        let g = graph::Service::new(Arc::clone(&data));
        Self::new_with_graph(data, g)
    }
    pub fn new_with_graph(data: Arc<Content>, graph: Arc<graph::Service>) -> Self {
        Self {
            pack: Pack::new(Arc::clone(&data)),
            data,
            graph,
            store: Store::new(),
            ranked: OnceLock::new(),
        }
    }
    fn rank_categories(&self) -> Vec<RankedSet> {
        let mut ranked = Vec::new();
        let usable: Vec<String> = self
            .data
            .category_order
            .iter()
            .filter(|cat| self.graph.by_category(cat).len() >= 4)
            .cloned()
            .collect();
        let mut ent: BTreeMap<(String, String), f64> = BTreeMap::new();
        for (i, a) in usable.iter().enumerate() {
            let am = self.graph.by_category(a);
            for b in &usable[i + 1..] {
                let bm = self.graph.by_category(b);
                let bs: BTreeSet<_> = bm.iter().collect();
                let cross: usize = am
                    .iter()
                    .map(|id| {
                        self.graph
                            .neighbor_ids(id)
                            .iter()
                            .filter(|id| bs.contains(id))
                            .count()
                    })
                    .sum();
                ent.insert(
                    (a.clone(), b.clone()),
                    cross as f64 / ((am.len() * bm.len()) as f64).powf(0.5),
                );
            }
        }
        for a in 0..usable.len() {
            for b in a + 1..usable.len() {
                for c in b + 1..usable.len() {
                    for d in c + 1..usable.len() {
                        let mut cats = vec![
                            usable[a].clone(),
                            usable[b].clone(),
                            usable[c].clone(),
                            usable[d].clone(),
                        ];
                        cats.sort();
                        let mut values = Vec::new();
                        for (i, x) in cats.iter().enumerate() {
                            for y in &cats[i + 1..] {
                                values.push(*ent.get(&(x.clone(), y.clone())).unwrap_or(&0.));
                            }
                        }
                        ranked.push(RankedSet {
                            categories: cats,
                            entanglement: python_sum(&values),
                        });
                    }
                }
            }
        }
        ranked.sort_by(|a, b| {
            a.entanglement
                .total_cmp(&b.entanglement)
                .then(a.categories.cmp(&b.categories))
        });
        ranked
    }
    fn build_board(&self, random: &mut Random, difficulty: &str) -> Result<GameSession, ApiError> {
        // Match Python's lazy fallback cache; curated creates need no table.
        let ranked = self.ranked.get_or_init(|| self.rank_categories());
        let n = ranked.len();
        if n == 0 {
            return Err(fail(503, "Nu există suficiente categorii pentru un joc."));
        }
        let third = (n / 3).max(1);
        let pool = match difficulty {
            "usor" => &ranked[..third],
            "greu" => &ranked[n - third..],
            _ => ranked,
        };
        let cats = &pool[random.randbelow(pool.len())].categories;
        let members: BTreeMap<String, BTreeSet<String>> = cats
            .iter()
            .map(|cat| {
                (
                    cat.clone(),
                    self.graph.by_category(cat).into_iter().collect(),
                )
            })
            .collect();
        let all: BTreeSet<String> = members.values().flatten().cloned().collect();
        let mut groups = BTreeMap::new();
        let mut order = Vec::new();
        for cat in cats {
            let ids = self.graph.by_category(cat);
            let own = &members[cat];
            let fair: Vec<_> = ids
                .iter()
                .filter(|id| {
                    let neighbors = self.graph.neighbor_ids(id);
                    let own_count = neighbors
                        .iter()
                        .filter(|node| *node != *id && own.contains(*node))
                        .count();
                    let foreign = neighbors
                        .iter()
                        .filter(|node| all.contains(*node) && !own.contains(*node))
                        .count();
                    foreign <= own_count
                })
                .cloned()
                .collect();
            let mut choices = if fair.len() >= 4 { fair } else { ids };
            if difficulty == "usor" || difficulty == "greu" {
                choices.sort_by(|a, b| {
                    let sa = self.graph.salience(a);
                    let sb = self.graph.salience(b);
                    if sa == sb {
                        a.cmp(b)
                    } else if difficulty == "usor" {
                        sb.total_cmp(&sa)
                    } else {
                        sa.total_cmp(&sb)
                    }
                });
            } else {
                random.shuffle(&mut choices);
            }
            let mut picked = choices[..4].to_vec();
            picked.sort();
            order.extend(picked.clone());
            groups.insert(cat.clone(), picked);
        }
        random.shuffle(&mut order);
        Ok(new_session(
            groups,
            order,
            difficulty,
            "",
            "",
            BTreeMap::new(),
        ))
    }
    fn quality(&self, game: &GameSession) -> (bool, usize) {
        let mut owners = BTreeMap::new();
        let mut total = 0;
        for (cat, members) in &game.groups {
            for id in members {
                total += 1;
                owners.insert(id, cat);
            }
        }
        if total != 16 || owners.len() != 16 {
            return (false, 1_000_000);
        }
        let mut residual = 0;
        for (id, cat) in &owners {
            let mut own = 0;
            let mut foreign: BTreeMap<&String, usize> = BTreeMap::new();
            for node in self.graph.neighbor_ids(id) {
                if let Some(other) = owners.get(&node) {
                    if *other == *cat && &node != *id {
                        own += 1;
                    } else if *other != *cat {
                        *foreign.entry(other).or_default() += 1;
                    }
                }
            }
            let worst = foreign.values().copied().max().unwrap_or(0);
            if worst > own {
                return (false, 1_000_000);
            }
            if worst == own && own > 0 {
                residual += 1;
            }
        }
        (true, residual)
    }
    fn pick_board(&self, random: &mut Random, difficulty: &str) -> Result<GameSession, ApiError> {
        let mut best = None;
        let mut best_residual = 1_000_000;
        for _ in 0..16 {
            let candidate = self.build_board(random, difficulty)?;
            let (ok, residual) = self.quality(&candidate);
            if ok && residual == 0 {
                return Ok(candidate);
            }
            if ok && residual < best_residual {
                best = Some(candidate);
                best_residual = residual;
            }
        }
        best.ok_or_else(|| fail(503, "Nu am putut genera o tablă validă; reîncearcă."))
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
        if !category.is_empty() && !self.data.category_labels.contains_key(category) {
            return Err(fail(400, "Categorie necunoscută."));
        }
        let options = PickOptions {
            category: category.to_owned(),
            difficulty: difficulty.to_owned(),
            ..Default::default()
        };
        let mut random;
        let item = if !daily.is_empty() {
            random = Random::from_u64(daily_seed(daily, "conexiuni"));
            self.pack.pick_daily("conexiuni", daily, &options)
        } else {
            random = seeded(seed)?;
            self.pack.pick_seeded("conexiuni", &mut random, &options)
        };
        let game = if let Some(item) = item {
            curated(item, daily, category)?
        } else if !category.is_empty() {
            return Err(fail(503, "Nu există încă jocuri pentru această categorie."));
        } else {
            let mut game = self.pick_board(&mut random, difficulty)?;
            game.daily = daily.to_owned();
            game
        };
        let mut body = self.state("", &game);
        let id = self.store.create(game).map_err(|failure| match failure {
            StoreError::Capacity => fail(503, "Prea multe jocuri active. Încearcă din nou."),
            _ => fail(503, "Jocul nu a putut fi creat. Încearcă din nou."),
        })?;
        body["game_id"] = json!(id);
        Ok(body)
    }
    fn concept(&self, id: &str) -> Value {
        json!({"id":id,"label":self.data.labels.get(id).map(String::as_str).unwrap_or(id)})
    }
    fn label<'a>(&'a self, game: &'a GameSession, cat: &'a str) -> &'a str {
        game.labels
            .get(cat)
            .or_else(|| self.data.category_labels.get(cat))
            .map(String::as_str)
            .unwrap_or(cat)
    }
    fn group(&self, game: &GameSession, cat: &str) -> Value {
        json!({"key":cat,"label":self.label(game,cat),"tiles":game.groups[cat].iter().map(|id|self.concept(id)).collect::<Vec<_>>()})
    }
    fn share(&self, game: &GameSession) -> String {
        let cats: Vec<&str> = game.groups.keys().map(String::as_str).collect();
        let emoji = ["🟩", "🟦", "🟪", "🟧"];
        let rows: Vec<String> = game
            .history
            .iter()
            .map(|guess| {
                guess
                    .iter()
                    .map(|id| {
                        emoji[owner(game, id)
                            .and_then(|cat| cats.binary_search(&cat).ok())
                            .unwrap_or(0)
                            % 4]
                    })
                    .collect()
            })
            .collect();
        let mut header = "cat_de_roman_esti · Conexiuni · ".to_owned();
        if !game.category.is_empty() {
            header.push_str(&format!("{} · ", self.data.category_labels[&game.category]));
        }
        let word = if game.mistakes == 1 {
            "greșeală"
        } else {
            "greșeli"
        };
        header.push_str(&format!("{} {word}", game.mistakes));
        if game.clues_used > 0 {
            header.push_str(&format!(" · indiciu x{}", game.clues_used));
        }
        if !game.daily.is_empty() {
            header.push_str(&format!(" · {}", game.daily));
        }
        format!(
            "{header}\n{}",
            if rows.is_empty() {
                "—".to_owned()
            } else {
                rows.join("\n")
            }
        )
    }
    fn state(&self, id: &str, game: &GameSession) -> Value {
        let terminal = game.won || game.lost;
        let solved_ids: BTreeSet<&str> = game
            .solved
            .iter()
            .flat_map(|category| game.groups[category].iter().map(String::as_str))
            .collect();
        let tiles: Vec<Value> = game
            .order
            .iter()
            .filter(|id| terminal || !solved_ids.contains(id.as_str()))
            .map(|id| self.concept(id))
            .collect();
        let mut body = json!({"game_id":id,"tiles":tiles,"solved":game.solved.iter().map(|cat|self.group(game,cat)).collect::<Vec<_>>(),"solved_count":game.solved.len(),"remaining_groups":game.groups.len()-game.solved.len(),"lives":game.lives,"mistakes":game.mistakes,"won":game.won,"lost":game.lost,"difficulty":game.difficulty,"clues_used":game.clues_used,"clue_available":clue_available(game),"clues":game.clues});
        if !game.daily.is_empty() {
            body["daily"] = json!(game.daily);
        }
        if !game.category.is_empty() {
            body["board_category"] = json!(game.category);
        }
        if terminal {
            body["score"] =
                json!(1000usize.saturating_sub(250 * game.mistakes + 100 * game.clues_used));
            body["share"] = json!(self.share(game));
            let mut order = game.solved.clone();
            order.extend(
                game.groups
                    .keys()
                    .filter(|cat| !game.solved.contains(cat))
                    .cloned(),
            );
            body["solution"] = json!(
                order
                    .iter()
                    .map(|cat| self.group(game, cat))
                    .collect::<Vec<_>>()
            );
        }
        body
    }
    fn action(
        &self,
        id: &str,
        callback: impl FnOnce(&mut GameSession) -> Result<Value, ApiError>,
    ) -> Result<Value, ApiError> {
        self.store
            .transaction(id, callback)
            .ok_or_else(|| fail(404, "Joc inexistent"))?
    }
    pub fn get(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |game| Ok(self.state(id, game)))
    }
    pub fn guess(&self, id: &str, ids: Vec<String>) -> Result<Value, ApiError> {
        self.guess_input(id, || Ok(ids))
    }
    pub fn guess_input(
        &self,
        id: &str,
        validate: impl FnOnce() -> Result<Vec<String>, ApiError>,
    ) -> Result<Value, ApiError> {
        self.action(id, |game| {
            let ids = validate()?;
            if game.won || game.lost {
                return Err(fail(400, "Jocul s-a terminat"));
            }
            let key: BTreeSet<_> = ids.iter().collect();
            if ids.len() != 4 || key.len() != 4 {
                return Err(fail(400, "Alege exact 4 concepte distincte"));
            }
            for node in &ids {
                if !game.order.contains(node) {
                    return Err(fail(400, "Concept care nu e pe tablă"));
                }
                if owner(game, node)
                    .is_some_and(|cat| game.solved.iter().any(|solved| solved == cat))
                {
                    return Err(fail(400, "Concept deja rezolvat"));
                }
            }
            if game
                .history
                .iter()
                .any(|previous| previous.iter().collect::<BTreeSet<_>>() == key)
            {
                return Err(fail(409, "Ai încercat deja această combinație."));
            }
            game.history.push(ids.clone());
            let mut counts: BTreeMap<String, usize> = BTreeMap::new();
            for node in &ids {
                if let Some(cat) = owner(game, node) {
                    *counts.entry(cat.to_owned()).or_default() += 1;
                }
            }
            if counts.len() == 1 {
                let shared = counts.keys().next().unwrap().clone();
                game.solved.push(shared.clone());
                game.won = game.solved.len() == 4;
                let mut body = self.state(id, game);
                body["ok"] = json!(true);
                body["correct"] = json!(true);
                body["category"] = json!({"key":shared,"label":self.label(game,&shared)});
                return Ok(body);
            }
            game.mistakes += 1;
            game.lives -= 1;
            game.lost = game.lives == 0;
            let mut body = self.state(id, game);
            body["ok"] = json!(true);
            body["correct"] = json!(false);
            body["one_away"] = json!(counts.values().any(|count| *count == 3));
            Ok(body)
        })
    }
    pub fn clue(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |game| {
            if game.won || game.lost { return Err(fail(400, "Jocul s-a terminat")); }
            if game.clues_used >= 2 { return Err(fail(400, "Indiciile au fost deja folosite")); }
            if game.mistakes < 2 + game.clues_used {
                let need = 2 + game.clues_used - game.mistakes;
                let word = if need == 1 { "greșeală" } else { "greșeli" };
                return Err(fail(400, &format!("Indiciul apare după încă {need} {word}.")));
            }
            let unsolved: Vec<String> = game.groups.keys().filter(|cat| !game.solved.contains(cat)).cloned().collect();
            let mut cat = unsolved[0].clone();
            if unsolved.len() > 1 && let Some(previous) = game.clued.last()
                && let Some(next) = unsolved.iter().find(|cat| *cat > previous) { cat = next.clone(); }
            game.clued.push(cat.clone());
            let label = self.label(game, &cat);
            let redacted = self.data.label_patterns.get(label).cloned()
                .unwrap_or_else(|| pattern(label, &self.data.letter_ranges));
            let clue = json!({"pattern": redacted, "message": format!("Numele unui grup rămas: {redacted} (fiecare _ este o literă lipsă).")});
            game.clues.push(clue.clone()); game.clues_used += 1;
            let mut body = self.state(id, game); body["ok"] = json!(true); body["clue"] = clue;
            Ok(body)
        })
    }
}
fn curated(item: &PackItem, daily: &str, category: &str) -> Result<GameSession, ApiError> {
    let invalid = || fail(503, "Tabla Conexiuni este invalidă.");
    let groups: BTreeMap<String, Vec<String>> = item.payload["groups"]
        .as_object()
        .filter(|groups| groups.len() == 4)
        .ok_or_else(invalid)?
        .iter()
        .map(|(cat, ids)| {
            list(ids)
                .filter(|ids| ids.len() == 4)
                .map(|ids| (cat.clone(), ids))
                .ok_or_else(invalid)
        })
        .collect::<Result<_, _>>()?;
    let order = list(&item.payload["order"])
        .filter(|order| order.len() == 16)
        .ok_or_else(invalid)?;
    let labels: BTreeMap<String, String> = item.payload["group_labels"]
        .as_object()
        .ok_or_else(invalid)?
        .iter()
        .map(|(cat, label)| {
            label
                .as_str()
                .map(|label| (cat.clone(), label.to_owned()))
                .ok_or_else(invalid)
        })
        .collect::<Result<_, _>>()?;
    Ok(new_session(
        groups,
        order,
        &item.difficulty,
        daily,
        category,
        labels,
    ))
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::thread;
    #[test]
    fn curated_creation_leaves_fallback_ranking_cold() {
        let service = Conexiuni::new(Arc::new(Content::load().unwrap()));
        assert!(service.ranked.get().is_none());
        service.create(Some("17"), "", "", "normal").unwrap();
        assert!(service.ranked.get().is_none());
        service
            .pick_board(&mut Random::from_u64(13), "normal")
            .unwrap();
        assert!(!service.ranked.get().unwrap().is_empty());
    }
    fn compare(result: Result<Value, ApiError>, expected: &Value) {
        let (status, mut body) = match result {
            Ok(body) => (200, body),
            Err(error) => (error.status, json!({"detail":error.detail})),
        };
        if status == 200 {
            body["game_id"] = json!("<session>");
        }
        assert_eq!(json!(status), expected["status"]);
        assert_eq!(body, expected["body"]);
    }
    #[test]
    fn python_api_goldens_cover_curated_mined_and_exact_daily_floors() {
        let vectors: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/conexiuni/testdata/python-goldens.json"
        ))
        .unwrap();
        let base = Arc::new(Content::load().unwrap());
        let default_service = Conexiuni::new(Arc::clone(&base));
        for case in vectors["cases"].as_array().unwrap() {
            let category = case["category"].as_str().unwrap();
            let difficulty = case["difficulty"].as_str().unwrap();
            let custom;
            if let Some(limit) = case["pack_limit"].as_u64() {
                let mut modified = (*base).clone();
                modified.pack_items.retain(|item| {
                    item.game == "conexiuni"
                        && item.pilot_eligible
                        && item.difficulty == difficulty
                        && (category.is_empty() || item.category == category)
                });
                modified.pack_items.sort_by(|a, b| a.id.cmp(&b.id));
                modified.pack_items.truncate(limit as usize);
                custom = Some(Conexiuni::new_with_graph(
                    Arc::new(modified),
                    Arc::clone(&default_service.graph),
                ));
            } else {
                custom = None;
            }
            let service = custom.as_ref().unwrap_or(&default_service);
            let result = service.create(
                case["seed"].as_str(),
                case["daily"].as_str().unwrap(),
                category,
                difficulty,
            );
            let id = result
                .as_ref()
                .ok()
                .map(|body| body["game_id"].as_str().unwrap().to_owned())
                .unwrap_or_default();
            compare(result, &case["create"]);
            for step in case["steps"].as_array().unwrap() {
                let result = match step["action"].as_str().unwrap() {
                    "get" => service.get(&id),
                    "clue" => service.clue(&id),
                    "guess" => service.guess(
                        &id,
                        step["ids"]
                            .as_array()
                            .unwrap()
                            .iter()
                            .map(|id| id.as_str().unwrap().to_owned())
                            .collect(),
                    ),
                    action => panic!("unknown action {action}"),
                };
                compare(result, step);
            }
        }
    }
    #[test]
    fn concurrent_wrong_set_costs_once_and_validation_precedes_terminal() {
        let service = Arc::new(Conexiuni::new(Arc::new(Content::load().unwrap())));
        let body = service.create(Some("17"), "", "", "normal").unwrap();
        let id = body["game_id"].as_str().unwrap().to_owned();
        let groups = service
            .store
            .transaction(&id, |game| {
                game.groups.values().cloned().collect::<Vec<_>>()
            })
            .unwrap();
        let mut wrong = groups[0][..3].to_vec();
        wrong.push(groups[1][0].clone());
        let workers: Vec<_> = (0..32)
            .map(|_| {
                let service = Arc::clone(&service);
                let id = id.clone();
                let wrong = wrong.clone();
                thread::spawn(move || service.guess(&id, wrong))
            })
            .collect();
        let mut accepted = 0;
        for worker in workers {
            match worker.join().unwrap() {
                Ok(body) => {
                    accepted += 1;
                    assert_eq!(body["mistakes"], json!(1));
                    assert_eq!(body["one_away"], json!(true));
                }
                Err(failure) => assert_eq!(failure.status, 409),
            }
        }
        assert_eq!(accepted, 1);
        for group in groups {
            service.guess(&id, group).unwrap();
        }
        assert_eq!(
            service
                .guess_input(&id, || Err(ApiError::new(422, "invalid")))
                .unwrap_err()
                .status,
            422
        );
    }
    #[test]
    fn mining_rejects_insufficient_categories_and_degenerate_boards() {
        let mut data = Content::load().unwrap();
        data.category_order = vec!["muzica".to_owned()];
        let service = Conexiuni::new(Arc::new(data));
        let failure = service
            .pick_board(&mut Random::from_u64(1), "normal")
            .err()
            .unwrap();
        assert_eq!(
            failure.detail,
            json!("Nu există suficiente categorii pentru un joc.")
        );
        let bad = new_session(
            BTreeMap::from([("a".to_owned(), vec!["x".to_owned(); 4])]),
            vec!["x".to_owned()],
            "normal",
            "",
            "",
            BTreeMap::new(),
        );
        assert!(!service.quality(&bad).0);
    }
}
