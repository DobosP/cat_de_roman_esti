//! Anonymous game storage and routing, executed on the HTTP blocking pool.
use crate::{
    ApiError,
    alchimie::Alchimie,
    alchimie_explore::Explorer,
    conexiuni::Conexiuni,
    content::Content,
    contexto::{Contexto, GuessBody},
    httpapi,
    lant::Lant,
    perechi::Perechi,
    validation,
};
use serde_json::Value;
use std::sync::Arc;

pub struct Arcade {
    content: Arc<Content>,
    perechi: Perechi,
    conexiuni: Conexiuni,
    contexto: Contexto,
    lant: Lant,
    alchimie: Alchimie,
    explorer: Explorer,
}

impl Arcade {
    pub fn new(content: Arc<Content>) -> Self {
        Self {
            perechi: Perechi::new(Arc::clone(&content)),
            conexiuni: Conexiuni::new(Arc::clone(&content)),
            contexto: Contexto::new(Arc::clone(&content)),
            lant: Lant::new(Arc::clone(&content)),
            alchimie: Alchimie::new(Arc::clone(&content)),
            explorer: Explorer::new(Arc::clone(&content)),
            content,
        }
    }

    /// None is reserved for paths outside these native game families. A known
    /// family always returns its own 404/405 or authoritative game response.
    pub fn handle(
        &self,
        method: &str,
        path: &str,
        query: &str,
        raw: &[u8],
    ) -> Option<Result<Value, ApiError>> {
        if path.starts_with("/api/alchimie/") {
            return Some(self.exploration(method, path, raw));
        }
        let rest = path.strip_prefix("/api/wordgames/")?;
        let game = rest.split('/').next()?;
        if !["perechi", "conexiuni", "contexto", "lant", "alchimie"].contains(&game) {
            return None;
        }
        let prefix = format!("/api/wordgames/{game}/games");
        if path == prefix {
            return Some(if method == "POST" {
                self.create(game, query)
            } else {
                Err(ApiError::new(405, "Method Not Allowed"))
            });
        }
        let Some(tail) = path.strip_prefix(&format!("{prefix}/")) else {
            return Some(Err(ApiError::new(404, "Not Found")));
        };
        let segments: Vec<_> = tail.split('/').collect();
        if segments[0].is_empty() || segments.len() > 2 {
            return Some(Err(ApiError::new(404, "Not Found")));
        }
        let id = segments[0];
        if segments.len() == 1 {
            return Some(if method == "GET" || method == "HEAD" {
                match game {
                    "perechi" => self.perechi.get(id),
                    "conexiuni" => self.conexiuni.get(id),
                    "contexto" => self.contexto.get(id),
                    "lant" => self.lant.get(id),
                    "alchimie" => self.alchimie.get(id),
                    _ => unreachable!(),
                }
            } else {
                Err(ApiError::new(405, "Method Not Allowed"))
            });
        }
        let action = segments[1];
        let known = match game {
            "perechi" => ["match", "hint"].contains(&action),
            "conexiuni" => ["guess", "clue"].contains(&action),
            "contexto" => ["guess", "clue", "giveup"].contains(&action),
            "lant" => ["move", "undo", "hint"].contains(&action),
            "alchimie" => ["combine", "hint", "reset"].contains(&action),
            _ => false,
        };
        if !known {
            return Some(Err(ApiError::new(404, "Not Found")));
        }
        if method != "POST" {
            return Some(Err(ApiError::new(405, "Method Not Allowed")));
        }
        Some(match (game, action) {
            ("perechi", "match") => self
                .perechi
                .match_input(id, || validation::ids(raw, "MatchBody")),
            ("perechi", "hint") => self.perechi.hint(id),
            ("conexiuni", "guess") => self
                .conexiuni
                .guess_input(id, || validation::ids(raw, "GuessBody")),
            ("conexiuni", "clue") => self.conexiuni.clue(id),
            ("contexto", "guess") => self.contexto.guess_input(id, || {
                let (text, confirm) = validation::contexto_guess(raw)?;
                Ok(GuessBody { text, confirm })
            }),
            ("contexto", "clue") => self.contexto.clue(id),
            ("contexto", "giveup") => self.contexto.give_up(id),
            ("lant", "move") => self
                .lant
                .move_input(id, || validation::text(raw, "MoveBody")),
            ("lant", "undo") => self.lant.undo(id),
            ("lant", "hint") => self.lant.hint(id),
            ("alchimie", "combine") => self
                .alchimie
                .combine_input(id, || validation::pair(raw, "CombineBody", false)),
            ("alchimie", "hint") => self.alchimie.hint(id),
            ("alchimie", "reset") => self.alchimie.reset(id),
            _ => unreachable!(),
        })
    }

