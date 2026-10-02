//! Four hidden reviewed pairs; there is deliberately no mined fallback.
use crate::ApiError;
use crate::catalog::{Catalog, FilterOptions, daily_seed};
use crate::content::{Board, Content};
use crate::pyrandom::Random;
use crate::session::{Store, StoreError};
use num_bigint::BigInt;
use serde_json::{Value, json};
use std::collections::BTreeSet;
use std::sync::Arc;

struct Pair {
    members: Vec<String>,
    label: String,
}

struct GameSession {
    pairs: Vec<Pair>,
    order: Vec<String>,
    solved: Vec<usize>,
    wrong_history: Vec<Vec<String>>,
    mistakes: usize,
    hinted: Option<usize>,
    hints_used: usize,
    won: bool,
    lost: bool,
    daily: String,
    category: String,
    source_ring: Vec<String>,
}
pub struct Perechi {
    data: Arc<Content>,
    catalog: Catalog,
    store: Store<GameSession>,
}
fn fail(status: u16, detail: &str) -> ApiError {
    ApiError::new(status, detail)
}
fn rng(seed: Option<&str>) -> Result<Random, ApiError> {
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
fn build(
    board: &Board,
    random: &mut Random,
    daily: &str,
    category: &str,
    previous: &[String],
) -> Result<GameSession, ApiError> {
    let invalid = || fail(503, "Catalogul Perechi este invalid.");
    let rows = board.payload["pairs"]
        .as_array()
        .filter(|rows| rows.len() == 4)
        .ok_or_else(invalid)?;
    let mut pairs = Vec::new();
    let mut order = Vec::new();
    let mut unique = BTreeSet::new();
    for row in rows {
        let object = row
            .as_object()
            .filter(|row| {
                row.len() == 2 && row.contains_key("members") && row.contains_key("group_label")
            })
            .ok_or_else(invalid)?;
        let values = object["members"]
            .as_array()
            .filter(|values| values.len() == 2)
            .ok_or_else(invalid)?;
        let members = values
            .iter()
            .map(|id| id.as_str().map(str::to_owned).ok_or_else(invalid))
            .collect::<Result<Vec<_>, _>>()?;
        let label = object["group_label"]
            .as_str()
            .ok_or_else(invalid)?
            .to_owned();
        for id in &members {
            if !unique.insert(id.clone()) {
                return Err(invalid());
            }
            order.push(id.clone());
        }
        pairs.push(Pair { members, label });
    }
    random.shuffle(&mut order);
    let mut source_ring: Vec<String> = previous
        .iter()
        .filter(|source| *source != &board.source_id)
        .cloned()
        .collect();
    source_ring.push(board.source_id.clone());
    if source_ring.len() > 4 {
        source_ring.drain(..source_ring.len() - 4);
    }
    Ok(GameSession {
        pairs,
        order,
        solved: Vec::new(),
        wrong_history: Vec::new(),
        mistakes: 0,
        hinted: None,
        hints_used: 0,
        won: false,
        lost: false,
        daily: daily.to_owned(),
        category: category.to_owned(),
        source_ring,
    })
}
impl Perechi {
    pub fn new(data: Arc<Content>) -> Self {
        Self {
            catalog: Catalog::new(Arc::clone(&data)),
            data,
            store: Store::new(),
        }
    }
    pub fn create(
        &self,
        seed: Option<&str>,
        daily: &str,
        category: &str,
        previous: &str,
        starter: bool,
    ) -> Result<Value, ApiError> {
        if !category.is_empty() && !self.data.category_labels.contains_key(category) {
            return Err(fail(400, "Categorie necunoscută."));
        }
        let mut random;
        let mut ring = Vec::new();
        let board = if !daily.is_empty() {
            random = Random::from_u64(daily_seed(daily, "perechi"));
            self.catalog.pick_daily("perechi", daily, category)
        } else {
            random = rng(seed)?;
            if !previous.is_empty() {
                ring = self
                    .store
                    .transaction(previous, |game| game.source_ring.clone())
                    .unwrap_or_default();
            }
            let exclusions: BTreeSet<String> = ring.iter().cloned().collect();
            let mut passes = vec![exclusions.clone()];
            if !exclusions.is_empty() {
                passes.push(BTreeSet::new())
            }
            let profiles = if starter {
                vec![true, false]
            } else {
                vec![false]
            };
            let mut selected = None;
            for excluded in passes {
                for profile in &profiles {
                    selected = self.catalog.pick_seeded(
                        "perechi",
                        &mut random,
                        &FilterOptions {
                            category: category.to_owned(),
                            exclude_sources: excluded.clone(),
                            starter: *profile,
                            balance_categories: starter,
                            ..Default::default()
                        },
                    );
                    if selected.is_some() {
                        break;
                    }
                }
                if selected.is_some() {
                    break;
                }
            }
            selected
        }
        .ok_or_else(|| fail(503, "Nu există jocuri Perechi pentru filtrul ales."))?;
        let game = build(board, &mut random, daily, category, &ring)?;
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
    fn pair(&self, pair: &Pair) -> Value {
        json!({"tiles":pair.members.iter().map(|id|self.concept(id)).collect::<Vec<_>>(),"label":pair.label})
    }
    fn state(&self, id: &str, game: &GameSession) -> Value {
        let tiles:Vec<Value>=game.order.iter().map(|id|json!({"id":id,"label":self.data.labels.get(id).map(String::as_str).unwrap_or(id),"solved":game.solved.iter().any(|index|game.pairs[*index].members.contains(id))})).collect();
        let mut body = json!({"game_id":id,"tiles":tiles,"solved_pairs":game.solved.iter().map(|index|self.pair(&game.pairs[*index])).collect::<Vec<_>>(),"solved_count":game.solved.len(),"remaining_pairs":4-game.solved.len(),"mistakes":game.mistakes,"remaining_mistakes":6-game.mistakes,"actions":game.solved.len()+game.wrong_history.len(),"hint_available":!game.won&&!game.lost&&game.hints_used<1&&game.mistakes>=2&&game.solved.len()<4,"hints_used":game.hints_used,"won":game.won,"lost":game.lost});
        if let Some(index) = game.hinted {
            body["hint"] = self.pair(&game.pairs[index]);
        }
        if !game.daily.is_empty() {
            body["daily"] = json!(game.daily);
        }
        if !game.category.is_empty() {
            body["board_category"] = json!(game.category);
        }
        if game.won || game.lost {
            body["score"] = json!(if game.lost {
                0
            } else {
                1000usize
                    .saturating_sub(100 * game.mistakes + 150 * game.hints_used)
                    .max(100)
            });
            let word = if game.mistakes == 1 {
                "greșeală"
            } else {
                "greșeli"
            };
            let mut header = format!("cat_de_roman_esti · Perechi · {} {word}", game.mistakes);
            if game.hints_used > 0 {
                header.push_str(" · indiciu")
            }
            if !game.daily.is_empty() {
                header.push_str(&format!(" · {}", game.daily))
            }
            body["share"] = json!(format!(
                "{header}\n{}{}",
                "🟩".repeat(game.solved.len()),
                "⬜".repeat(4 - game.solved.len())
            ));
            body["solution"] = json!(
                game.pairs
                    .iter()
                    .map(|pair| self.pair(pair))
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
    pub fn match_pair(&self, id: &str, ids: Vec<String>) -> Result<Value, ApiError> {
        self.match_input(id, || Ok(ids))
    }
    pub fn match_input(
        &self,
        id: &str,
        validate: impl FnOnce() -> Result<Vec<String>, ApiError>,
    ) -> Result<Value, ApiError> {
        self.action(id, |game| {
            if game.won || game.lost {
                return Err(fail(400, "Jocul s-a terminat"));
            }
            let ids = validate()?;
            if ids.len() != 2 || ids[0] == ids[1] {
                return Err(fail(400, "Alege exact două concepte distincte"));
            }
            if ids.iter().any(|id| !game.order.contains(id)) {
                return Err(fail(400, "Concept care nu e pe tablă"));
            }
            if ids.iter().any(|id| {
                game.solved
                    .iter()
                    .any(|index| game.pairs[*index].members.contains(id))
            }) {
                return Err(fail(400, "Concept deja rezolvat"));
            }
            if let Some(index) = game
                .pairs
                .iter()
                .position(|pair| ids.iter().all(|id| pair.members.contains(id)))
            {
                game.solved.push(index);
                game.won = game.solved.len() == 4;
                let mut body = self.state(id, game);
                body["ok"] = json!(true);
                body["correct"] = json!(true);
                body["pair"] = self.pair(&game.pairs[index]);
                return Ok(body);
            }
            let mut key = ids;
            key.sort();
            let repeated = game.wrong_history.contains(&key);
            if !repeated {
                game.wrong_history.push(key);
                game.mistakes += 1;
                game.lost = game.mistakes >= 6;
            }
            let mut body = self.state(id, game);
            body["ok"] = json!(true);
            body["correct"] = json!(false);
            body["repeated"] = json!(repeated);
            Ok(body)
        })
    }
    pub fn hint(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |game| {
            if game.won || game.lost {
                return Err(fail(400, "Jocul s-a terminat"));
            }
            if game.hints_used >= 1 {
                return Err(fail(400, "Indiciul a fost deja folosit"));
            }
            if game.mistakes < 2 {
                return Err(fail(400, "Indiciul se deschide după două greșeli."));
            }
            game.hinted = (0..4).find(|index| !game.solved.contains(index));
            game.hints_used += 1;
            let mut body = self.state(id, game);
            body["ok"] = json!(true);
            Ok(body)
        })
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::thread;

    fn compare(result: Result<Value, ApiError>, expected: &Value) {
        let (status, mut body) = match result {
            Ok(body) => (200, body),
            Err(error) => (error.status, json!({"detail": error.detail})),
        };
        if status == 200 {
            body["game_id"] = json!("<session>");
        }
        assert_eq!(json!(status), expected["status"]);
        assert_eq!(body, expected["body"]);
    }

    #[test]
    fn python_api_goldens_cover_pairs_hints_losses_daily_and_rotation() {
        let vectors: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/perechi/testdata/python-goldens.json"
        ))
        .unwrap();
        let service = Perechi::new(Arc::new(Content::load().unwrap()));
        let mut identifiers = BTreeMap::new();
        for (index, case) in vectors["cases"].as_array().unwrap().iter().enumerate() {
            let previous = case["previous_case"].as_i64().unwrap();
            let previous = if previous >= 0 {
                identifiers
                    .get(&(previous as usize))
                    .map(String::as_str)
                    .unwrap()
            } else {
                ""
            };
            let result = service.create(
                case["seed"].as_str(),
                case["daily"].as_str().unwrap(),
                case["category"].as_str().unwrap(),
                previous,
                case["starter"].as_bool().unwrap(),
            );
            let id = result
                .as_ref()
                .ok()
                .map(|body| body["game_id"].as_str().unwrap().to_owned())
                .unwrap_or_default();
            identifiers.insert(index, id.clone());
            compare(result, &case["create"]);
            for step in case["steps"].as_array().unwrap() {
                let result = match step["action"].as_str().unwrap() {
                    "get" => service.get(&id),
                    "hint" => service.hint(&id),
                    "match" => service.match_pair(
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
    fn concurrent_duplicates_charge_once_and_terminal_precedes_validation() {
        let service = Arc::new(Perechi::new(Arc::new(Content::load().unwrap())));
        let created = service.create(Some("17"), "", "", "", false).unwrap();
        let id = created["game_id"].as_str().unwrap().to_owned();
        let pairs = service
            .store
            .transaction(&id, |game| {
                game.pairs
                    .iter()
                    .map(|pair| pair.members.clone())
                    .collect::<Vec<_>>()
            })
            .unwrap();
        let wrong = vec![pairs[0][0].clone(), pairs[1][0].clone()];
        let workers: Vec<_> = (0..32)
            .map(|_| {
                let service = Arc::clone(&service);
                let id = id.clone();
                let wrong = wrong.clone();
                thread::spawn(move || service.match_pair(&id, wrong).unwrap())
            })
            .collect();
        let results: Vec<_> = workers
            .into_iter()
            .map(|worker| worker.join().unwrap())
            .collect();
        assert_eq!(
            results
                .iter()
                .filter(|body| body["repeated"] == json!(false))
                .count(),
            1
        );
        for pair in pairs {
            service.match_pair(&id, pair).unwrap();
        }
        let failure = service
            .match_input(&id, || panic!("terminal match validated body"))
            .unwrap_err();
        assert_eq!(failure.status, 400);
        assert_eq!(
            service
                .match_input("missing", || panic!("missing match validated body"))
                .unwrap_err()
                .status,
            404
        );
    }
}
