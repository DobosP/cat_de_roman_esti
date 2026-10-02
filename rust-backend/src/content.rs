//! Shared, private reviewed export: identical bytes and digest to the Go backend.
use serde::{Deserialize, Serialize};
use serde_json::Value;
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};

pub const BUNDLED: &[u8] = include_bytes!("../../go-backend/internal/content/bundled.json");
const PIN: &str = include_str!("../../go-backend/internal/content/digest.go");

/// Canonical JSON for digests: sort every object, retain array order and UTF-8.
pub fn canonical_json(value: &Value) -> Vec<u8> {
    fn ordered(v: &Value) -> Value {
        match v {
            Value::Object(map) => {
                let mut keys: Vec<_> = map.keys().collect();
                keys.sort();
                let mut out = serde_json::Map::new();
                for k in keys {
                    out.insert(k.clone(), ordered(&map[k]));
                }
                Value::Object(out)
            }
            Value::Array(values) => Value::Array(values.iter().map(ordered).collect()),
            _ => v.clone(),
        }
    }
    serde_json::to_vec(&ordered(value)).expect("canonical public JSON")
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Board {
    pub game: String,
    pub catalog_id: String,
    pub source_id: String,
    pub category: String,
    pub difficulty: String,
    pub overall_score: i32,
    pub starter_score: i32,
    pub overall_rank: i32,
    pub starter_rank: Option<i32>,
    pub starter_safe: bool,
    pub payload: Value,
}

#[derive(Debug, Clone, Deserialize)]
#[serde(deny_unknown_fields)]
pub struct Content {
    pub schema_version: u32,
    pub app_version: String,
    pub sources: BTreeMap<String, String>,
    pub labels: BTreeMap<String, String>,
    pub category_labels: BTreeMap<String, String>,
    pub boards: Vec<Board>,
    pub manifest: Value,
    #[serde(default)]
    pub category_order: Vec<String>,
    #[serde(default)]
    pub letter_ranges: Vec<[u32; 2]>,
    #[serde(default)]
    pub label_patterns: BTreeMap<String, String>,
    #[serde(default)]
    pub nodes: Vec<Node>,
    #[serde(default)]
    pub edges: Vec<Edge>,
    #[serde(default)]
    pub pack_items: Vec<PackItem>,
    #[serde(default)]
    pub pack_ranked: bool,
    #[serde(default)]
    pub normalization_map: BTreeMap<String, String>,
    #[serde(default)]
    pub accent_normalization_map: BTreeMap<String, String>,
    #[serde(default)]
    pub casefold_map: BTreeMap<String, String>,
    #[serde(default)]
    pub normalized_index: BTreeMap<String, String>,
    #[serde(default)]
    pub contexto_data: Value,
    #[serde(default)]
    pub lant_captions: BTreeMap<String, String>,
    #[serde(default)]
    pub discovery_world: Value,
    #[serde(default)]
    pub recipe_extensions: Value,
    #[serde(default)]
    pub alchimie_projections: Value,
    #[serde(default)]
    pub metadata: Value,
}

#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Node {
    pub id: String,
    pub node_type: String,
    pub label_ro: String,
    pub category: String,
    pub description: String,
    pub salience: f64,
    pub difficulty_tier: String,
    pub degree: i32,
    pub aliases: Vec<String>,
    pub tags: Vec<String>,
    pub facets: Value,
    pub source: String,
    pub redistributable: bool,
}
#[derive(Debug, Clone, Deserialize, Serialize)]
pub struct Edge {
    pub id: String,
    #[serde(rename = "src_id")]
    pub src: String,
    #[serde(rename = "dst_id")]
    pub dst: String,
    pub relation: String,
    pub label_ro: String,
    pub strength: f64,
    pub is_distractor: bool,
    pub bidirectional: bool,
    pub tags: Vec<String>,
    pub facets: Value,
    pub source: String,
    pub redistributable: bool,
}
#[derive(Debug, Clone, Deserialize)]
pub struct PackItem {
    pub game: String,
    pub id: String,
    pub category: String,
    pub difficulty: String,
    pub payload: Value,
    pub source: String,
    pub status: String,
    pub pilot_score: i32,
    pub pilot_eligible: bool,
    pub selection_weight: i32,
}

