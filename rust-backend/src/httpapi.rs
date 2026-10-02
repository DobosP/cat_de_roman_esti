//! Axum transport for the anonymous six-game arcade and exploration API.
use crate::{ApiError, content::Content, intrusul::Intrusul};
use axum::{
    Router,
    body::{Body, to_bytes},
    extract::{Request, State},
    response::Response,
};
use http::{HeaderMap, HeaderValue, StatusCode};
use num_bigint::BigInt;
use serde::{Deserialize, Serialize};
use serde_json::{Value, json};
use std::{
    collections::BTreeMap,
    sync::{Arc, OnceLock},
    time::Duration,
};

pub const MAX_REQUEST_BYTES: usize = 65536;
const PREFIX: &str = "/api/wordgames/intrusul/games";
const DECIMAL_SOURCE: &str = include_str!("../../go-backend/internal/httpapi/decimal.go");

struct AppState {
    content: Arc<Content>,
    game: Intrusul,
    arcade: crate::arcade::Arcade,
    static_root: std::path::PathBuf,
    upstream: Option<String>,
    client: Option<reqwest::Client>,
}

pub fn router(content: Arc<Content>, upstream: Option<String>) -> Result<Router, String> {
    let client = if upstream.is_some() {
        Some(
            reqwest::Client::builder()
                .no_proxy()
                .timeout(Duration::from_secs(30))
                .redirect(reqwest::redirect::Policy::none())
                .build()
                .map_err(|e| e.to_string())?,
        )
    } else {
        None
    };
    let state = Arc::new(AppState {
        game: Intrusul::new(content.clone()),
        arcade: crate::arcade::Arcade::new(content.clone()),
        static_root: crate::website::default_static_root(),
        content,
        upstream,
        client,
    });
    Ok(Router::new().fallback(handle).with_state(state))
}

fn reply(status: u16, body: Value, head: bool, cors: &HeaderMap) -> Response {
    let data = encode_json(&body).expect("public JSON is serializable");
    let mut response = Response::builder()
        .status(status)
        .header("content-type", "application/json")
        .header("x-content-type-options", "nosniff")
        .header("referrer-policy", "same-origin")
        .body(if head {
            Body::empty()
        } else {
            Body::from(data)
        })
        .unwrap();
    response.headers_mut().extend(cors.clone());
    if status == 413 {
        response
            .headers_mut()
            .insert("cache-control", HeaderValue::from_static("no-store"));
    }
    response
}

fn error(status: u16, message: &str, head: bool, cors: &HeaderMap) -> Response {
    reply(status, json!({"detail":message}), head, cors)
}

fn local_origin(origin: &str) -> bool {
    let Some(host) = origin.strip_prefix("http://") else {
        return false;
    };
    if host == "localhost" || host == "127.0.0.1" {
        return true;
    }
    let Some((host, port)) = host.split_once(':') else {
        return false;
    };
    (host == "localhost" || host == "127.0.0.1")
        && !port.is_empty()
        && port.bytes().all(|b| b.is_ascii_digit())
}

