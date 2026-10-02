pub mod alchimie;
pub mod alchimie_explore;
pub mod arcade;
pub mod catalog;
pub mod conexiuni;
pub mod content;
pub mod contexto;
pub mod graph;
pub mod httpapi;
pub mod intrusul;
pub mod lant;
pub mod pack;
pub mod perechi;
pub mod pyrandom;
pub mod session;
pub mod validation;
pub mod website;

#[derive(Debug, Clone)]
pub struct ApiError {
    pub status: u16,
    pub detail: serde_json::Value,
}

impl ApiError {
    pub fn new(status: u16, detail: &str) -> Self {
        Self {
            status,
            detail: serde_json::Value::String(detail.to_owned()),
        }
    }
}

impl std::fmt::Display for ApiError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}: {}", self.status, self.detail)
    }
}
impl std::error::Error for ApiError {}
