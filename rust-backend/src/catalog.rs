//! Ranked, deterministic selection over the reviewed private board inventory.
//! Catalog IDs, source IDs, rankings and answer payloads stay server-side.

use crate::content::{Board, Content};
use crate::pyrandom::Random;
use std::collections::{BTreeMap, BTreeSet};
use std::sync::Arc;

#[derive(Default, Clone)]
pub struct FilterOptions {
    pub category: String,
    pub difficulty: String,
    pub exclude_sources: BTreeSet<String>,
    pub starter: bool,
    pub balance_categories: bool,
}

pub type PickOptions = FilterOptions;

pub struct Catalog {
    content: Arc<Content>,
    order: Vec<usize>,
}

struct BoardGroup<'a> {
    key: &'a str,
    boards: Vec<&'a Board>,
}

impl Catalog {
    /// Content is validated by the Python exporter and the pinned Rust loader.
    pub fn new(content: Arc<Content>) -> Self {
        let mut order: Vec<usize> = (0..content.boards.len()).collect();
        order.sort_by(|left, right| {
            content.boards[*left]
                .catalog_id
                .cmp(&content.boards[*right].catalog_id)
        });
        Self { content, order }
    }

    pub fn pool(&self, game: &str, options: &FilterOptions) -> Vec<&Board> {
        self.order
            .iter()
            .map(|index| &self.content.boards[*index])
            .filter(|board| {
                board.game == game
                    && (options.category.is_empty() || board.category == options.category)
                    && (options.difficulty.is_empty() || board.difficulty == options.difficulty)
                    && !options.exclude_sources.contains(&board.source_id)
                    && (!options.starter || board.starter_safe)
            })
            .collect()
    }

    /// Sources are weighted before variants. Optional category balancing first
    /// averages each source, so prolific sources do not inflate category weight.
    /// No strict filter is widened when it yields an empty pool.
    pub fn pick_seeded(
        &self,
        game: &str,
        rng: &mut Random,
        options: &FilterOptions,
    ) -> Option<&Board> {
        let mut pool = preferred_shelf(self.pool(game, options));
        if pool.is_empty() {
            return None;
        }
        if options.balance_categories && options.category.is_empty() {
            let categories = groups(&pool, true);
            let selected = weighted_index(&group_weights(&categories, options.starter, true), rng);
            pool = categories[selected].boards.clone();
        }
        let sources = groups(&pool, false);
        let selected = weighted_index(&group_weights(&sources, options.starter, false), rng);
        let candidates = &sources[selected].boards;
        Some(candidates[weighted_index(&candidate_weights(candidates, options.starter), rng)])
    }

    pub fn pick_daily(&self, game: &str, daily: &str, category: &str) -> Option<&Board> {
        self.pick_daily_with_options(
            game,
            daily,
            &FilterOptions {
                category: category.to_owned(),
                ..Default::default()
            },
        )
    }

    /// Daily takes only category and difficulty into account. Starter flags and
    /// previous-session exclusions cannot fork the shared daily board.
    pub fn pick_daily_with_options(
        &self,
        game: &str,
        daily: &str,
        options: &FilterOptions,
    ) -> Option<&Board> {
        let strict = FilterOptions {
            category: options.category.clone(),
            difficulty: options.difficulty.clone(),
            ..Default::default()
        };
        let pool = preferred_shelf(self.pool(game, &strict));
        let sources = groups(&pool, false);
        if sources.is_empty() {
            return None;
        }
        let base = format!(
            "{daily}:{game}:{}:{}:",
            options.category, options.difficulty
        );
        let keys: Vec<String> = sources
            .iter()
            .map(|source| format!("{base}{}", source.key))
            .collect();
        let selected = rendezvous_index(&keys, &group_weights(&sources, false, false), "source");
        let source = &sources[selected];
        let keys: Vec<String> = source
            .boards
            .iter()
            .map(|board| format!("{base}{}:{}", source.key, board.catalog_id))
            .collect();
        Some(
            source.boards[rendezvous_index(
                &keys,
                &candidate_weights(&source.boards, false),
                "candidate",
            )],
        )
    }
}

pub fn score_band_weight(score: i32) -> usize {
    match score {
        85.. => 5,
        75.. => 4,
        65.. => 3,
        55.. => 2,
        _ => 1,
    }
}

fn preferred_shelf(pool: Vec<&Board>) -> Vec<&Board> {
    let preferred: Vec<&Board> = pool
        .iter()
        .copied()
        .filter(|board| board.overall_score >= 55)
        .collect();
    if preferred.is_empty() {
        pool
    } else {
        preferred
    }
}