async fn handle(State(s): State<Arc<AppState>>, request: Request) -> Response {
    let (parts, body) = request.into_parts();
    let method = parts.method.as_str();
    let decoded_path = path_decode(parts.uri.path());
    let path = decoded_path.as_str();
    let head = method == "HEAD";
    let mut cors = HeaderMap::new();
    let header_bytes = parts.uri.to_string().len()
        + parts
            .headers
            .iter()
            .map(|(k, v)| k.as_str().len() + v.len() + 4)
            .sum::<usize>();
    if header_bytes > 16 * 1024 {
        return error(431, "Request Header Fields Too Large", head, &cors);
    }
    if parts
        .headers
        .get("content-length")
        .and_then(|v| v.to_str().ok())
        .and_then(|v| v.parse::<u64>().ok())
        .is_some_and(|n| n > MAX_REQUEST_BYTES as u64)
    {
        return error(413, "Request body too large", head, &cors);
    }
    let raw = match tokio::time::timeout(Duration::from_secs(15), to_bytes(body, MAX_REQUEST_BYTES))
        .await
    {
        Ok(Ok(v)) => v,
        Ok(Err(_)) => return error(413, "Request body too large", head, &cors),
        Err(_) => return error(400, "Request body unreadable", head, &cors),
    };
    if path.starts_with("/api/wordgames/")
        || path.starts_with("/api/alchimie/")
        || s.upstream.is_none()
    {
        cors.insert("vary", HeaderValue::from_static("origin"));
        if let Some(origin) = parts
            .headers
            .get("origin")
            .filter(|v| v.to_str().is_ok_and(local_origin))
        {
            cors.insert("access-control-allow-origin", origin.clone());
            cors.insert(
                "access-control-allow-credentials",
                HeaderValue::from_static("true"),
            );
            if method == "OPTIONS"
                && parts
                    .headers
                    .get("access-control-request-method")
                    .is_some_and(|v| !v.is_empty())
            {
                let mut response = Response::builder()
                    .status(200)
                    .header("content-length", "0")
                    .body(Body::empty())
                    .unwrap();
                cors.insert("access-control-allow-headers",HeaderValue::from_static("accept, authorization, content-type, user-agent, x-csrftoken, x-requested-with"));
                cors.insert(
                    "access-control-allow-methods",
                    HeaderValue::from_static("DELETE, GET, OPTIONS, PATCH, POST, PUT"),
                );
                cors.insert("access-control-max-age", HeaderValue::from_static("86400"));
                response.headers_mut().extend(cors);
                return response;
            }
        }
    }
    if path == "/healthz" {
        return reply(200, json!({"ok":true}), head, &cors);
    }
    if !path.starts_with("/api/wordgames/intrusul") {
        if path.starts_with("/api/wordgames/") || path.starts_with("/api/alchimie/") {
            let state = s.clone();
            let method = method.to_owned();
            let path = path.to_owned();
            let query = parts.uri.query().unwrap_or("").to_owned();
            let raw = raw.clone();
            match tokio::task::spawn_blocking(move || {
                state.arcade.handle(&method, &path, &query, &raw)
            })
            .await
            {
                Ok(Some(Ok(body))) => return reply(200, body, head, &cors),
                Ok(Some(Err(e))) => {
                    return reply(e.status, json!({"detail":e.detail}), head, &cors);
                }
                Ok(None) => {}
                Err(_) => return error(500, "Internal Server Error", head, &cors),
            }
        }
        if let Some(mut response) =
            crate::website::handle(method, path, &parts.headers, &s.content, &s.static_root)
        {
            for (name, value) in &cors {
                if name == "vary" {
                    response.headers_mut().append(name, value.clone());
                } else {
                    response.headers_mut().insert(name, value.clone());
                }
            }
            response.headers_mut().insert(
                "x-content-type-options",
                HeaderValue::from_static("nosniff"),
            );
            response
                .headers_mut()
                .insert("referrer-policy", HeaderValue::from_static("same-origin"));
            response
                .headers_mut()
                .insert("x-frame-options", HeaderValue::from_static("DENY"));
            return response;
        }
        if let Some(upstream) = &s.upstream {
            let url = format!(
                "{upstream}{}",
                parts.uri.path_and_query().map_or("/", |v| v.as_str())
            );
            let client = s.client.as_ref().expect("upstream client");
            let mut forwarded = parts.headers.clone();
            strip_connection_headers(&mut forwarded);
            for name in [
                "connection",
                "transfer-encoding",
                "upgrade",
                "keep-alive",
                "proxy-authorization",
                "proxy-authenticate",
                "te",
                "trailer",
            ] {
                forwarded.remove(name);
            }
            let response = client
                .request(parts.method.clone(), url)
                .headers(forwarded)
                .body(raw)
                .send()
                .await;
            return match response {
                Ok(response) => {
                    let status = response.status();
                    let mut headers = response.headers().clone();
                    strip_connection_headers(&mut headers);
                    for name in [
                        "connection",
                        "transfer-encoding",
                        "upgrade",
                        "keep-alive",
                        "te",
                        "trailer",
                    ] {
                        headers.remove(name);
                    }
                    let mut result = Response::new(Body::from_stream(response.bytes_stream()));
                    *result.status_mut() = status;
                    *result.headers_mut() = headers;
                    result
                }
                Err(_) => error(503, "Python backend unavailable", head, &cors),
            };
        }
        return error(404, "Not Found", head, &cors);
    }
    let method = method.to_owned();
    let path = path.to_owned();
    let query = parts.uri.query().unwrap_or("").to_owned();
    let fallback_cors = cors.clone();
    match tokio::task::spawn_blocking(move || native(&s, &method, &path, &query, &raw, head, &cors))
        .await
    {
        Ok(response) => response,
        Err(_) => error(500, "Internal Server Error", head, &fallback_cors),
    }
}

