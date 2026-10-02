//! Anonymous metadata, configured legal notices and the unchanged SPA assets.
use crate::content::Content;
use axum::{body::Body, response::Response};
use http::{HeaderMap, HeaderValue};
use serde_json::{Value, json};
use std::{
    fs,
    path::{Path, PathBuf},
    time::UNIX_EPOCH,
};

#[derive(Default)]
struct Settings {
    operator: String,
    contact: String,
    donate: String,
    consent_version: String,
}
impl Settings {
    fn environment() -> Self {
        let trimmed = |name| {
            std::env::var(name)
                .unwrap_or_default()
                .trim_matches(crate::httpapi::py_space)
                .to_owned()
        };
        Self {
            operator: trimmed("CAT_LEGAL_OPERATOR"),
            contact: trimmed("CAT_LEGAL_CONTACT_EMAIL"),
            donate: trimmed("CAT_DONATE_URL"),
            consent_version: std::env::var("CAT_CONSENT_VERSION")
                .unwrap_or_else(|_| "2026-07-09".into()),
        }
    }
}
fn django_escape(value: &str) -> String {
    let mut out = String::new();
    for c in value.chars() {
        match c {
            '&' => out.push_str("&amp;"),
            '<' => out.push_str("&lt;"),
            '>' => out.push_str("&gt;"),
            '"' => out.push_str("&quot;"),
            '\'' => out.push_str("&#x27;"),
            c => out.push(c),
        }
    }
    out
}
fn replace_slot(mut text: String, start: &str, end: &str, replacement: &str) -> String {
    if let Some(first) = text.find(start)
        && let Some(last) = text[first + start.len()..].find(end)
    {
        let last = first + start.len() + last + end.len();
        text.replace_range(first..last, replacement)
    };
    text
}
fn render_legal(base: &str, s: &Settings) -> String {
    let mut body = replace_slot(
        base.into(),
        "Operatorul serviciului este <strong>",
        "</strong>. ",
        "",
    );
    body = replace_slot(
        body,
        "<a href=\"mailto:",
        "</a>",
        "<code>[[PLACEHOLDER: contact]]</code>",
    );
    let mut draft="<div class=\"draft\"><strong>DRAFT — text în lucru.</strong> Acest document trebuie completat și verificat de un avocat specializat în protecția datelor înainte de publicare.".to_owned();
    if s.operator.is_empty() || s.contact.is_empty() {
        draft.push_str(" Operatorul și datele de contact nu sunt încă finalizate.")
    };
    draft.push_str("</div>");
    body = replace_slot(body, "<div class=\"draft\">", "</div>", &draft);
    if !s.operator.is_empty() {
        body=body.replace("Pentru orice cerere sau plângere:",&format!("Operatorul serviciului este <strong>{}</strong>. Pentru orice cerere sau plângere:",django_escape(&s.operator)))
    };
    if !s.contact.is_empty() {
        let safe = django_escape(&s.contact);
        body = body.replace(
            "<code>[[PLACEHOLDER: contact]]</code>",
            &format!("<a href=\"mailto:{safe}\">{safe}</a>"),
        )
    };
    body = replace_slot(
        body,
        "<p class='draft'>Versiune schiță: <code>",
        "</code></p>",
        "",
    );
    if !s.consent_version.is_empty() {
        body = body.replacen(
            "\n<footer>",
            &format!(
                "<p class='draft'>Versiune schiță: <code>{}</code></p>\n<footer>",
                s.consent_version
            ),
            1,
        )
    };
    body
}
pub fn default_static_root() -> PathBuf {
    let cwd = std::env::current_dir().unwrap_or_default();
    for root in [
        Some(cwd.as_path()),
        cwd.parent(),
        cwd.parent().and_then(Path::parent),
    ]
    .into_iter()
    .flatten()
    {
        let p = root.join("cat_de_roman_esti/web/static");
        if p.join("index.html").is_file() {
            return p;
        }
    }
    PathBuf::from("cat_de_roman_esti/web/static")
}
fn bytes_response(status: u16, kind: Option<&str>, data: Vec<u8>, head: bool) -> Response {
    let mut builder = Response::builder()
        .status(status)
        .header("content-length", data.len().to_string());
    if let Some(kind) = kind {
        builder = builder.header("content-type", kind)
    };
    builder
        .body(if head {
            Body::empty()
        } else {
            Body::from(data)
        })
        .unwrap()
}
fn json_response(status: u16, value: &Value, head: bool) -> Response {
    bytes_response(
        status,
        Some("application/json"),
        crate::httpapi::encode_json(value).unwrap(),
        head,
    )
}
fn static_file(root: &Path, path: &str) -> Option<(PathBuf, fs::Metadata)> {
    let relative = if path == "/" {
        "index.html"
    } else {
        path.strip_prefix('/')?
    };
    if relative.is_empty()
        || relative.starts_with('/')
        || relative.contains('\\')
        || relative.contains("//")
        || relative.split('/').any(|part| matches!(part, "." | ".."))
    {
        return None;
    };
    let canonical = fs::canonicalize(root.join(relative)).ok()?;
    let canonical_root = fs::canonicalize(root).ok()?;
    if !canonical.starts_with(canonical_root) {
        return None;
    };
    let metadata = fs::metadata(&canonical).ok()?;
    metadata.is_file().then_some((canonical, metadata))
}
fn immutable(path: &str) -> bool {
    if !path.starts_with("/assets/") {
        return false;
    };
    let Some((stem, extension)) = path.rsplit_once('.') else {
        return false;
    };
    if !["css", "js", "woff", "woff2"].contains(&extension) {
        return false;
    };
    let bytes = stem.as_bytes();
    bytes.len() > 17
        && bytes[bytes.len() - 9] == b'-'
        && bytes[bytes.len() - 8..]
            .iter()
            .all(|c| c.is_ascii_alphanumeric() || *c == b'_' || *c == b'-')
}
fn media_type(path: &str) -> &'static str {
    match path.rsplit_once('.').map(|(_, ext)| ext) {
        Some("html") => "text/html; charset=\"utf-8\"",
        Some("js" | "mjs") => "text/javascript; charset=\"utf-8\"",
        Some("css") => "text/css; charset=\"utf-8\"",
        Some("json") => "application/json",
        Some("svg") => "image/svg+xml",
        Some("png") => "image/png",
        Some("ico") => "image/vnd.microsoft.icon",
        Some("woff") => "font/woff",
        Some("woff2") => "font/woff2",
        _ => "application/octet-stream",
    }
}
fn byte_range(header: &str, size: usize) -> Option<Result<(usize, usize), ()>> {
    let value = header.strip_prefix("bytes=")?;
    if value.contains(',') {
        return None;
    };
    let (left, right) = value.split_once('-')?;
    let (start, end) = if left.is_empty() {
        let suffix = right.trim().parse::<usize>().ok()?;
        (size.saturating_sub(suffix), size.saturating_sub(1))
    } else {
        let start = left.trim().parse::<usize>().ok()?;
        let end = if right.is_empty() {
            size.saturating_sub(1)
        } else {
            right
                .trim()
                .parse::<usize>()
                .ok()?
                .min(size.saturating_sub(1))
        };
        (start, end)
    };
    Some(if start >= size || end < start {
        Err(())
    } else {
        Ok((start, end))
    })
}
fn static_response(
    method: &str,
    path: &str,
    headers: &HeaderMap,
    file: &Path,
    metadata: &fs::Metadata,
) -> Response {
    let type_path = if path.ends_with('/') {
        "index.html"
    } else {
        path
    };
    let head = method == "HEAD";
    if method != "GET" && !head {
        let mut r = bytes_response(405, None, vec![], head);
        r.headers_mut()
            .insert("allow", HeaderValue::from_static("GET, HEAD"));
        return r;
    };
    let modified = metadata.modified().unwrap_or(UNIX_EPOCH);
    let seconds = modified
        .duration_since(UNIX_EPOCH)
        .unwrap_or_default()
        .as_secs();
    let tag = format!("\"{seconds:x}-{:x}\"", metadata.len());
    let cache = if immutable(path) {
        "max-age=315360000, public, immutable"
    } else {
        "max-age=0, public"
    };
    let fresh = if let Some(value) = headers.get("if-none-match") {
        value.to_str().ok() == Some(&tag)
    } else {
        headers
            .get("if-modified-since")
            .and_then(|v| v.to_str().ok())
            .and_then(|v| httpdate::parse_http_date(v).ok())
            .is_some_and(|date| {
                date.duration_since(UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_secs()
                    >= seconds
            })
    };
    let mut r = if fresh {
        Response::builder().status(304).body(Body::empty()).unwrap()
    } else {
        match fs::read(file) {
            Ok(data) => {
                let range = headers
                    .get("range")
                    .and_then(|v| v.to_str().ok())
                    .and_then(|v| byte_range(v, data.len()));
                match range {
                    Some(Err(())) => {
                        let mut r = bytes_response(416, Some(media_type(type_path)), vec![], head);
                        r.headers_mut().insert(
                            "content-range",
                            HeaderValue::from_str(&format!("bytes */{}", data.len())).unwrap(),
                        );
                        r
                    }
                    Some(Ok((start, end))) => {
                        let mut r = bytes_response(
                            206,
                            Some(media_type(type_path)),
                            data[start..=end].to_vec(),
                            head,
                        );
                        r.headers_mut().insert(
                            "content-range",
                            HeaderValue::from_str(&format!("bytes {start}-{end}/{}", data.len()))
                                .unwrap(),
                        );
                        r
                    }
                    None => bytes_response(200, Some(media_type(type_path)), data, head),
                }
            }
            Err(_) => bytes_response(404, Some("text/html; charset=utf-8"), vec![], head),
        }
    };
    r.headers_mut()
        .insert("cache-control", HeaderValue::from_static(cache));
    r.headers_mut()
        .insert("etag", HeaderValue::from_str(&tag).unwrap());
    if !fresh {
        r.headers_mut().insert(
            "last-modified",
            HeaderValue::from_str(&httpdate::fmt_http_date(modified)).unwrap(),
        );
        r.headers_mut()
            .insert("accept-ranges", HeaderValue::from_static("bytes"));
    };
    r
}
fn redirect(path: &str) -> Response {
    let mut r = Response::builder()
        .status(302)
        .header("cache-control", "max-age=0, public")
        .body(Body::empty())
        .unwrap();
    let escaped = path.bytes().fold(String::new(), |mut out, b| {
        if b.is_ascii_alphanumeric() || b"/-._~".contains(&b) {
            out.push(char::from(b))
        } else {
            out.push_str(&format!("%{b:02X}"))
        };
        out
    });
    r.headers_mut()
        .insert("location", HeaderValue::from_str(&escaped).unwrap());
    r
}
pub fn handle(
    method: &str,
    path: &str,
    headers: &HeaderMap,
    c: &Content,
    root: &Path,
) -> Option<Response> {
    handle_config(method, path, headers, c, root, &Settings::environment())
}
fn handle_config(
    method: &str,
    path: &str,
    headers: &HeaderMap,
    c: &Content,
    root: &Path,
    settings: &Settings,
) -> Option<Response> {
    let head = method == "HEAD";
    match path {
        "/api/health" | "/api/categories" | "/api/manifest" => {
            let mut r = if method != "GET" && !head {
                json_response(405, &json!({"detail":"Method Not Allowed"}), head)
            } else {
                json_response(
                    200,
                    if path == "/api/manifest" {
                        &c.manifest
                    } else {
                        &c.metadata[path]
                    },
                    head,
                )
            };
            r.headers_mut()
                .insert("allow", HeaderValue::from_static("GET, HEAD, OPTIONS"));
            return Some(r);
        }
        "/api/me" => {
            return Some(json_response(
                200,
                &json!({"accounts_enabled":false,"authenticated":false,"user":null,"donate_url":settings.donate}),
                head,
            ));
        }
        "/openapi.json" => {
            let kind = if headers
                .get("accept")
                .and_then(|v| v.to_str().ok())
                .is_some_and(|v| {
                    v.contains("application/json")
                        && !v.contains("application/vnd.oai.openapi+json")
                }) {
                "application/json"
            } else {
                "application/vnd.oai.openapi+json"
            };
            let mut r = if method == "OPTIONS" {
                json_response(
                    200,
                    &json!({"name":"Spectacular Jsonapi","description":"","renders":["application/vnd.oai.openapi+json","application/json"],"parses":["application/json"]}),
                    head,
                )
            } else if method != "GET" && !head {
                json_response(
                    405,
                    &json!({"detail":format!("Method \"{method}\" not allowed.")}),
                    head,
                )
            } else {
                let mut r = json_response(200, &c.metadata["openapi"], head);
                r.headers_mut().insert(
                    "content-disposition",
                    HeaderValue::from_static("inline; filename=\"cat_de_roman_esti.json\""),
                );
                r
            };
            r.headers_mut()
                .insert("content-type", HeaderValue::from_static(kind));
            r.headers_mut()
                .insert("allow", HeaderValue::from_static("GET, HEAD, OPTIONS"));
            r.headers_mut()
                .insert("vary", HeaderValue::from_static("Accept"));
            return Some(r);
        }
        "/api/submissions" => {
            let mut r = json_response(
                if method == "POST" { 503 } else { 405 },
                &json!({"detail":if method=="POST"{"Trimiterea de jocuri nu este activata pe acest server."}else{"Method Not Allowed"}}),
                head,
            );
            r.headers_mut()
                .insert("allow", HeaderValue::from_static("POST, OPTIONS"));
            return Some(r);
        }
        "/legal/privacy" | "/legal/terms" => {
            let key = if path == "/legal/privacy" {
                "privacy_html"
            } else {
                "terms_html"
            };
            return Some(bytes_response(
                200,
                Some("text/html; charset=utf-8"),
                render_legal(c.metadata[key].as_str().unwrap_or(""), settings).into_bytes(),
                head,
            ));
        }
        _ => {}
    };
    if path.starts_with("/api/") {
        return None;
    };
    if let Some((file, metadata)) = static_file(root, path) {
        return Some(if path.ends_with("/index.html") {
            redirect(path.strip_suffix("index.html").unwrap())
        } else {
            static_response(method, path, headers, &file, &metadata)
        });
    };
    if path != "/"
        && !path.ends_with('/')
        && static_file(root, &format!("{path}/index.html")).is_some()
    {
        return Some(redirect(&format!("{path}/")));
    };
    if path != "/"
        && path.ends_with('/')
        && let Some((file, metadata)) = static_file(root, &format!("{path}index.html"))
    {
        return Some(static_response(method, path, headers, &file, &metadata));
    };
    if path.starts_with("/assets/") {
        return Some(bytes_response(
            404,
            Some("text/html; charset=utf-8"),
            vec![],
            head,
        ));
    };
    if let Ok(index) = fs::read(root.join("index.html")) {
        let mut r = bytes_response(200, Some("text/html; charset=utf-8"), index, head);
        r.headers_mut()
            .insert("cache-control", HeaderValue::from_static("no-cache"));
        return Some(r);
    };
    if path == "/" || path.is_empty() {
        return Some(bytes_response(
            200,
            Some("text/html; charset=utf-8"),
            MISSING_BUILD_HTML.as_bytes().to_vec(),
            head,
        ));
    };
    Some(json_response(404, &json!({"detail":"Not Found"}), head))
}

const MISSING_BUILD_HTML: &str = r##"<!doctype html>
<html lang="ro">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>cat_de_roman_esti</title>
  <style>
    body { margin:0; min-height:100vh; display:flex; align-items:center;
      justify-content:center; font-family: system-ui, sans-serif; color:#e8e8f0;
      background: radial-gradient(1200px 800px at 30% 20%, #1b2350, #0a0d1f 70%); }
    .card { max-width: 34rem; padding: 2rem 2.5rem; border-radius: 18px;
      background: rgba(255,255,255,0.04); border:1px solid rgba(255,255,255,0.08);
      box-shadow: 0 20px 60px rgba(0,0,0,0.5); }
    h1 { margin:0 0 .5rem; font-size:1.6rem;
      background: linear-gradient(90deg,#ffd166,#ef476f,#118ab2);
      -webkit-background-clip:text; background-clip:text; color:transparent; }
    code { background: rgba(255,255,255,0.08); padding:.15rem .4rem; border-radius:6px; }
    a { color:#84d6ff; }
    p { line-height:1.55; }
  </style>
</head>
<body>
  <div class="card">
    <h1>cat_de_roman_esti</h1>
    <p>The API is live, but the front-end build is missing.</p>
    <p>Build the SPA to play the word-game arcade:</p>
    <p><code>cd frontend &amp;&amp; npm install &amp;&amp; npm run build</code></p>
    <p>The API is at <a href="/api/health">/api/health</a>.</p>
  </div>
</body>
</html>
"##;

#[cfg(test)]
mod tests {
    use super::*;
    use axum::body::to_bytes;
    use sha2::{Digest, Sha256};
    use std::time::{Duration, SystemTime};
    fn content() -> Content {
        Content::load().unwrap()
    }
    async fn body(response: Response) -> Vec<u8> {
        to_bytes(response.into_body(), 1024 * 1024)
            .await
            .unwrap()
            .to_vec()
    }
    struct Temp(PathBuf);
    impl Temp {
        fn new() -> Self {
            let mut random = [0u8; 8];
            getrandom::fill(&mut random).unwrap();
            let suffix = u64::from_le_bytes(random);
            let p =
                std::env::temp_dir().join(format!("cat-website-{}-{suffix:x}", std::process::id()));
            fs::create_dir(&p).unwrap();
            Self(p)
        }
    }
    impl Drop for Temp {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    #[tokio::test]
    async fn legal_pages_exact_python_configurations_and_no_build_placeholder() {
        let content = content();
        let data: Value = serde_json::from_str(include_str!(
            "../../go-backend/internal/httpapi/testdata/website_python.json"
        ))
        .unwrap();
        for c in data["cases"].as_array().unwrap() {
            let settings = Settings {
                operator: c["operator"]
                    .as_str()
                    .unwrap()
                    .trim_matches(crate::httpapi::py_space)
                    .into(),
                contact: c["contact"]
                    .as_str()
                    .unwrap()
                    .trim_matches(crate::httpapi::py_space)
                    .into(),
                consent_version: c["version"].as_str().unwrap().into(),
                ..Default::default()
            };
            for (path, key) in [("/legal/privacy", "privacy"), ("/legal/terms", "terms")] {
                let r = handle_config(
                    "GET",
                    path,
                    &HeaderMap::new(),
                    &content,
                    Path::new("missing"),
                    &settings,
                )
                .unwrap();
                assert_eq!(r.status(), 200);
                assert_eq!(r.headers()["content-type"], "text/html; charset=utf-8");
                assert_eq!(
                    format!("{:x}", Sha256::digest(body(r).await)),
                    c[key].as_str().unwrap(),
                    "config{} {path}",
                    c["name"]
                );
            }
        }
        assert_eq!(
            format!("{:x}", Sha256::digest(MISSING_BUILD_HTML.as_bytes())),
            data["placeholder_sha256"].as_str().unwrap()
        );
    }
    #[tokio::test]
    async fn anonymous_donation_metadata_methods_and_submissions_disabled() {
        let c = content();
        let settings = Settings {
            donate: "https://example.org/donate".into(),
            ..Default::default()
        };
        for method in ["GET", "HEAD", "POST", "OPTIONS", "DELETE"] {
            let r = handle_config(
                method,
                "/api/me",
                &HeaderMap::new(),
                &c,
                Path::new("missing"),
                &settings,
            )
            .unwrap();
            assert_eq!(r.status(), 200);
            let data = body(r).await;
            if method == "HEAD" {
                assert!(data.is_empty())
            } else {
                let v: Value = serde_json::from_slice(&data).unwrap();
                assert_eq!(
                    v,
                    json!({"accounts_enabled":false,"authenticated":false,"user":null,"donate_url":"https://example.org/donate"})
                );
            }
        }
        for path in ["/api/health", "/api/categories", "/api/manifest"] {
            for method in ["GET", "HEAD", "POST", "OPTIONS"] {
                let r = handle_config(
                    method,
                    path,
                    &HeaderMap::new(),
                    &c,
                    Path::new("missing"),
                    &settings,
                )
                .unwrap();
                assert_eq!(
                    r.status(),
                    if ["GET", "HEAD"].contains(&method) {
                        200
                    } else {
                        405
                    }
                );
                assert_eq!(r.headers()["allow"], "GET, HEAD, OPTIONS")
            }
        }
        let r = handle_config(
            "POST",
            "/api/submissions",
            &HeaderMap::new(),
            &c,
            Path::new("missing"),
            &settings,
        )
        .unwrap();
        assert_eq!(r.status(), 503);
        let r = handle_config(
            "OPTIONS",
            "/openapi.json",
            &HeaderMap::new(),
            &c,
            Path::new("missing"),
            &settings,
        )
        .unwrap();
        assert_eq!(r.status(), 200);
        assert_eq!(
            r.headers()["content-type"],
            "application/vnd.oai.openapi+json"
        );
        assert_eq!(r.headers()["vary"], "Accept");
        let v: Value = serde_json::from_slice(&body(r).await).unwrap();
        assert_eq!(v["name"], "Spectacular Jsonapi");
    }
    #[tokio::test]
    async fn static_cache_methods_conditionals_ranges_redirect_and_spa_fallback() {
        let c = content();
        let temp = Temp::new();
        let root = &temp.0;
        fs::create_dir(root.join("assets")).unwrap();
        fs::write(root.join("index.html"), b"<main>arcade</main>").unwrap();
        let asset = "/assets/code-rz8M-4-f.js";
        let file = root.join("assets/code-rz8M-4-f.js");
        fs::write(&file, b"0123456789").unwrap();
        fs::File::options()
            .write(true)
            .open(&file)
            .unwrap()
            .set_modified(UNIX_EPOCH + Duration::from_secs(1700000000))
            .unwrap();
        let settings = Settings::default();
        let request = |method, path, headers: &HeaderMap| {
            handle_config(method, path, headers, &c, root, &settings).unwrap()
        };
        let r = request("GET", "/", &HeaderMap::new());
        assert_eq!(r.status(), 200);
        assert!(
            r.headers()["content-type"]
                .to_str()
                .unwrap()
                .starts_with("text/html")
        );
        assert_eq!(body(r).await, b"<main>arcade</main>");
        let r = request("GET", asset, &HeaderMap::new());
        assert_eq!(r.status(), 200);
        assert_eq!(r.headers()["etag"], "\"6553f100-a\"");
        assert_eq!(
            r.headers()["cache-control"],
            "max-age=315360000, public, immutable"
        );
        assert_eq!(body(r).await, b"0123456789");
        for method in ["POST", "OPTIONS"] {
            let r = request(method, asset, &HeaderMap::new());
            assert_eq!(r.status(), 405);
            assert_eq!(r.headers()["allow"], "GET, HEAD");
            assert!(body(r).await.is_empty())
        }
        let mut h = HeaderMap::new();
        h.insert("if-none-match", HeaderValue::from_static("\"6553f100-a\""));
        assert_eq!(request("GET", asset, &h).status(), 304);
        h.clear();
        h.insert(
            "if-modified-since",
            HeaderValue::from_static("Tue, 14 Nov 2023 22:13:20 GMT"),
        );
        assert_eq!(request("GET", asset, &h).status(), 304);
        h.clear();
        h.insert("range", HeaderValue::from_static("bytes=2-5"));
        let r = request("GET", asset, &h);
        assert_eq!(r.status(), 206);
        assert_eq!(r.headers()["content-range"], "bytes 2-5/10");
        assert_eq!(body(r).await, b"2345");
        h.insert("range", HeaderValue::from_static("bytes=100-"));
        assert_eq!(request("GET", asset, &h).status(), 416);
        h.insert("range", HeaderValue::from_static("bytes=0-1,5-6"));
        assert_eq!(request("GET", asset, &h).status(), 200);
        let r = request("POST", "/index.html", &HeaderMap::new());
        assert_eq!(r.status(), 302);
        assert_eq!(r.headers()["location"], "/");
        let r = request("GET", "/intrusul", &HeaderMap::new());
        assert_eq!(r.status(), 200);
        assert_eq!(r.headers()["cache-control"], "no-cache");
        assert_eq!(body(r).await, b"<main>arcade</main>");
        let r = request("GET", "/assets/missing.js", &HeaderMap::new());
        assert_eq!(r.status(), 404);
        assert!(body(r).await.is_empty());
        let missing = Temp::new();
        assert_eq!(
            handle_config("GET", "/", &HeaderMap::new(), &c, &missing.0, &settings)
                .unwrap()
                .status(),
            200
        );
        assert_eq!(
            handle_config(
                "GET",
                "/intrusul",
                &HeaderMap::new(),
                &c,
                &missing.0,
                &settings
            )
            .unwrap()
            .status(),
            404
        );
        assert!(immutable("/assets/derivedReplay-Bor7pKb-.js"));
        assert!(!immutable("/assets/image-12345678.png"));
        assert!(!immutable("/assets/code.js"));
        let _ = SystemTime::now();
    }
}