fn groups<'a>(pool: &[&'a Board], category: bool) -> Vec<BoardGroup<'a>> {
    let mut grouped: BTreeMap<&'a str, Vec<&'a Board>> = BTreeMap::new();
    for board in pool {
        let key = if category {
            board.category.as_str()
        } else {
            board.source_id.as_str()
        };
        grouped.entry(key).or_default().push(board);
    }
    grouped
        .into_iter()
        .map(|(key, boards)| BoardGroup { key, boards })
        .collect()
}

fn board_score(board: &Board, starter: bool) -> i32 {
    if starter {
        board.starter_score
    } else {
        board.overall_score
    }
}

fn source_average(boards: &[&Board], starter: bool) -> i32 {
    let total: i64 = boards
        .iter()
        .map(|board| i64::from(board_score(board, starter)))
        .sum();
    ((total + boards.len() as i64 / 2) / boards.len() as i64) as i32
}

fn category_average(boards: &[&Board], starter: bool) -> i32 {
    let sources = groups(boards, false);
    let total: i64 = sources
        .iter()
        .map(|source| i64::from(source_average(&source.boards, starter)))
        .sum();
    ((total + sources.len() as i64 / 2) / sources.len() as i64) as i32
}

fn weighted_index(weights: &[usize], rng: &mut Random) -> usize {
    let mut ticket = rng.randbelow(weights.iter().sum());
    for (index, weight) in weights.iter().enumerate() {
        if ticket < *weight {
            return index;
        }
        ticket -= weight;
    }
    unreachable!("catalog: weighted selection exhausted its ticket range")
}

fn group_weights(grouped: &[BoardGroup<'_>], starter: bool, category: bool) -> Vec<usize> {
    grouped
        .iter()
        .map(|group| {
            score_band_weight(if category {
                category_average(&group.boards, starter)
            } else {
                source_average(&group.boards, starter)
            })
        })
        .collect()
}

fn candidate_weights(boards: &[&Board], starter: bool) -> Vec<usize> {
    boards
        .iter()
        .map(|board| score_band_weight(board_score(board, starter)))
        .collect()
}

fn rendezvous_index(keys: &[String], weights: &[usize], namespace: &str) -> usize {
    assert_eq!(keys.len(), weights.len());
    let mut best: Option<([u8; 8], &str, usize)> = None;
    for (index, (base, weight)) in keys.iter().zip(weights).enumerate() {
        let mut rank = blake2b8(base.as_bytes());
        for ticket in 1..*weight {
            let versioned = format!("{base}:v38:{namespace}:{ticket}");
            rank = rank.min(blake2b8(versioned.as_bytes()));
        }
        if best
            .as_ref()
            .is_none_or(|(old_rank, old_key, _)| (rank, base.as_str()) < (*old_rank, *old_key))
        {
            best = Some((rank, base, index));
        }
    }
    best.expect("catalog: empty rendezvous").2
}

/// Python `daily_seed`: unkeyed BLAKE2b with digest_size=8, interpreted big-endian.
/// Truncating a BLAKE2b-512 digest is not equivalent to this parameterization.
pub fn daily_seed(date: &str, salt: &str) -> u64 {
    u64::from_be_bytes(blake2b8(format!("{date}:{salt}").as_bytes()))
}

const BLAKE_IV: [u64; 8] = [
    0x6a09_e667_f3bc_c908,
    0xbb67_ae85_84ca_a73b,
    0x3c6e_f372_fe94_f82b,
    0xa54f_f53a_5f1d_36f1,
    0x510e_527f_ade6_82d1,
    0x9b05_688c_2b3e_6c1f,
    0x1f83_d9ab_fb41_bd6b,
    0x5be0_cd19_137e_2179,
];

const BLAKE_SIGMA: [[usize; 16]; 12] = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
    [11, 8, 12, 0, 5, 2, 15, 13, 10, 14, 3, 6, 7, 1, 9, 4],
    [7, 9, 3, 1, 13, 12, 11, 14, 2, 6, 5, 10, 4, 0, 15, 8],
    [9, 0, 5, 7, 2, 4, 10, 15, 14, 1, 11, 12, 6, 8, 3, 13],
    [2, 12, 6, 10, 0, 11, 8, 3, 4, 13, 7, 5, 15, 14, 1, 9],
    [12, 5, 1, 15, 14, 13, 4, 10, 0, 7, 6, 3, 9, 2, 8, 11],
    [13, 11, 7, 14, 12, 1, 3, 9, 5, 0, 15, 4, 8, 6, 2, 10],
    [6, 15, 14, 9, 11, 3, 0, 8, 12, 2, 13, 7, 1, 4, 10, 5],
    [10, 2, 8, 4, 7, 6, 1, 5, 15, 11, 9, 14, 3, 12, 13, 0],
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
    [14, 10, 4, 8, 9, 15, 13, 6, 1, 12, 0, 2, 11, 7, 5, 3],
];

