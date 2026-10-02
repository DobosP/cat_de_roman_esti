//! Native anonymous Intrusul gameplay; solutions remain private until completion.

use crate::ApiError;
use crate::catalog::{Catalog, FilterOptions, daily_seed};
use crate::content::{Board, Content};
use crate::pyrandom::Random;
use crate::session::{Store, StoreError};
use num_bigint::BigInt;
use serde_json::{Value, json};
use std::collections::BTreeSet;
use std::sync::Arc;

pub const GAME_KEY: &str = "intrusul";
pub const MAX_MISTAKES: usize = 3;
pub const SOURCE_RING_LIMIT: usize = 4;

fn error(status: u16, detail: &str) -> ApiError {
    ApiError {
        status,
        detail: Value::String(detail.to_owned()),
    }
}

struct GameSession {
    members: Vec<String>,
    intruder: String,
    group_label: String,
    order: Vec<String>,
    difficulty: String,
    source_ring: Vec<String>,
    daily: String,
    category: String,
    wrong_ids: Vec<String>,
    attempts: usize,
    hint_used: bool,
    won: bool,
    lost: bool,
}

impl GameSession {
    fn finished(&self) -> bool {
        self.won || self.lost
    }

    fn score(&self) -> usize {
        if !self.won {
            return 0;
        }
        (1000usize
            .saturating_sub(200 * self.wrong_ids.len() + if self.hint_used { 150 } else { 0 }))
        .max(100)
    }
}

pub struct Intrusul {
    content: Arc<Content>,
    catalog: Catalog,
    store: Store<GameSession>,
}

