use crate::{
    catalog::blake2b8,
    content::{Content, PackItem},
    pyrandom::Random,
};
use std::{
    collections::{BTreeMap, BTreeSet},
    sync::Arc,
};

#[derive(Default, Clone)]
pub struct PickOptions {
    pub category: String,
    pub difficulty: String,
    pub exclude_ids: BTreeSet<String>,
    pub min_pool: Option<usize>,
    pub filtered_shelf_weights: bool,
}
pub struct Pack {
    items: Vec<PackItem>,
    content: Option<Arc<Content>>,
    order: Vec<usize>,
    ranked: bool,
}
impl Pack {
    pub fn new(c: Arc<Content>) -> Self {
        let mut order: Vec<_> = (0..c.pack_items.len()).collect();
        order.sort_by(|a, b| c.pack_items[*a].id.cmp(&c.pack_items[*b].id));
        Self {
            ranked: c.pack_ranked,
            content: Some(c),
            order,
            items: Vec::new(),
        }
    }
    pub fn from_items(mut items: Vec<PackItem>, ranked: bool) -> Self {
        items.sort_by(|a, b| a.id.cmp(&b.id));
        Self {
            items,
            ranked,
            content: None,
            order: Vec::new(),
        }
    }
    pub fn pool(&self, game: &str, o: &PickOptions) -> Vec<&PackItem> {
        // Borrow the single embedded catalog; never deep-clone all JSON payloads
        // into each game service. Owned small catalogs remain a test/mining seam.
        let items: Box<dyn Iterator<Item = &PackItem> + '_> = match &self.content {
            Some(content) => Box::new(self.order.iter().map(|i| &content.pack_items[*i])),
            None => Box::new(self.items.iter()),
        };
        items
            .filter(|v| {
                v.game == game
                    && (o.category.is_empty() || v.category == o.category)
                    && (o.difficulty.is_empty() || v.difficulty == o.difficulty)
                    && !o.exclude_ids.contains(&v.id)
            })
            .collect()
    }
    pub fn pick_seeded(&self, game: &str, rng: &mut Random, o: &PickOptions) -> Option<&PackItem> {
        let mut base = o.clone();
        if self.ranked {
            base.exclude_ids.clear()
        };
        let mut pool = self.pool(game, &base);
        let mut effective = None;
        let preferred: Vec<_> = pool.iter().copied().filter(|v| v.pilot_eligible).collect();
        if self.ranked {
            pool = preferred;
            if pool.is_empty() {
                return None;
            };
            if o.filtered_shelf_weights {
                effective = Some(weights(&pool))
            };
            if !o.exclude_ids.is_empty() {
                let unplayed: Vec<_> = pool
                    .iter()
                    .copied()
                    .filter(|v| !o.exclude_ids.contains(&v.id))
                    .collect();
                if !unplayed.is_empty() {
                    pool = unplayed
                }
            }
        } else if !preferred.is_empty() {
            pool = preferred
        }
        if pool.is_empty() {
            return None;
        };
        let total = pool.iter().map(|v| weight(v, effective.as_ref())).sum();
        let mut ticket = rng.randbelow(total);
        for item in pool {
            let w = weight(item, effective.as_ref());
            if ticket < w {
                return Some(item);
            };
            ticket -= w
        }
        None
    }
    pub fn pick_daily(&self, game: &str, daily: &str, o: &PickOptions) -> Option<&PackItem> {
        let floor = o
            .min_pool
            .unwrap_or(if o.category.is_empty() { 8 } else { 4 })
            .max(1);
        let mut base = o.clone();
        base.exclude_ids.clear();
        let mut pool = self.pool(game, &base);
        let preferred: Vec<_> = pool.iter().copied().filter(|v| v.pilot_eligible).collect();
        let mut effective = None;
        if self.ranked {
            pool = preferred;
            if pool.len() < floor {
                return None;
            };
            if o.filtered_shelf_weights {
                effective = Some(weights(&pool))
            }
        } else {
            if pool.len() < floor {
                return None;
            };
            if preferred.len() >= floor {
                pool = preferred
            }
        }
        pool.into_iter().min_by_key(|v| {
            let key = format!("{daily}:{game}:{}:{}:{}", o.category, o.difficulty, v.id);
            let mut rank = blake2b8(key.as_bytes());
            for ticket in 1..weight(v, effective.as_ref()) {
                rank = rank.min(blake2b8(format!("{key}:v37:{ticket}").as_bytes()))
            }
            (rank, v.id.clone())
        })
    }
    pub fn selectable_count(&self, game: &str, category: &str, difficulty: &str) -> usize {
        self.pool(
            game,
            &PickOptions {
                category: category.into(),
                difficulty: difficulty.into(),
                ..Default::default()
            },
        )
        .into_iter()
        .filter(|v| !self.ranked || v.pilot_eligible)
        .count()
    }
}
fn weights(pool: &[&PackItem]) -> BTreeMap<String, usize> {
    let mut sorted = pool.to_vec();
    sorted.sort_by(|a, b| b.pilot_score.cmp(&a.pilot_score).then(a.id.cmp(&b.id)));
    sorted
        .into_iter()
        .enumerate()
        .map(|(i, v)| (v.id.clone(), 5 - (5 * i / pool.len()).min(4)))
        .collect()
}
fn weight(item: &PackItem, effective: Option<&BTreeMap<String, usize>>) -> usize {
    if let Some(map) = effective {
        map[&item.id]
    } else {
        if (1..=5).contains(&item.selection_weight) {
            item.selection_weight as usize
        } else {
            1
        }
    }
}