fn blake_mix(v: &mut [u64; 16], a: usize, b: usize, c: usize, d: usize, x: u64, y: u64) {
    v[a] = v[a].wrapping_add(v[b]).wrapping_add(x);
    v[d] = (v[d] ^ v[a]).rotate_right(32);
    v[c] = v[c].wrapping_add(v[d]);
    v[b] = (v[b] ^ v[c]).rotate_right(24);
    v[a] = v[a].wrapping_add(v[b]).wrapping_add(y);
    v[d] = (v[d] ^ v[a]).rotate_right(16);
    v[c] = v[c].wrapping_add(v[d]);
    v[b] = (v[b] ^ v[c]).rotate_right(63);
}

fn blake_compress(h: &mut [u64; 8], block: &[u8; 128], total: u64, final_block: bool) {
    let mut words = [0; 16];
    let mut v = [0; 16];
    for (word, chunk) in words.iter_mut().zip(block.as_chunks::<8>().0) {
        *word = u64::from_le_bytes(*chunk);
    }
    v[..8].copy_from_slice(h);
    v[8..].copy_from_slice(&BLAKE_IV);
    v[12] ^= total;
    if final_block {
        v[14] = !v[14];
    }
    for s in BLAKE_SIGMA {
        blake_mix(&mut v, 0, 4, 8, 12, words[s[0]], words[s[1]]);
        blake_mix(&mut v, 1, 5, 9, 13, words[s[2]], words[s[3]]);
        blake_mix(&mut v, 2, 6, 10, 14, words[s[4]], words[s[5]]);
        blake_mix(&mut v, 3, 7, 11, 15, words[s[6]], words[s[7]]);
        blake_mix(&mut v, 0, 5, 10, 15, words[s[8]], words[s[9]]);
        blake_mix(&mut v, 1, 6, 11, 12, words[s[10]], words[s[11]]);
        blake_mix(&mut v, 2, 7, 8, 13, words[s[12]], words[s[13]]);
        blake_mix(&mut v, 3, 4, 9, 14, words[s[14]], words[s[15]]);
    }
    for i in 0..8 {
        h[i] ^= v[i] ^ v[i + 8];
    }
}