impl Intrusul {
    pub fn new(content: Arc<Content>) -> Self {
        Self {
            catalog: Catalog::new(Arc::clone(&content)),
            content,
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
        if !category.is_empty() && !self.content.category_labels.contains_key(category) {
            return Err(error(400, "Categorie necunoscută."));
        }
        let mut ring = Vec::new();
        let mut rng;
        let board = if !daily.is_empty() {
            rng = Random::from_u64(daily_seed(daily, GAME_KEY));
            self.catalog.pick_daily(GAME_KEY, daily, category)
        } else {
            rng = if let Some(seed) = seed {
                let parsed: BigInt = seed
                    .parse()
                    .map_err(|_| error(422, "seed trebuie să fie un număr întreg."))?;
                Random::new(&parsed)
            } else {
                let mut entropy = [0u8; 32];
                getrandom::fill(&mut entropy)
                    .map_err(|_| error(503, "Jocul nu a putut fi creat. Încearcă din nou."))?;
                let words: Vec<u32> = entropy
                    .as_chunks::<4>()
                    .0
                    .iter()
                    .map(|part| u32::from_le_bytes(*part))
                    .collect();
                Random::from_words(&words)
            };
            if !previous.is_empty() {
                ring = self
                    .store
                    .transaction(previous, |game| game.source_ring.clone())
                    .unwrap_or_default();
            }
            let excluded: BTreeSet<String> = ring.iter().cloned().collect();
            let mut passes = vec![excluded.clone()];
            if !excluded.is_empty() {
                passes.push(BTreeSet::new());
            }
            let mut selected = None;
            for exclusions in passes {
                let mut options = FilterOptions {
                    category: category.to_owned(),
                    exclude_sources: exclusions,
                    balance_categories: starter,
                    ..Default::default()
                };
                if starter {
                    options.starter = true;
                    selected = self.catalog.pick_seeded(GAME_KEY, &mut rng, &options);
                    if selected.is_some() {
                        break;
                    }
                }
                options.starter = false;
                selected = self.catalog.pick_seeded(GAME_KEY, &mut rng, &options);
                if selected.is_some() {
                    break;
                }
            }
            selected
        };
        let board = board.ok_or_else(|| {
            error(
                503,
                "Nu există încă jocuri sigure pentru această categorie.",
            )
        })?;
        let game = build(board, &mut rng, daily, category, &ring)?;
        // The response owns its snapshot before the mutable session is published.
        let mut response = self.state("", &game);
        let id = self.store.create(game).map_err(|failure| match failure {
            StoreError::Capacity => error(503, "Prea multe jocuri active. Încearcă din nou."),
            _ => error(503, "Jocul nu a putut fi creat. Încearcă din nou."),
        })?;
        response["game_id"] = Value::String(id);
        Ok(response)
    }

    fn concept(&self, id: &str) -> Value {
        let label = self
            .content
            .labels
            .get(id)
            .map(String::as_str)
            .unwrap_or(id);
        json!({"id": id, "label": label})
    }

    fn concepts(&self, ids: &[String]) -> Value {
        Value::Array(ids.iter().map(|id| self.concept(id)).collect())
    }

    fn share(&self, game: &GameSession) -> String {
        let mut header = "cat_de_roman_esti · Intrusul".to_owned();
        if !game.category.is_empty() {
            let label = self
                .content
                .category_labels
                .get(&game.category)
                .map(String::as_str)
                .unwrap_or(&game.category);
            header.push_str(&format!(" · {label}"));
        }
        let result = if game.won { "🟩" } else { "🟥" };
        let attempt_word = if game.attempts == 1 {
            "încercare"
        } else {
            "încercări"
        };
        let mut share = format!("{header}\n{result} {} {attempt_word}", game.attempts);
        if game.hint_used {
            share.push_str(" · indiciu");
        }
        if !game.daily.is_empty() {
            share.push_str(&format!("\n{}", game.daily));
        }
        share
    }

    fn state(&self, id: &str, game: &GameSession) -> Value {
        let mut body = json!({
            "game_id": id,
            "tiles": self.concepts(&game.order),
            "wrong_ids": game.wrong_ids,
            "attempts": game.attempts,
            "mistakes": game.wrong_ids.len(),
            "remaining_mistakes": MAX_MISTAKES.saturating_sub(game.wrong_ids.len()),
            "won": game.won,
            "lost": game.lost,
            "difficulty": game.difficulty,
            "hints_used": usize::from(game.hint_used),
            "hint_available": !game.finished() && !game.wrong_ids.is_empty() && !game.hint_used,
        });
        if !game.daily.is_empty() {
            body["daily"] = json!(game.daily);
        }
        if !game.category.is_empty() {
            body["board_category"] = json!(game.category);
        }
        if game.hint_used {
            body["clue"] = json!({"label": game.group_label, "message": format!("Trei cuvinte țin de: {}.", game.group_label)});
        }
        if game.finished() {
            body["score"] = json!(game.score());
            body["share"] = json!(self.share(game));
            body["solution"] = json!({"intruder": self.concept(&game.intruder), "group": {"label": game.group_label, "tiles": self.concepts(&game.members)}});
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
            .ok_or_else(|| error(404, "Joc inexistent"))?
    }

    pub fn get(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |game| Ok(self.state(id, game)))
    }

    pub fn guess(&self, id: &str, selected: &str) -> Result<Value, ApiError> {
        self.guess_input(id, || Ok(selected.to_owned()))
    }

    /// Validate the body while pinned, after lookup and before the terminal
    /// guard. This preserves the original API's 404 / 422 / 400 precedence.
    pub fn guess_input(
        &self,
        id: &str,
        validate: impl FnOnce() -> Result<String, ApiError>,
    ) -> Result<Value, ApiError> {
        self.action(id, |game| {
            let input = validate()?;
            if game.finished() {
                return Err(error(400, "Jocul s-a terminat"));
            }
            // Python str.strip also includes the four ASCII information
            // separators, which Unicode's White_Space property omits.
            let selected = input
                .trim_matches(|c: char| c.is_whitespace() || matches!(c, '\u{001c}'..='\u{001f}'));
            if !game.order.iter().any(|id| id == selected) {
                return Err(error(400, "Concept care nu este pe tablă"));
            }
            if game.wrong_ids.iter().any(|id| id == selected) {
                let mut body = self.state(id, game);
                body["ok"] = json!(true);
                body["correct"] = json!(false);
                body["already_tried"] = json!(true);
                body["message"] = json!("Deja încercat · fără cost.");
                return Ok(body);
            }
            game.attempts += 1;
            let correct = selected == game.intruder;
            let message = if correct {
                game.won = true;
                "Exact — acesta este intrusul!"
            } else {
                game.wrong_ids.push(selected.to_owned());
                game.lost = game.wrong_ids.len() >= MAX_MISTAKES;
                if game.lost {
                    "Gata — îți arăt intrusul și legătura dintre celelalte trei."
                } else {
                    "Face parte din grup. Mai încearcă."
                }
            };
            let mut body = self.state(id, game);
            body["ok"] = json!(true);
            body["correct"] = json!(correct);
            body["already_tried"] = json!(false);
            body["message"] = json!(message);
            Ok(body)
        })
    }

    pub fn hint(&self, id: &str) -> Result<Value, ApiError> {
        self.action(id, |game| {
            if game.finished() {
                return Err(error(400, "Jocul s-a terminat"));
            }
            if game.hint_used {
                return Err(error(400, "Indiciul a fost deja folosit"));
            }
            if game.wrong_ids.is_empty() {
                return Err(error(400, "Indiciul apare după prima încercare."));
            }
            game.hint_used = true;
            let mut body = self.state(id, game);
            body["ok"] = json!(true);
            Ok(body)
        })
    }
}

fn build(
    board: &Board,
    rng: &mut Random,
    daily: &str,
    category: &str,
    previous: &[String],
) -> Result<GameSession, ApiError> {
    let invalid = || error(503, "Tabla aleasă nu mai este validă.");
    let members = board.payload["members"]
        .as_array()
        .ok_or_else(invalid)?
        .iter()
        .map(|member| member.as_str().map(str::to_owned).ok_or_else(invalid))
        .collect::<Result<Vec<_>, _>>()?;
    let intruder = board.payload["intruder"]
        .as_str()
        .filter(|id| !id.is_empty())
        .ok_or_else(invalid)?
        .to_owned();
    let group_label = board.payload["group_label"]
        .as_str()
        .filter(|label| !label.is_empty())
        .ok_or_else(invalid)?
        .to_owned();
    if members.len() != 3 {
        return Err(invalid());
    }
    let mut order = members.clone();
    order.push(intruder.clone());
    let unique: BTreeSet<_> = order.iter().collect();
    if unique.len() != 4 || order.iter().any(String::is_empty) {
        return Err(invalid());
    }
    rng.shuffle(&mut order);
    let mut source_ring: Vec<String> = previous
        .iter()
        .filter(|source| *source != &board.source_id)
        .cloned()
        .collect();
    source_ring.push(board.source_id.clone());
    if source_ring.len() > SOURCE_RING_LIMIT {
        source_ring.drain(..source_ring.len() - SOURCE_RING_LIMIT);
    }
    Ok(GameSession {
        members,
        intruder,
        group_label,
        order,
        difficulty: board.difficulty.clone(),
        source_ring,
        daily: daily.to_owned(),
        category: category.to_owned(),
        wrong_ids: Vec::new(),
        attempts: 0,
        hint_used: false,
        won: false,
        lost: false,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::sync::atomic::{AtomicU64, Ordering};
    use std::thread;
    use std::time::Duration;

    fn test_service() -> Intrusul {
        let content: Content = serde_json::from_value(json!({
            "schema_version": 1, "app_version": "test", "sources": {}, "manifest": {},
            "labels": {"a": "Țară", "b": "Școală", "c": "Carte", "d": "Intrus"},
            "category_labels": {"cultura": "Cultură", "empty": "Fără table"},
            "boards": (0..7).map(|i| json!({"game": GAME_KEY, "catalog_id": format!("catalog-{i}"), "source_id": format!("source-{i}"), "category": "cultura", "difficulty": "usor", "overall_score": 90, "starter_score": 90, "overall_rank": i+1, "starter_rank": i+1, "starter_safe": true, "payload": {"members": ["a", "b", "c"], "intruder": "d", "group_label": "Grupul privat"}})).collect::<Vec<_>>()
        })).unwrap();
        Intrusul::new(Arc::new(content))
    }

    fn create(service: &Intrusul, seed: &str) -> (String, Value) {
        let body = service.create(Some(seed), "", "", "", false).unwrap();
        (body["game_id"].as_str().unwrap().to_owned(), body)
    }

    fn assert_error(result: Result<Value, ApiError>, status: u16, detail: &str) {
        let failure = result.unwrap_err();
        assert_eq!(failure.status, status);
        assert_eq!(failure.detail, json!(detail));
    }

    fn assert_private(body: &Value) {
        let serialized = body.to_string();
        for key in [
            "solution",
            "intruder",
            "members",
            "group",
            "group_label",
            "source_id",
            "source_ring",
            "catalog_id",
            "rank",
            "standard_rank",
            "starter_rank",
            "standard_score",
            "starter_score",
            "selection_weight",
            "score",
            "share",
        ] {
            assert!(
                !serialized.contains(&format!("\"{key}\":")),
                "private key {key}"
            );
        }
        for value in ["Grupul privat", "catalog-", "source-"] {
            assert!(!serialized.contains(value));
        }
    }

    #[test]
    fn initial_state_is_private_seeded_and_returns_owned_snapshots() {
        let service = test_service();
        let (id, first) = create(&service, "17");
        let (_, second) = create(&service, "17");
        assert_eq!(first["tiles"], second["tiles"]);
        assert_eq!(first, service.get(&id).unwrap());
        assert_private(&first);
        for key in ["attempts", "mistakes", "hints_used"] {
            assert_eq!(first[key], json!(0));
        }
        assert_eq!(first["remaining_mistakes"], json!(3));
        assert_eq!(first["wrong_ids"], json!([]));
        assert!(first.get("board_category").is_none());
        assert_eq!(first["hint_available"], json!(false));
    }

    #[test]
    fn unseeded_anonymous_play_uses_os_entropy_and_unique_sessions() {
        let service = test_service();
        let first = service.create(None, "", "", "", false).unwrap();
        let second = service.create(None, "", "", "", false).unwrap();
        assert_ne!(first["game_id"], second["game_id"]);
        assert_eq!(first["tiles"].as_array().unwrap().len(), 4);
        assert_private(&first);
        assert_eq!(
            service
                .guess(first["game_id"].as_str().unwrap(), "d")
                .unwrap()["score"],
            json!(1000)
        );
    }

    #[test]
    fn wrong_repeat_hint_and_scored_win_match_existing_gameplay() {
        let service = test_service();
        let (id, _) = create(&service, "17");
        assert_error(
            service.hint(&id),
            400,
            "Indiciul apare după prima încercare.",
        );
        let mut wrong = service.guess(&id, "\u{001c} a \u{001f}").unwrap();
        assert_eq!(wrong["correct"], json!(false));
        assert_eq!(wrong["already_tried"], json!(false));
        assert_eq!(wrong["attempts"], json!(1));
        assert_eq!(wrong["hint_available"], json!(true));
        assert_private(&wrong);
        wrong["wrong_ids"][0] = json!("tampered");
        wrong["tiles"][0]["label"] = json!("tampered");
        let repeated = service.guess(&id, "a").unwrap();
        assert_eq!(repeated["already_tried"], json!(true));
        assert_eq!(repeated["attempts"], json!(1));
        assert_eq!(repeated["wrong_ids"], json!(["a"]));
        let hinted = service.hint(&id).unwrap();
        assert_eq!(hinted["hints_used"], json!(1));
        assert_eq!(hinted["hint_available"], json!(false));
        assert_eq!(
            hinted["clue"]["message"],
            json!("Trei cuvinte țin de: Grupul privat.")
        );
        assert!(hinted.get("solution").is_none());
        assert_error(service.hint(&id), 400, "Indiciul a fost deja folosit");
        let won = service.guess(&id, "d").unwrap();
        assert_eq!(won["attempts"], json!(2));
        assert_eq!(won["score"], json!(650));
        assert_eq!(
            won["share"],
            json!("cat_de_roman_esti · Intrusul\n🟩 2 încercări · indiciu")
        );
        assert_eq!(won["solution"]["intruder"]["id"], json!("d"));
        assert_eq!(won["solution"]["group"]["label"], json!("Grupul privat"));
        assert_error(service.guess(&id, "d"), 400, "Jocul s-a terminat");
        assert_error(service.hint(&id), 400, "Jocul s-a terminat");
    }

    #[test]
    fn first_try_and_third_wrong_scores_and_terminal_guards() {
        let service = test_service();
        let (id, _) = create(&service, "51");
        let won = service.guess(&id, "d").unwrap();
        assert_eq!(won["score"], json!(1000));
        assert_eq!(
            won["share"],
            json!("cat_de_roman_esti · Intrusul\n🟩 1 încercare")
        );
        let (lost_id, _) = create(&service, "52");
        for (index, wrong) in ["a", "b", "c"].into_iter().enumerate() {
            let body = service.guess(&lost_id, wrong).unwrap();
            assert_eq!(body["lost"], json!(index == 2));
            assert_eq!(body["mistakes"], json!(index + 1));
            if index == 2 {
                assert_eq!(body["score"], json!(0));
                assert_eq!(body["remaining_mistakes"], json!(0));
                assert_eq!(
                    body["share"],
                    json!("cat_de_roman_esti · Intrusul\n🟥 3 încercări")
                );
            }
        }
    }

    #[test]
    fn daily_ignores_rotation_seed_and_starter_and_preserves_themed_share() {
        let service = test_service();
        let (previous, _) = create(&service, "31");
        let first = service
            .create(Some("1"), "2026-10-01", "cultura", "", false)
            .unwrap();
        let second = service
            .create(Some("999"), "2026-10-01", "cultura", &previous, true)
            .unwrap();
        assert_eq!(first["tiles"], second["tiles"]);
        assert_eq!(first["daily"], json!("2026-10-01"));
        assert_eq!(first["board_category"], json!("cultura"));
        let id = second["game_id"].as_str().unwrap();
        service
            .store
            .transaction(id, |game| assert_eq!(game.source_ring.len(), 1));
        let won = service.guess(id, "d").unwrap();
        assert_eq!(
            won["share"],
            json!("cat_de_roman_esti · Intrusul · Cultură\n🟩 1 încercare\n2026-10-01")
        );
    }

    #[test]
    fn source_ring_is_distinct_bounded_and_forced_repeat_moves_to_tail() {
        let service = test_service();
        let mut previous = String::new();
        let mut seen = Vec::new();
        for _ in 0..12 {
            let body = service
                .create(Some("31"), "", "", &previous, false)
                .unwrap();
            previous = body["game_id"].as_str().unwrap().to_owned();
            service.store.transaction(&previous, |game| {
                let source_id = game.source_ring.last().unwrap().clone();
                assert!(!seen.contains(&source_id));
                seen.push(source_id);
                if seen.len() > SOURCE_RING_LIMIT {
                    seen.remove(0);
                }
                assert_eq!(game.source_ring, seen);
            });
        }
        let board = &service.content.boards[0];
        let ring = vec![
            "source-a".to_owned(),
            board.source_id.clone(),
            "source-c".to_owned(),
            "source-d".to_owned(),
        ];
        let forced = build(board, &mut Random::from_u64(1), "", "", &ring).unwrap();
        assert_eq!(
            forced.source_ring,
            vec!["source-a", "source-c", "source-d", &board.source_id]
        );
        let absent = service
            .create(Some("31"), "", "", "expired-id", false)
            .unwrap();
        service
            .store
            .transaction(absent["game_id"].as_str().unwrap(), |game| {
                assert_eq!(game.source_ring.len(), 1)
            });
    }

    #[test]
    fn selection_and_action_errors_are_stable_and_starter_can_widen() {
        let mut service = test_service();
        let mut content = (*service.content).clone();
        for board in &mut content.boards {
            board.starter_safe = false;
        }
        service = Intrusul::new(Arc::new(content));
        assert!(service.create(Some("7"), "", "", "", true).is_ok());
        assert_error(
            service.create(Some("1"), "", "missing", "", false),
            400,
            "Categorie necunoscută.",
        );
        assert_error(
            service.create(Some("1"), "", "empty", "", false),
            503,
            "Nu există încă jocuri sigure pentru această categorie.",
        );
        let (id, _) = create(&service, "1");
        assert_error(
            service.guess(&id, "not-on-board"),
            400,
            "Concept care nu este pe tablă",
        );
        assert_error(service.get("missing"), 404, "Joc inexistent");
        assert_error(service.guess("missing", "a"), 404, "Joc inexistent");
        assert_error(service.hint("missing"), 404, "Joc inexistent");
    }

    #[test]
    fn concurrent_duplicate_wrong_hint_and_win_charge_once() {
        let service = Arc::new(test_service());
        let (id, _) = create(&service, "61");
        let wrong_workers: Vec<_> = (0..32)
            .map(|_| {
                let service = Arc::clone(&service);
                let id = id.clone();
                thread::spawn(move || service.guess(&id, "a").unwrap())
            })
            .collect();
        let wrongs: Vec<_> = wrong_workers
            .into_iter()
            .map(|worker| worker.join().unwrap())
            .collect();
        assert_eq!(
            wrongs
                .iter()
                .filter(|body| body["already_tried"] == json!(false))
                .count(),
            1
        );
        for body in wrongs {
            assert_eq!(body["attempts"], json!(1));
            assert_eq!(body["mistakes"], json!(1));
        }
        let hint_workers: Vec<_> = (0..32)
            .map(|_| {
                let service = Arc::clone(&service);
                let id = id.clone();
                thread::spawn(move || service.hint(&id))
            })
            .collect();
        assert_eq!(
            hint_workers
                .into_iter()
                .map(|worker| worker.join().unwrap())
                .filter(Result::is_ok)
                .count(),
            1
        );
        let win_workers: Vec<_> = (0..32)
            .map(|_| {
                let service = Arc::clone(&service);
                let id = id.clone();
                thread::spawn(move || service.guess(&id, "d"))
            })
            .collect();
        let wins: Vec<_> = win_workers
            .into_iter()
            .map(|worker| worker.join().unwrap())
            .filter_map(Result::ok)
            .collect();
        assert_eq!(wins.len(), 1);
        assert_eq!(wins[0]["score"], json!(650));
    }

    #[test]
    fn validation_is_pinned_and_missing_validation_terminal_precedence_matches() {
        let mut service = test_service();
        service.store = Store::with_options(
            Some(Duration::from_secs(7200)),
            Some(1),
            Arc::new(|| Duration::ZERO),
        )
        .unwrap();
        let (id, _) = create(&service, "1");
        let detail = json!([{"loc": ["id"], "msg": "Field required"}]);
        let validation = || -> Result<String, ApiError> {
            assert!(!service.store.delete(&id));
            assert_error(
                service.create(Some("2"), "", "", "", false),
                503,
                "Prea multe jocuri active. Încearcă din nou.",
            );
            Err(ApiError {
                status: 422,
                detail: detail.clone(),
            })
        };
        let failure = service.guess_input(&id, validation).unwrap_err();
        assert_eq!(failure.status, 422);
        assert_eq!(failure.detail, detail);
        assert_eq!(service.get(&id).unwrap()["attempts"], json!(0));
        service.guess(&id, "d").unwrap();
        assert_eq!(
            service.guess_input(&id, validation).unwrap_err().status,
            422
        );
        assert_error(
            service.guess_input("missing", || panic!("validator called for missing session")),
            404,
            "Joc inexistent",
        );
    }

    #[test]
    fn ttl_expiry_is_a_missing_session_and_malformed_boards_fail_closed() {
        let mut service = test_service();
        let clock = Arc::new(AtomicU64::new(0));
        let clock_now = Arc::clone(&clock);
        service.store = Store::with_options(
            Some(Duration::from_secs(1)),
            Some(1),
            Arc::new(move || Duration::from_secs(clock_now.load(Ordering::SeqCst))),
        )
        .unwrap();
        let (id, _) = create(&service, "1");
        clock.store(2, Ordering::SeqCst);
        assert_error(service.get(&id), 404, "Joc inexistent");
        let mut board = service.content.boards[0].clone();
        for payload in [
            json!({"members": ["a", "b"], "intruder": "d", "group_label": "x"}),
            json!({"members": ["a", "b", "c"], "intruder": "a", "group_label": "x"}),
        ] {
            board.payload = payload;
            let failure = build(&board, &mut Random::from_u64(1), "", "", &[])
                .err()
                .unwrap();
            assert_eq!(failure.status, 503);
            assert_eq!(failure.detail, json!("Tabla aleasă nu mai este validă."));
        }
    }
}
