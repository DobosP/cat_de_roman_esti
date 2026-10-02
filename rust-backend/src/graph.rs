//! Shared directed graph and exact Romanian text-resolution primitives.
use crate::content::{Content, Edge, Node};
use std::{
    cmp::Ordering,
    collections::{BTreeMap, BinaryHeap, HashMap},
    sync::{Arc, Mutex, OnceLock, Weak},
};

pub struct Neighbor<'a> {
    pub id: &'a str,
    pub edge: &'a Edge,
}
pub struct Service {
    pub content: Arc<Content>,
    nodes: HashMap<String, usize>,
    all: Vec<String>,
    real: HashMap<String, Vec<(String, usize)>>,
    full: HashMap<String, Vec<(String, usize)>>,
    adj: BTreeMap<String, Vec<String>>,
    rev: BTreeMap<String, Vec<String>>,
    positions: HashMap<String, usize>,
    dense_adj: Vec<Vec<usize>>,
    dense_rev: Vec<Vec<usize>>,
    dense_costs: Vec<Vec<f64>>,
}
impl Service {
    pub fn new(content: Arc<Content>) -> Arc<Self> {
        static CACHE: OnceLock<Mutex<HashMap<usize, Weak<Service>>>> = OnceLock::new();
        let mut cache = CACHE
            .get_or_init(|| Mutex::new(HashMap::new()))
            .lock()
            .unwrap_or_else(|e| e.into_inner());
        cache.retain(|_, v| v.strong_count() > 0);
        let key = Arc::as_ptr(&content) as usize;
        if let Some(g) = cache.get(&key).and_then(Weak::upgrade) {
            return g;
        };
        let g = Arc::new(Self::build(content));
        cache.insert(key, Arc::downgrade(&g));
        g
    }
    fn build(content: Arc<Content>) -> Self {
        let nodes: HashMap<_, _> = content
            .nodes
            .iter()
            .enumerate()
            .map(|(i, n)| (n.id.clone(), i))
            .collect();
        let mut all: Vec<_> = nodes.keys().cloned().collect();
        all.sort();
        let mut raw: HashMap<String, Vec<(String, usize)>> = HashMap::new();
        for (i, e) in content.edges.iter().enumerate() {
            raw.entry(e.src.clone())
                .or_default()
                .push((e.dst.clone(), i));
            if e.bidirectional {
                raw.entry(e.dst.clone())
                    .or_default()
                    .push((e.src.clone(), i))
            }
        }
        let mut g = Self {
            content,
            nodes,
            all,
            real: HashMap::new(),
            full: HashMap::new(),
            adj: BTreeMap::new(),
            rev: BTreeMap::new(),
            positions: HashMap::new(),
            dense_adj: vec![],
            dense_rev: vec![],
            dense_costs: vec![],
        };
        for id in &g.all {
            for distractors in [false, true] {
                let mut best: HashMap<String, usize> = HashMap::new();
                for (dst, e) in raw.get(id).into_iter().flatten() {
                    let edge = &g.content.edges[*e];
                    if !g.nodes.contains_key(dst) || (!distractors && edge.is_distractor) {
                        continue;
                    };
                    if best
                        .get(dst)
                        .is_none_or(|old| edge.strength > g.content.edges[*old].strength)
                    {
                        best.insert(dst.clone(), *e);
                    }
                }
                let mut nbs: Vec<_> = best.into_iter().collect();
                nbs.sort_by(|(a, ae), (b, be)| {
                    g.content.edges[*be]
                        .strength
                        .total_cmp(&g.content.edges[*ae].strength)
                        .then_with(|| g.label(a).cmp(g.label(b)))
                        .then(a.cmp(b))
                });
                if distractors {
                    g.full.insert(id.clone(), nbs);
                } else {
                    let mut ids: Vec<_> = nbs.iter().map(|(id, _)| id.clone()).collect();
                    ids.sort();
                    for next in &ids {
                        g.rev.entry(next.clone()).or_default().push(id.clone());
                    }
                    g.adj.insert(id.clone(), ids);
                    g.real.insert(id.clone(), nbs);
                }
            }
        }
        for ids in g.rev.values_mut() {
            ids.sort();
        }
        g.positions = g
            .all
            .iter()
            .enumerate()
            .map(|(i, id)| (id.clone(), i))
            .collect();
        g.dense_adj = g
            .all
            .iter()
            .map(|id| g.adj[id].iter().map(|next| g.positions[next]).collect())
            .collect();
        g.dense_rev = g
            .all
            .iter()
            .map(|id| {
                g.rev
                    .get(id)
                    .into_iter()
                    .flatten()
                    .map(|previous| g.positions[previous])
                    .collect()
            })
            .collect();
        g.dense_costs = g
            .all
            .iter()
            .map(|id| {
                g.rev
                    .get(id)
                    .into_iter()
                    .flatten()
                    .map(|previous| edge_cost(g.link(previous, id).unwrap().strength))
                    .collect()
            })
            .collect();
        g
    }
    pub fn node(&self, id: &str) -> Option<&Node> {
        self.nodes.get(id).map(|i| &self.content.nodes[*i])
    }
    pub fn exists(&self, id: &str) -> bool {
        self.nodes.contains_key(id)
    }
    pub fn label<'a>(&'a self, id: &'a str) -> &'a str {
        self.node(id).map_or(id, |n| n.label_ro.as_str())
    }
    pub fn display_label<'a>(&'a self, id: &'a str) -> &'a str {
        self.content.labels.get(id).map_or(id, String::as_str)
    }
    pub fn description(&self, id: &str) -> &str {
        self.node(id).map_or("", |n| n.description.as_str())
    }
    pub fn salience(&self, id: &str) -> f64 {
        self.node(id).map_or(0., |n| n.salience)
    }
    pub fn all_ids(&self) -> Vec<String> {
        self.all.clone()
    }
    pub fn by_category(&self, cat: &str) -> Vec<String> {
        self.all
            .iter()
            .filter(|id| self.node(id).unwrap().category == cat)
            .cloned()
            .collect()
    }
    pub fn by_salience(&self, minimum: f64, descending: bool) -> Vec<String> {
        let mut ids: Vec<_> = self
            .all
            .iter()
            .filter(|id| self.salience(id) >= minimum)
            .cloned()
            .collect();
        ids.sort_by(|a, b| {
            let cmp = self.salience(a).total_cmp(&self.salience(b)).then(a.cmp(b));
            if descending { cmp.reverse() } else { cmp }
        });
        ids
    }
    pub fn neighbors(&self, id: &str, include_distractors: bool) -> Vec<Neighbor<'_>> {
        let table = if include_distractors {
            &self.full
        } else {
            &self.real
        };
        table
            .get(id)
            .into_iter()
            .flatten()
            .map(|(id, e)| Neighbor {
                id,
                edge: &self.content.edges[*e],
            })
            .collect()
    }
    pub fn neighbor_ids(&self, id: &str) -> Vec<String> {
        self.adj.get(id).cloned().unwrap_or_default()
    }
    pub fn predecessor_ids(&self, id: &str) -> Vec<String> {
        self.rev.get(id).cloned().unwrap_or_default()
    }
    pub fn degree(&self, id: &str) -> usize {
        self.adj.get(id).map_or(0, Vec::len)
    }
    pub fn link(&self, a: &str, b: &str) -> Option<&Edge> {
        self.real
            .get(a)
            .into_iter()
            .flatten()
            .find(|(id, _)| id == b)
            .map(|(_, e)| &self.content.edges[*e])
    }
    pub fn link_label(&self, a: &str, b: &str) -> &str {
        self.link(a, b).map_or("", |e| e.label_ro.as_str())
    }
    pub fn common_neighbors(&self, a: &str, b: &str, category: &str) -> Vec<String> {
        let aa = self.neighbor_ids(a);
        let bb = self.neighbor_ids(b);
        aa.into_iter()
            .filter(|id| {
                bb.binary_search(id).is_ok()
                    && (category.is_empty() || self.node(id).unwrap().category == category)
            })
            .collect()
    }
    pub fn distances_from_ordered(&self, id: &str) -> (BTreeMap<String, usize>, Vec<String>) {
        self.distance_map(id, false)
    }
    pub fn distances_to_ordered(&self, id: &str) -> (BTreeMap<String, usize>, Vec<String>) {
        self.distance_map(id, true)
    }
    pub fn distances_from(&self, id: &str) -> BTreeMap<String, usize> {
        self.distance_map_only(id, false)
    }
    pub fn distances_to(&self, id: &str) -> BTreeMap<String, usize> {
        self.distance_map_only(id, true)
    }
    pub fn distance(&self, a: &str, b: &str) -> Option<usize> {
        if a == b {
            return Some(0);
        }
        if !self.exists(a) || !self.exists(b) {
            return None;
        };
        let (Some(start), Some(target)) = (self.index(a), self.index(b)) else {
            return None;
        };
        let mut dist = vec![-1i32; self.all.len()];
        let mut queue = Vec::with_capacity(self.all.len());
        queue.push(start);
        dist[start] = 0;
        let mut at = 0;
        while at < queue.len() {
            let current = queue[at];
            for &next in &self.dense_adj[current] {
                if dist[next] >= 0 {
                    continue;
                };
                dist[next] = dist[current] + 1;
                if next == target {
                    return Some(dist[next] as usize);
                }
                queue.push(next);
            }
            at += 1;
        }
        None
    }
    pub fn weighted_distances_to(&self, target: &str) -> BTreeMap<String, f64> {
        let mut out: BTreeMap<_, _> = self
            .weighted_distances_to_dense(target)
            .into_iter()
            .enumerate()
            .filter(|(_, cost)| cost.is_finite())
            .map(|(i, cost)| (self.all[i].clone(), cost))
            .collect();
        if self.index(target).is_none() {
            out.insert(target.to_owned(), 0.);
        }
        out
    }
    pub fn index(&self, id: &str) -> Option<usize> {
        self.positions.get(id).copied()
    }
    pub fn id_at(&self, index: usize) -> &str {
        &self.all[index]
    }
    pub fn node_count(&self) -> usize {
        self.all.len()
    }
    fn dense_bfs(&self, id: &str, reverse: bool) -> (Vec<i32>, Vec<usize>) {
        let mut dist = vec![-1; self.all.len()];
        let mut order = Vec::with_capacity(self.all.len());
        let Some(start) = self.index(id) else {
            return (dist, order);
        };
        dist[start] = 0;
        order.push(start);
        let adjacency = if reverse {
            &self.dense_rev
        } else {
            &self.dense_adj
        };
        let mut at = 0;
        while at < order.len() {
            let current = order[at];
            for &next in &adjacency[current] {
                if dist[next] < 0 {
                    dist[next] = dist[current] + 1;
                    order.push(next)
                }
            }
            at += 1;
        }
        (dist, order)
    }
    fn distance_map_only(&self, id: &str, reverse: bool) -> BTreeMap<String, usize> {
        let (dist, order) = self.dense_bfs(id, reverse);
        if order.is_empty() {
            return BTreeMap::from([(id.to_owned(), 0)]);
        };
        order
            .into_iter()
            .map(|i| (self.all[i].clone(), dist[i] as usize))
            .collect()
    }
    fn distance_map(&self, id: &str, reverse: bool) -> (BTreeMap<String, usize>, Vec<String>) {
        let (dist, order) = self.dense_bfs(id, reverse);
        if order.is_empty() {
            return (BTreeMap::from([(id.to_owned(), 0)]), vec![id.to_owned()]);
        };
        let map = order
            .iter()
            .map(|i| (self.all[*i].clone(), dist[*i] as usize))
            .collect();
        let order = order.into_iter().map(|i| self.all[i].clone()).collect();
        (map, order)
    }
    pub fn distances_to_dense(&self, target: &str) -> Vec<i32> {
        self.dense_bfs(target, true).0
    }
    pub fn weighted_distances_to_dense(&self, target: &str) -> Vec<f64> {
        let mut dist = vec![f64::INFINITY; self.all.len()];
        let Some(start) = self.index(target) else {
            return dist;
        };
        dist[start] = 0.;
        let mut heap = BinaryHeap::from([CostNode {
            cost: 0.,
            index: start,
        }]);
        while let Some(current) = heap.pop() {
            if current.cost > dist[current.index] {
                continue;
            };
            for (at, &previous) in self.dense_rev[current.index].iter().enumerate() {
                let cost = current.cost + self.dense_costs[current.index][at];
                if cost < dist[previous] {
                    dist[previous] = cost;
                    heap.push(CostNode {
                        cost,
                        index: previous,
                    });
                }
            }
        }
        dist
    }
    pub fn normalize(&self, text: &str) -> String {
        transform(text, &self.content.normalization_map)
    }
    pub fn casefold(&self, text: &str) -> String {
        let mut result = String::new();
        for c in text.chars() {
            if let Some(v) = self.content.casefold_map.get(&c.to_string()) {
                result.push_str(v)
            } else {
                result.push(c)
            }
        }
        result
    }
    pub fn reviewed_unresolved(&self, text: &str) -> bool {
        let key =
            transform(text, &self.content.accent_normalization_map).replace('\u{0327}', "\u{0326}");
        key == "pas\u{0326}te" || key == "pas\u{0326}tele"
    }
    pub fn resolve(&self, text: &str) -> Option<String> {
        if text.is_empty() || self.reviewed_unresolved(text) {
            return None;
        };
        self.content
            .normalized_index
            .get(&self.normalize(text))
            .cloned()
    }
    pub fn suggest(&self, text: &str, limit: usize) -> Vec<String> {
        if self.reviewed_unresolved(text) || limit == 0 {
            return vec![];
        };
        let key = self.normalize(text);
        if key.is_empty() {
            return vec![];
        };
        let length = key.chars().count();
        let mut scores: Vec<_> = self
            .content
            .normalized_index
            .iter()
            .filter_map(|(cand, id)| {
                if ratio_upper_len(cand.chars().count(), length) < 0.78 {
                    return None;
                };
                let score = sequence_ratio(cand, &key);
                (score >= 0.78).then_some((score, cand, id))
            })
            .collect();
        scores.sort_by(|a, b| b.0.total_cmp(&a.0).then(b.1.cmp(a.1)));
        scores.truncate(limit * 4);
        let mut seen = std::collections::BTreeSet::new();
        let mut out = vec![];
        for (_, _, id) in scores {
            if seen.insert(id) {
                out.push(self.label(id).to_owned());
                if out.len() == limit {
                    break;
                }
            }
        }
        out
    }
    pub fn resolve_fuzzy(&self, text: &str) -> Option<String> {
        if self.reviewed_unresolved(text) {
            return None;
        };
        let key = self.normalize(text);
        if key.is_empty() {
            return None;
        };
        if let Some(exact) = self.content.normalized_index.get(&key) {
            return Some(exact.clone());
        };
        if ["intrigii", "intrigilor"].contains(&key.as_str()) {
            return None;
        };
        let length = key.chars().count();
        let mut best: HashMap<&str, f64> = HashMap::new();
        for (cand, id) in &self.content.normalized_index {
            if ratio_upper_len(cand.chars().count(), length) < 0.84 {
                continue;
            };
            let score = sequence_ratio(cand, &key);
            if score >= 0.84 && best.get(id.as_str()).is_none_or(|old| score > *old) {
                best.insert(id, score);
            }
        }
        let mut ranked: Vec<_> = best.into_iter().collect();
        ranked.sort_by(|a, b| b.1.total_cmp(&a.1).then(a.0.cmp(b.0)));
        if ranked.is_empty()
            || ranked[0].1 < 0.90
            || (ranked.len() > 1 && ranked[0].1 - ranked[1].1 <= 0.06)
        {
            None
        } else {
            Some(ranked[0].0.to_owned())
        }
    }
}
#[derive(PartialEq)]
struct CostNode {
    cost: f64,
    index: usize,
}
impl Eq for CostNode {}
impl Ord for CostNode {
    fn cmp(&self, other: &Self) -> Ordering {
        other
            .cost
            .total_cmp(&self.cost)
            .then_with(|| other.index.cmp(&self.index))
    }
}
impl PartialOrd for CostNode {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}
fn edge_cost(strength: f64) -> f64 {
    if !strength.is_finite() || strength <= 0. {
        1.5
    } else {
        2. - strength.clamp(0., 1.)
    }
}
fn py_space(c: char) -> bool {
    matches!(c,'\u{9}'..='\u{d}'|'\u{1c}'..='\u{20}'|'\u{85}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}')
}
fn transform(text: &str, mapping: &BTreeMap<String, String>) -> String {
    let mut result = String::new();
    for c in text.chars() {
        if let Some(replacement) = mapping.get(&c.to_string()) {
            result.push_str(replacement)
        } else {
            result.push(c)
        }
    }
    result
        .split(py_space)
        .filter(|s| !s.is_empty())
        .collect::<Vec<_>>()
        .join(" ")
}
fn ratio_upper_len(a: usize, b: usize) -> f64 {
    if a + b == 0 {
        1.
    } else {
        2. * a.min(b) as f64 / (a + b) as f64
    }
}
pub fn sequence_ratio(a: &str, b: &str) -> f64 {
    let (a, b): (Vec<_>, Vec<_>) = (a.chars().collect(), b.chars().collect());
    if a.len() + b.len() == 0 {
        return 1.;
    };
    let mut positions: HashMap<char, Vec<usize>> = HashMap::new();
    for (j, c) in b.iter().enumerate() {
        positions.entry(*c).or_default().push(j)
    }
    if b.len() >= 200 {
        positions.retain(|_, js| js.len() <= b.len() / 100 + 1);
    }
    let mut queue = vec![(0, a.len(), 0, b.len())];
    let mut matches = 0;
    while let Some((alo, ahi, blo, bhi)) = queue.pop() {
        let (mut bi, mut bj, mut size) = (alo, blo, 0);
        let mut previous: HashMap<usize, usize> = HashMap::new();
        for (i, c) in a.iter().enumerate().take(ahi).skip(alo) {
            let mut current = HashMap::new();
            for &j in positions.get(c).into_iter().flatten() {
                if j < blo {
                    continue;
                }
                if j >= bhi {
                    break;
                };
                let k = if j > 0 {
                    previous.get(&(j - 1)).copied().unwrap_or(0) + 1
                } else {
                    1
                };
                current.insert(j, k);
                if k > size {
                    bi = i + 1 - k;
                    bj = j + 1 - k;
                    size = k;
                }
            }
            previous = current;
        }
        while bi > alo && bj > blo && a[bi - 1] == b[bj - 1] {
            bi -= 1;
            bj -= 1;
            size += 1;
        }
        while bi + size < ahi && bj + size < bhi && a[bi + size] == b[bj + size] {
            size += 1;
        }
        if size > 0 {
            matches += size;
            if alo < bi && blo < bj {
                queue.push((alo, bi, blo, bj));
            }
            if bi + size < ahi && bj + size < bhi {
                queue.push((bi + size, ahi, bj + size, bhi));
            }
        }
    }
    2. * matches as f64 / (a.len() + b.len()) as f64
}