// Fixed-output unkeyed sequential BLAKE2b-64 follows RFC 7693, without unsafe
// code or additional dependencies. It is private puzzle-selection machinery.
pub fn blake2b8(mut input: &[u8]) -> [u8; 8] {
    let mut h = BLAKE_IV;
    h[0] ^= 0x0101_0008;
    let mut total = 0u64;
    while input.len() > 128 {
        let block: &[u8; 128] = input[..128].try_into().expect("full BLAKE2b block");
        total += 128;
        blake_compress(&mut h, block, total, false);
        input = &input[128..];
    }
    let mut block = [0; 128];
    block[..input.len()].copy_from_slice(input);
    total += input.len() as u64;
    blake_compress(&mut h, &block, total, true);
    h[0].to_le_bytes()
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::{Value, json};

    fn bundled_content() -> Content {
        serde_json::from_str(include_str!(
            "../../go-backend/internal/content/bundled.json"
        ))
        .unwrap()
    }

    fn synthetic_content() -> Content {
        let mut base: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/content/bundled.json"
        ))
        .unwrap();
        let mut boards: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/catalog/testdata/synthetic_boards.json"
        ))
        .unwrap();
        for board in boards.as_array_mut().unwrap() {
            board["overall_rank"] = json!(1);
            board["starter_rank"] = if board["starter_safe"] == true {
                json!(1)
            } else {
                Value::Null
            };
            board["payload"] = json!({});
        }
        base["boards"] = boards;
        serde_json::from_value(base).unwrap()
    }

    fn options(value: &Value) -> FilterOptions {
        FilterOptions {
            category: value["category"].as_str().unwrap_or("").to_owned(),
            difficulty: value["difficulty"].as_str().unwrap_or("").to_owned(),
            exclude_sources: value["exclude_source_ids"]
                .as_array()
                .map(|items| {
                    items
                        .iter()
                        .map(|item| item.as_str().unwrap().to_owned())
                        .collect()
                })
                .unwrap_or_default(),
            starter: value["starter"].as_bool().unwrap_or(false),
            balance_categories: value["balance_categories"].as_bool().unwrap_or(false),
        }
    }

    fn board_id(board: Option<&Board>) -> &str {
        board.map_or("", |board| board.catalog_id.as_str())
    }

    #[test]
    fn canonical_python_selection_and_following_rng_state() {
        let bundled = Catalog::new(Arc::new(bundled_content()));
        let synthetic = Catalog::new(Arc::new(synthetic_content()));
        let golden: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/catalog/testdata/python_selector.json"
        ))
        .unwrap();
        for (index, vector) in golden["seeded"].as_array().unwrap().iter().enumerate() {
            let catalog = if vector["inventory"] == "bundled" {
                &bundled
            } else {
                &synthetic
            };
            let mut rng = Random::from_decimal(vector["seed"].as_str().unwrap()).unwrap();
            let selected = catalog.pick_seeded("intrusul", &mut rng, &options(&vector["options"]));
            assert_eq!(
                board_id(selected),
                vector["id"].as_str().unwrap(),
                "seeded {index}"
            );
            assert_eq!(
                rng.getrandbits(64).to_string(),
                vector["next_bits"].as_str().unwrap(),
                "seeded {index}: following RNG state"
            );
        }
        for (index, vector) in golden["daily"].as_array().unwrap().iter().enumerate() {
            let catalog = if vector["inventory"] == "bundled" {
                &bundled
            } else {
                &synthetic
            };
            let selected = catalog.pick_daily_with_options(
                "intrusul",
                vector["day"].as_str().unwrap(),
                &options(&vector["options"]),
            );
            assert_eq!(
                board_id(selected),
                vector["id"].as_str().unwrap(),
                "daily {index}"
            );
        }
    }

    #[test]
    fn blake2b8_cpython_vectors() {
        let golden: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/catalog/testdata/blake2b8.json"
        ))
        .unwrap();
        for (index, vector) in golden.as_array().unwrap().iter().enumerate() {
            let actual = blake2b8(vector["input"].as_str().unwrap().as_bytes());
            let hex: String = actual.iter().map(|byte| format!("{byte:02x}")).collect();
            assert_eq!(hex, vector["digest"].as_str().unwrap(), "BLAKE2b8 {index}");
        }
        assert_eq!(
            daily_seed("2026-10-01", "intrusul"),
            7_572_043_643_114_448_372
        );
    }

    #[test]
    fn input_order_does_not_affect_seeded_or_daily_selection() {
        let content = synthetic_content();
        let original = Catalog::new(Arc::new(content));
        let mut reversed = synthetic_content();
        reversed.boards.reverse();
        let reversed = Catalog::new(Arc::new(reversed));
        let options = FilterOptions {
            balance_categories: true,
            ..Default::default()
        };
        for seed in 0..100 {
            assert_eq!(
                board_id(original.pick_seeded("intrusul", &mut Random::from_u64(seed), &options)),
                board_id(reversed.pick_seeded("intrusul", &mut Random::from_u64(seed), &options))
            );
            let day = format!("order-test-{seed}");
            assert_eq!(
                board_id(original.pick_daily("intrusul", &day, "")),
                board_id(reversed.pick_daily("intrusul", &day, ""))
            );
        }
    }

    #[test]
    fn preferred_shelf_never_widens_strict_filters() {
        let catalog = Catalog::new(Arc::new(synthetic_content()));
        let strict = FilterOptions {
            category: "stiinta".to_owned(),
            ..Default::default()
        };
        let ids: Vec<&str> = catalog
            .pool("intrusul", &strict)
            .iter()
            .map(|board| board.catalog_id.as_str())
            .collect();
        assert_eq!(ids, ["d1", "e1"]);
        assert!(
            catalog
                .pick_daily("intrusul", "2026-10-01", "unknown")
                .is_none()
        );
        for seed in 0..100 {
            let selected = catalog
                .pick_seeded(
                    "intrusul",
                    &mut Random::from_u64(seed),
                    &FilterOptions::default(),
                )
                .unwrap();
            assert!(selected.overall_score >= 55);
        }
    }
}