    fn create(&self, game: &str, query: &str) -> Result<Value, ApiError> {
        let q = httpapi::query_values(query);
        let seed = httpapi::query_int(&q, "seed")?;
        let starter = if game == "perechi" {
            httpapi::query_int(&q, "starter")?
        } else {
            None
        };
        let last = |key: &str| {
            q.get(key)
                .and_then(|values| values.last())
                .map_or("", String::as_str)
        };
        let category = last("category");
        if q.contains_key("category") && !self.content.category_labels.contains_key(category) {
            return Err(ApiError::new(400, "Categorie necunoscută."));
        }
        if starter
            .as_deref()
            .is_some_and(|starter| starter != "0" && starter != "1")
        {
            return Err(ApiError::new(400, "starter trebuie să fie 0 sau 1."));
        }
        let daily = last("daily");
        let daily_option = q.get("daily").map(|_| daily);
        let difficulty = if q.contains_key("difficulty") {
            last("difficulty")
        } else {
            "normal"
        };
        match game {
            "perechi" => self.perechi.create(
                seed.as_deref(),
                daily,
                category,
                last("previous_game_id"),
                starter.as_deref() == Some("1"),
            ),
            "conexiuni" => self
                .conexiuni
                .create(seed.as_deref(), daily, category, difficulty),
            "contexto" => self
                .contexto
                .create(seed.as_deref(), difficulty, daily_option, category),
            "lant" => self
                .lant
                .create(seed.as_deref(), difficulty, daily_option, category),
            "alchimie" => self
                .alchimie
                .create(seed.as_deref(), daily, category, difficulty),
            _ => Err(ApiError::new(404, "Not Found")),
        }
    }

    fn exploration(&self, method: &str, path: &str, raw: &[u8]) -> Result<Value, ApiError> {
        let prefix = "/api/alchimie/explore";
        if path == prefix {
            if method != "POST" {
                return Err(ApiError::new(405, "Method Not Allowed"));
            }
            let (progress, goal) = validation::exploration_create(raw)?;
            return self.explorer.create(progress.as_ref(), goal.as_deref());
        }
        let tail = path
            .strip_prefix("/api/alchimie/explore/")
            .ok_or_else(|| ApiError::new(404, "Not Found"))?;
        let segments: Vec<_> = tail.split('/').collect();
        if segments[0].is_empty() || segments.len() > 2 {
            return Err(ApiError::new(404, "Not Found"));
        }
        if segments.len() == 1 {
            return if method == "GET" || method == "HEAD" {
                self.explorer.get(segments[0])
            } else {
                Err(ApiError::new(405, "Method Not Allowed"))
            };
        }
        let (id, action) = (segments[0], segments[1]);
        if !["combine", "hint", "goal"].contains(&action) {
            return Err(ApiError::new(404, "Not Found"));
        }
        if method != "POST" {
            return Err(ApiError::new(405, "Method Not Allowed"));
        }
        match action {
            "combine" => self
                .explorer
                .combine_input(id, || validation::pair(raw, "PairBody", true)),
            "hint" => self.explorer.hint(id),
            "goal" => self.explorer.goal_input(id, || validation::goal(raw)),
            _ => unreachable!(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn known_routes_never_fall_back_and_inputs_are_validated_inside_sessions() {
        let arcade = Arcade::new(Arc::new(Content::load().unwrap()));
        assert!(arcade.handle("GET", "/unrelated", "", b"").is_none());
        for game in ["perechi", "conexiuni", "contexto", "lant", "alchimie"] {
            let prefix = format!("/api/wordgames/{game}/games");
            assert_eq!(
                arcade
                    .handle("GET", &prefix, "", b"")
                    .unwrap()
                    .unwrap_err()
                    .status,
                405
            );
            assert_eq!(
                arcade
                    .handle("POST", &format!("{prefix}/missing/unknown"), "", b"{}")
                    .unwrap()
                    .unwrap_err()
                    .status,
                404
            );
            assert_eq!(
                arcade
                    .handle("POST", &prefix, "seed=invalid", b"{}")
                    .unwrap()
                    .unwrap_err()
                    .status,
                422
            );
        }
        assert_eq!(
            arcade
                .handle(
                    "POST",
                    "/api/wordgames/perechi/games/missing/match",
                    "",
                    b"{broken"
                )
                .unwrap()
                .unwrap_err()
                .status,
            404
        );
        assert_eq!(
            arcade
                .handle("POST", "/api/alchimie/explore/missing/goal", "", b"{}")
                .unwrap()
                .unwrap_err()
                .status,
            404
        );
        assert_eq!(
            arcade
                .handle("POST", "/api/alchimie/explore", "", br#"{"progress":{}}"#)
                .unwrap()
                .unwrap_err()
                .status,
            422
        );
        let explore = arcade
            .handle("POST", "/api/alchimie/explore", "", b"{}")
            .unwrap()
            .unwrap();
        let id = explore["game_id"].as_str().unwrap();
        assert_eq!(
            arcade
                .handle(
                    "POST",
                    &format!("/api/alchimie/explore/{id}/combine"),
                    "",
                    br#"{"a":"","b":"x","extra":true}"#
                )
                .unwrap()
                .unwrap_err()
                .status,
            422
        );
    }
}