fn native(
    s: &AppState,
    method: &str,
    path: &str,
    query: &str,
    raw: &[u8],
    head: bool,
    cors: &HeaderMap,
) -> Response {
    let result: Result<Value, ApiError> = if path == PREFIX {
        if method != "POST" {
            return error(405, "Method Not Allowed", head, cors);
        }
        let q = query_values(query);
        let seed = match query_int(&q, "seed") {
            Ok(v) => v,
            Err(e) => return reply(e.status, json!({"detail":e.detail}), head, cors),
        };
        let starter = match query_int(&q, "starter") {
            Ok(v) => v,
            Err(e) => return reply(e.status, json!({"detail":e.detail}), head, cors),
        };
        let category = last(&q, "category");
        if q.contains_key("category") && !s.content.category_labels.contains_key(category) {
            return error(400, "Categorie necunoscută.", head, cors);
        }
        if starter.as_deref().is_some_and(|v| v != "0" && v != "1") {
            return error(400, "starter trebuie să fie 0 sau 1.", head, cors);
        }
        s.game.create(
            seed.as_deref(),
            last(&q, "daily"),
            category,
            last(&q, "previous_game_id"),
            starter.as_deref() == Some("1"),
        )
    } else {
        let Some(rest) = path.strip_prefix(&format!("{PREFIX}/")) else {
            return error(404, "Not Found", head, cors);
        };
        let segments: Vec<_> = rest.split('/').collect();
        if segments[0].is_empty()
            || segments.len() > 2
            || (segments.len() == 2 && !["guess", "hint"].contains(&segments[1]))
        {
            return error(404, "Not Found", head, cors);
        }
        if segments.len() == 1 {
            if method != "GET" && !head {
                return error(405, "Method Not Allowed", head, cors);
            }
            s.game.get(segments[0])
        } else {
            if method != "POST" {
                return error(405, "Method Not Allowed", head, cors);
            }
            if segments[1] == "hint" {
                s.game.hint(segments[0])
            } else {
                s.game.guess_input(segments[0], || guess_id(raw))
            }
        }
    };
    match result {
        Ok(body) => reply(200, body, head, cors),
        Err(e) => reply(e.status, json!({"detail":e.detail}), head, cors),
    }
}

fn strip_connection_headers(headers: &mut HeaderMap) {
    let names: Vec<_> = headers
        .get_all("connection")
        .iter()
        .filter_map(|v| v.to_str().ok())
        .flat_map(|v| v.split(','))
        .filter_map(|v| http::header::HeaderName::from_bytes(v.trim().as_bytes()).ok())
        .collect();
    for name in names {
        headers.remove(name);
    }
}

fn path_decode(raw: &str) -> String {
    let bytes = raw.as_bytes();
    let mut decoded = Vec::new();
    let mut i = 0;
    while i < bytes.len() {
        if bytes[i] == b'%' && i + 2 < bytes.len() {
            let hex = |b: u8| match b {
                b'0'..=b'9' => Some(b - b'0'),
                b'a'..=b'f' => Some(b - b'a' + 10),
                b'A'..=b'F' => Some(b - b'A' + 10),
                _ => None,
            };
            if let (Some(h), Some(l)) = (hex(bytes[i + 1]), hex(bytes[i + 2])) {
                decoded.push(h * 16 + l);
                i += 3;
                continue;
            }
        }
        decoded.push(bytes[i]);
        i += 1;
    }
    String::from_utf8_lossy(&decoded).into_owned()
}

