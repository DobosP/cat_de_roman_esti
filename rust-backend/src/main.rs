use axum::body::{Body, to_bytes};
use cat_rust_server::{content::Content, httpapi};
use serde::Deserialize;
use serde_json::json;
use std::{
    collections::BTreeMap,
    io::{self, BufRead, Write},
    sync::Arc,
    time::Instant,
};
use tower::ServiceExt;

#[derive(Deserialize)]
struct Replay {
    #[serde(default)]
    method: String,
    path: String,
    #[serde(default)]
    body: String,
    #[serde(default)]
    headers: BTreeMap<String, String>,
}

fn ascii_uri(raw: &str) -> String {
    let mut result = String::new();
    for b in raw.bytes() {
        if b >= 128 {
            result.push_str(&format!("%{b:02X}"))
        } else {
            result.push(b as char)
        }
    }
    result
}

fn main() -> Result<(), Box<dyn std::error::Error>> {
    tokio::runtime::Builder::new_multi_thread()
        .worker_threads(2)
        .max_blocking_threads(2)
        .enable_all()
        .build()?
        .block_on(run())
}

async fn run() -> Result<(), Box<dyn std::error::Error>> {
    let mut listen = "127.0.0.1:8082".to_owned();
    let mut upstream = None;
    let mut replay = false;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--listen" | "-listen" => listen = args.next().ok_or("missing listen")?,
            "--python-upstream" | "-python-upstream" => {
                upstream = Some(httpapi::validate_upstream(
                    &args.next().ok_or("missing upstream")?,
                )?)
            }
            "--replay" | "-replay" => replay = true,
            "--help" | "-h" => {
                println!(
                    "cat-rust-server [--listen 127.0.0.1:8082] [--python-upstream http://127.0.0.1:8000] [--replay]"
                );
                return Ok(());
            }
            _ => return Err(format!("unknown option {arg}").into()),
        }
    }
    let accounts = std::env::var("CAT_ACCOUNTS_ENABLED").unwrap_or_default();
    if ["1", "true", "yes", "on"].contains(&accounts.trim().to_lowercase().as_str()) {
        return Err("Rust backend requires accounts OFF".into());
    }
    for name in ["CAT_KG_FIXTURE", "CAT_GAMES_PACK", "CAT_BOARD_RANKINGS"] {
        if std::env::var(name).is_ok_and(|s| !s.is_empty()) {
            return Err("Rust backend requires bundled content without source overrides".into());
        }
    }
    if std::env::var("CAT_SUBMISSIONS_DIR").is_ok_and(|s| !s.is_empty()) {
        return Err(
            "Rust backend does not support CAT_SUBMISSIONS_DIR; use Python for enabled submissions"
                .into(),
        );
    }
    if std::env::var("CAT_MAX_REQUEST_BYTES").is_ok_and(|s| !s.is_empty() && s != "65536") {
        return Err("Rust backend requires default request budget".into());
    }
    let c = Arc::new(Content::load()?);
    if let Some(upstream) = &upstream {
        if replay {
            return Err("replay is offline".into());
        }
        httpapi::check_upstream(upstream, &c).await?
    }
    let app = httpapi::router(c.clone(), upstream)?;
    if replay {
        let stdin = io::stdin();
        let mut stdout = io::BufWriter::new(io::stdout());
        for line in stdin.lock().lines() {
            let input: Replay = serde_json::from_str(&line?)?;
            let mut request = http::Request::builder()
                .method(if input.method.is_empty() {
                    "GET"
                } else {
                    &input.method
                })
                .uri(ascii_uri(&input.path));
            for (k, v) in &input.headers {
                request = request.header(k, v);
            }
            let request = request.body(Body::from(input.body))?;
            let start = Instant::now();
            let response = app.clone().oneshot(request).await?;
            let status = response.status().as_u16();
            let body = to_bytes(response.into_body(), 4 * 1024 * 1024).await?;
            let elapsed = start.elapsed().as_nanos();
            let body = if body.is_empty() {
                serde_json::Value::Null
            } else {
                httpapi::parse_json(&body)?
            };
            stdout.write_all(&httpapi::encode_json(
                &json!({"status":status,"body":body,"duration_ns":elapsed}),
            )?)?;
            stdout.write_all(b"\n")?;
            stdout.flush()?;
        }
        return Ok(());
    }
    let listener = tokio::net::TcpListener::bind(&listen).await?;
    eprintln!(
        "Rust arcade {}: all six games and exploration; listen {}",
        c.app_version,
        listener.local_addr()?
    );
    axum::serve(listener, app)
        .with_graceful_shutdown(shutdown())
        .await?;
    Ok(())
}

async fn shutdown() {
    #[cfg(unix)]
    {
        let mut term = tokio::signal::unix::signal(tokio::signal::unix::SignalKind::terminate())
            .expect("SIGTERM handler");
        tokio::select! {_=tokio::signal::ctrl_c()=>{},_=term.recv()=>{}}
    }
    #[cfg(not(unix))]
    {
        let _ = tokio::signal::ctrl_c().await;
    }
}