fn hash_valid(s: &str) -> bool {
    s.len() == 64 && s.bytes().all(|b| b.is_ascii_hexdigit())
}

impl Content {
    pub fn load() -> Result<Self, String> {
        let expected = PIN.split('"').nth(1).ok_or("missing embedded digest pin")?;
        if !hash_valid(expected) || format!("{:x}", Sha256::digest(BUNDLED)) != expected {
            return Err("private content: embedded export digest drift".into());
        }
        Self::decode(BUNDLED)
    }

    pub fn decode(raw: &[u8]) -> Result<Self, String> {
        let content: Self = serde_json::from_slice(raw).map_err(|e| e.to_string())?;
        if content.schema_version != 2
            || content.app_version.is_empty()
            || content.labels.is_empty()
            || content.boards.is_empty()
        {
            return Err("private content: incomplete schema".into());
        }
        let m = &content.manifest;
        let hash = m["content_hash"].as_str().unwrap_or("");
        if !hash.starts_with("sha256:")
            || !hash_valid(&hash[7..])
            || m["build_version"].as_str().unwrap_or("").is_empty()
            || m["app"] != "cat_de_roman_esti"
            || m["manifest_version"] != 1
            || m["schema_version"] != 1
            || m["counts"]["nodes"].as_u64() != Some(content.labels.len() as u64)
        {
            return Err("private content: invalid manifest identity".into());
        }
        for name in [
            "kg_sample.json",
            "derived_catalog_v38.json",
            "quick_games_v92.json",
            "board_rankings_v37.json",
            "release_reserve_v1.json",
            "games_pack.json",
        ] {
            if !content.sources.get(name).is_some_and(|s| hash_valid(s)) {
                return Err(format!("private content: missing source identity {name}"));
            }
        }
        let mut seen = BTreeSet::new();
        for b in &content.boards {
            if (b.game != "intrusul" && b.game != "perechi")
                || b.catalog_id.is_empty()
                || !seen.insert(&b.catalog_id)
                || b.source_id.is_empty()
                || !content.category_labels.contains_key(&b.category)
                || !(0..=100).contains(&b.overall_score)
                || !(0..=100).contains(&b.starter_score)
            {
                return Err("private content: invalid board identity/rank".into());
            }
            if b.game == "perechi" {
                let pairs = b.payload["pairs"]
                    .as_array()
                    .ok_or("invalid Perechi pairs")?;
                if pairs.len() != 4 {
                    return Err("invalid Perechi pairs".into());
                }
                let mut ids = BTreeSet::new();
                for pair in pairs {
                    let members = pair["members"]
                        .as_array()
                        .ok_or("invalid Perechi members")?;
                    if members.len() != 2 {
                        return Err("invalid Perechi members".into());
                    }
                    for value in members {
                        let id = value.as_str().ok_or("invalid Perechi ID")?;
                        if !content.labels.contains_key(id) || !ids.insert(id) {
                            return Err("invalid Perechi ID".into());
                        }
                    }
                }
                continue;
            }
            let members = b.payload["members"].as_array().ok_or("invalid members")?;
            let intruder = b.payload["intruder"].as_str().ok_or("invalid intruder")?;
            if members.len() != 3
                || !content.labels.contains_key(intruder)
                || b.payload["group_label"].as_str().unwrap_or("").is_empty()
            {
                return Err("private content: invalid Intrusul payload".into());
            }
            let mut ids = BTreeSet::from([intruder]);
            for id in members {
                let id = id.as_str().ok_or("invalid member ID")?;
                if !content.labels.contains_key(id) || !ids.insert(id) {
                    return Err("private content: invalid Intrusul members".into());
                }
            }
        }
        Ok(content)
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn export_is_identical_and_fail_closed() {
        let c = Content::load().unwrap();
        assert_eq!(
            c.boards.iter().filter(|b| b.game == "intrusul").count(),
            226
        );
        let mut v: Value = serde_json::from_slice(BUNDLED).unwrap();
        v["manifest"] = serde_json::json!({});
        assert!(Content::decode(&serde_json::to_vec(&v).unwrap()).is_err());
        let mut extra = BUNDLED.to_vec();
        extra.extend_from_slice(b" {}");
        assert!(Content::decode(&extra).is_err());
    }
}