fn json_depth(raw: &[u8]) -> usize {
    let (mut quoted, mut escape, mut depth, mut maximum) = (false, false, 0usize, 0usize);
    for &b in raw {
        if escape {
            escape = false;
            continue;
        }
        if quoted && b == b'\\' {
            escape = true;
            continue;
        }
        if b == b'"' {
            quoted = !quoted;
            continue;
        }
        if !quoted {
            match b {
                b'[' | b'{' => {
                    depth += 1;
                    maximum = maximum.max(depth)
                }
                b']' | b'}' => depth = depth.saturating_sub(1),
                _ => {}
            }
        }
    }
    maximum
}

pub fn py_space(c: char) -> bool {
    matches!(c,'\u{9}'..='\u{d}'|'\u{1c}'..='\u{20}'|'\u{85}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}')
}

pub fn last<'a>(q: &'a BTreeMap<String, Vec<String>>, key: &str) -> &'a str {
    q.get(key).and_then(|v| v.last()).map_or("", String::as_str)
}

pub fn query_values(raw: &str) -> BTreeMap<String, Vec<String>> {
    fn decode(s: &str) -> String {
        fn hex(b: u8) -> Option<u8> {
            match b {
                b'0'..=b'9' => Some(b - b'0'),
                b'a'..=b'f' => Some(b - b'a' + 10),
                b'A'..=b'F' => Some(b - b'A' + 10),
                _ => None,
            }
        }
        let bytes = s.as_bytes();
        let mut result = Vec::new();
        let mut i = 0;
        while i < bytes.len() {
            match bytes[i] {
                b'+' => result.push(b' '),
                b'%' if i + 2 < bytes.len() => {
                    if let (Some(high), Some(low)) = (hex(bytes[i + 1]), hex(bytes[i + 2])) {
                        result.push(high * 16 + low);
                        i += 2;
                    } else {
                        result.push(b'%');
                    }
                }
                c => result.push(c),
            };
            i += 1;
        }
        String::from_utf8_lossy(&result).into_owned()
    }
    let mut result: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for part in raw.split('&').filter(|s| !s.is_empty()) {
        let (k, v) = part.split_once('=').unwrap_or((part, ""));
        result.entry(decode(k)).or_default().push(decode(v));
    }
    result
}

fn decimal(c: char) -> Option<u8> {
    static ZEROS: OnceLock<Vec<u32>> = OnceLock::new();
    let zeros = ZEROS.get_or_init(|| {
        let table = DECIMAL_SOURCE
            .split("var decimalZeros = [...]rune{")
            .nth(1)
            .expect("frozen decimal table")
            .split('}')
            .next()
            .unwrap();
        table
            .split(',')
            .filter_map(|s| u32::from_str_radix(s.trim().strip_prefix("0x")?, 16).ok())
            .collect()
    });
    let index = zeros.partition_point(|v| *v <= c as u32);
    index.checked_sub(1).and_then(|i| {
        let value = c as u32 - zeros[i];
        (value < 10).then_some(value as u8)
    })
}

pub fn query_int(q: &BTreeMap<String, Vec<String>>, key: &str) -> Result<Option<String>, ApiError> {
    if !q.contains_key(key) {
        return Ok(None);
    }
    let raw = last(q, key);
    let invalid = || ApiError {
        status: 422,
        detail: json!([{"type":"int_parsing","loc":["query",key],"msg":"Input should be a valid integer, unable to parse string as an integer","input":raw}]),
    };
    let chars: Vec<_> = raw
        .trim_matches(|c| py_space(c) && !('\u{1c}'..='\u{1f}').contains(&c))
        .chars()
        .collect();
    let mut text = String::new();
    let mut count = 0;
    for (i, c) in chars.iter().copied().enumerate() {
        if i == 0 && (c == '+' || c == '-') {
            text.push(c);
            continue;
        }
        if c == '_' {
            if i == 0
                || i + 1 == chars.len()
                || decimal(chars[i - 1]).is_none()
                || decimal(chars[i + 1]).is_none()
            {
                return Err(invalid());
            };
            continue;
        }
        let digit = decimal(c).ok_or_else(invalid)?;
        text.push((b'0' + digit) as char);
        count += 1;
    }
    if count == 0 || count > 4300 {
        return Err(invalid());
    }
    let number = BigInt::parse_bytes(text.as_bytes(), 10).ok_or_else(invalid)?;
    Ok(Some(number.to_string()))
}