#[cfg(test)]
mod tests {
    use super::*;
    use serde_json::Value;
    #[test]
    fn canonical_python_graph() {
        let c = Arc::new(Content::load().unwrap());
        let g = Service::new(c.clone());
        assert!(Arc::ptr_eq(&g, &Service::new(c)));
        let v: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/graph/testdata/python_graph.json"
        ))
        .unwrap();
        for row in v["texts"].as_array().unwrap() {
            let text = row["text"].as_str().unwrap();
            assert_eq!(
                g.normalize(text),
                row["normalized"].as_str().unwrap(),
                "normalize {text}"
            );
            assert_eq!(
                g.reviewed_unresolved(text),
                row["unresolved"].as_bool().unwrap(),
                "guard {text}"
            );
            assert_eq!(
                g.resolve(text).unwrap_or_default(),
                row["resolved"].as_str().unwrap(),
                "resolve {text}"
            );
            assert_eq!(
                g.resolve_fuzzy(text).unwrap_or_default(),
                row["fuzzy"].as_str().unwrap(),
                "fuzzy {text}"
            );
            assert_eq!(
                serde_json::json!(g.suggest(text, 3)),
                row["suggestions"],
                "suggest {text}"
            );
        }
        for row in v["ratios"].as_array().unwrap() {
            assert_eq!(
                sequence_ratio(row[0].as_str().unwrap(), row[1].as_str().unwrap()),
                row[2].as_f64().unwrap(),
                "ratio {row}"
            );
        }
        for row in v["targets"].as_array().unwrap() {
            let id = row["id"].as_str().unwrap();
            let (from, from_order) = g.distances_from_ordered(id);
            let (to, to_order) = g.distances_to_ordered(id);
            assert_eq!(serde_json::json!(from), row["from"], "from {id}");
            assert_eq!(serde_json::json!(to), row["to"], "to {id}");
            assert_eq!(
                serde_json::json!(from_order),
                row["from_order"],
                "from order {id}"
            );
            assert_eq!(
                serde_json::json!(to_order),
                row["to_order"],
                "to order {id}"
            );
            assert_eq!(
                serde_json::json!(g.neighbor_ids(id)),
                row["neighbors"],
                "neighbors {id}"
            );
            for (node, value) in g.weighted_distances_to(id) {
                assert_eq!(
                    value,
                    row["weighted"][&node].as_f64().unwrap(),
                    "Dijkstra {id}/{node}"
                );
            }
        }
        assert_eq!(serde_json::json!(g.by_salience(0.6, true)), v["salience"]);
        assert_eq!(
            serde_json::json!(g.by_salience(0., false)),
            v["salience_ascending"]
        );
    }
}