fn guess_id(raw: &[u8]) -> Result<String, ApiError> {
    let value: Value = if raw.iter().all(|b| b.is_ascii_whitespace()) {
        Value::Null
    } else {
        if json_depth(raw) > 1024 {
            return Err(ApiError::new(422, "JSON nesting limit exceeded"));
        }
        parse_json(raw)
            .map_err(|e|ApiError{status:422,detail:json!([{"type":"json_invalid","loc":["body"],"msg":"JSON decode error","input":{},"ctx":{"error":json_message(raw,&e)}}])})?
    };
    let Some(object) = value.as_object() else {
        return Err(ApiError {
            status: 422,
            detail: json!([{"type":"model_type","loc":["body"],"msg":"Input should be a valid dictionary or instance of GuessBody","input":value,"ctx":{"class_name":"GuessBody"}}]),
        });
    };
    let Some(id) = object.get("id") else {
        return Err(ApiError {
            status: 422,
            detail: json!([{"type":"missing","loc":["body","id"],"msg":"Field required","input":value}]),
        });
    };
    let Some(id) = id.as_str() else {
        return Err(ApiError {
            status: 422,
            detail: json!([{"type":"string_type","loc":["body","id"],"msg":"Input should be a valid string","input":id}]),
        });
    };
    Ok(id.trim_matches(py_space).to_owned())
}

pub fn parse_json(raw: &[u8]) -> Result<Value, serde_json::Error> {
    let mut parser = serde_json::Deserializer::from_slice(raw);
    parser.disable_recursion_limit();
    let value = Value::deserialize(serde_stacker::Deserializer::new(&mut parser))?;
    parser.end()?;
    Ok(value)
}

pub fn encode_json(value: &Value) -> Result<Vec<u8>, serde_json::Error> {
    let mut output = Vec::new();
    let mut serializer = serde_json::Serializer::new(&mut output);
    value.serialize(serde_stacker::Serializer::new(&mut serializer))?;
    Ok(output)
}

pub fn json_message(raw: &[u8], e: &serde_json::Error) -> &'static str {
    let message = e.to_string();
    if message.contains("trailing characters") {
        return "Extra data";
    }
    if message.contains("key must be a string")
        || message.contains("trailing comma")
            && raw.iter().rev().find(|b| !b.is_ascii_whitespace()) == Some(&b'}')
    {
        return "Expecting property name enclosed in double quotes";
    }
    if message.contains("expected `:`") {
        return "Expecting ':' delimiter";
    }
    if message.contains("expected `,` or `}`") || message.contains("expected `,` or `]`") {
        return "Expecting ',' delimiter";
    }
    if message.contains("invalid escape") {
        return "Invalid \\escape";
    }
    if message.contains("invalid unicode") {
        return "Invalid \\uXXXX escape";
    }
    if message.contains("control character") {
        return "Invalid control character at";
    }
    if e.is_eof() {
        let mut quoted = false;
        let mut escape = false;
        let mut previous = 0;
        let mut last_key = false;
        let mut stack = Vec::new();
        for &c in raw {
            if escape {
                escape = false;
                continue;
            }
            if quoted && c == b'\\' {
                escape = true;
                continue;
            }
            if c == b'"' {
                if !quoted {
                    last_key = stack.last() == Some(&b'{') && b"{,".contains(&previous)
                }
                quoted = !quoted;
                if !quoted {
                    previous = b'"'
                };
                continue;
            }
            if !quoted {
                if b"{[".contains(&c) {
                    stack.push(c)
                }
                if b"}]".contains(&c) {
                    stack.pop();
                }
                if !c.is_ascii_whitespace() {
                    previous = c
                }
            }
        }
        if quoted {
            return "Unterminated string starting at";
        }
        return match previous {
            b'{' => "Expecting property name enclosed in double quotes",
            b',' if stack.last() == Some(&b'{') => {
                "Expecting property name enclosed in double quotes"
            }
            b':' | b'[' | b',' => "Expecting value",
            b'"' if last_key => "Expecting ':' delimiter",
            _ => "Expecting ',' delimiter",
        };
    }
    "Expecting value"
}

pub fn validate_upstream(raw: &str) -> Result<String, String> {
    let url = reqwest::Url::parse(raw).map_err(|e| e.to_string())?;
    let ip = url
        .host_str()
        .and_then(|s| s.trim_matches(['[', ']']).parse::<std::net::IpAddr>().ok());
    if url.scheme() != "http"
        || ip.is_none_or(|ip| !ip.is_loopback())
        || !url.username().is_empty()
        || url.password().is_some()
        || url.query().is_some()
        || url.fragment().is_some()
        || url.path() != "/"
    {
        return Err(
            "Python upstream must be numeric loopback HTTP without credentials/path/query".into(),
        );
    }
    Ok(raw.trim_end_matches('/').to_owned())
}

pub async fn check_upstream(upstream: &str, c: &Content) -> Result<(), String> {
    let client = reqwest::Client::builder()
        .no_proxy()
        .timeout(Duration::from_secs(5))
        .redirect(reqwest::redirect::Policy::none())
        .build()
        .map_err(|e| e.to_string())?;
    for path in ["/api/me", "/api/manifest"] {
        let mut response = client
            .get(format!("{upstream}{path}"))
            .send()
            .await
            .map_err(|e| e.to_string())?;
        if response.status() != StatusCode::OK {
            return Err("anonymous upstream probe failed".into());
        }
        let mut bytes = Vec::new();
        while let Some(chunk) = response.chunk().await.map_err(|e| e.to_string())? {
            if bytes.len() + chunk.len() > MAX_REQUEST_BYTES {
                return Err("upstream metadata too large".into());
            }
            bytes.extend_from_slice(&chunk);
        }
        let body: Value = serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
        if path == "/api/me" {
            if body["accounts_enabled"] != false
                || body["authenticated"] != false
                || !body["user"].is_null()
            {
                return Err("Rust backend refuses an accounts-enabled upstream".into());
            }
        } else if body["content_hash"] != c.manifest["content_hash"]
            || body["build_version"] != c.manifest["build_version"]
        {
            return Err("Python upstream content differs from native export".into());
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;
    use tower::ServiceExt;
    #[test]
    fn query_contract() {
        for (raw, valid) in [
            ("seed=١٢٣", true),
            ("seed=1_234", true),
            ("seed=%zz", false),
            ("seed=1;category=x", false),
            ("seed=𑯱", false),
        ] {
            assert_eq!(
                query_int(&query_values(raw), "seed").is_ok(),
                valid,
                "{raw}"
            );
        }
        assert_eq!(last(&query_values("seed=%ff%ff"), "seed"), "��");
        assert!(validate_upstream("http://127.0.0.1:8000").is_ok());
        assert!(validate_upstream("http://example.com").is_err());
    }
    #[tokio::test]
    async fn bounded_transport_and_cors() {
        let app = router(Arc::new(Content::load().unwrap()), None).unwrap();
        let response = app
            .clone()
            .oneshot(
                http::Request::builder()
                    .method("POST")
                    .uri(PREFIX)
                    .body(Body::from(vec![b' '; MAX_REQUEST_BYTES + 1]))
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), 413);
        let response = app
            .oneshot(
                http::Request::builder()
                    .method("OPTIONS")
                    .uri(PREFIX)
                    .header("Origin", "http://localhost:5173")
                    .header("Access-Control-Request-Method", "POST")
                    .body(Body::empty())
                    .unwrap(),
            )
            .await
            .unwrap();
        assert_eq!(response.status(), 200);
        assert_eq!(
            response.headers()["access-control-allow-origin"],
            "http://localhost:5173"
        );
    }
}
