//! Python-compatible deployment settings shared by every anonymous store.
use num_bigint::{BigInt, Sign};
use std::{env, sync::OnceLock};
pub const TTL_ENV: &str = "CAT_SESSION_TTL_SECONDS";
pub const CAP_ENV: &str = "CAT_MAX_SESSIONS_PER_GAME";
#[derive(Debug, PartialEq)]
pub struct Config {
    pub ttl_seconds: f64,
    pub max_sessions: usize,
}
const DECIMAL_SOURCE: &str = include_str!("../../../go-backend/internal/httpapi/decimal.go");
fn decimal(c: char) -> Option<char> {
    static ZEROS: OnceLock<Vec<u32>> = OnceLock::new();
    let zeros = ZEROS.get_or_init(|| {
        DECIMAL_SOURCE
            .split("var decimalZeros = [...]rune{")
            .nth(1)
            .expect("frozen Unicode15 decimal table")
            .split('}')
            .next()
            .unwrap()
            .split(',')
            .filter_map(|s| u32::from_str_radix(s.trim().strip_prefix("0x")?, 16).ok())
            .collect()
    });
    let index = zeros.partition_point(|v| *v <= c as u32);
    index.checked_sub(1).and_then(|i| {
        let n = c as u32 - zeros[i];
        (n < 10).then_some((b'0' + n as u8) as char)
    })
}
fn numeric_space(c: char) -> bool {
    matches!(c,'\u{9}'..='\u{d}'|' '|'\u{85}'|'\u{a0}'|'\u{1680}'|'\u{2000}'..='\u{200a}'|'\u{2028}'|'\u{2029}'|'\u{202f}'|'\u{205f}'|'\u{3000}')
}
fn numeric_text(raw: &str) -> Option<(String, usize)> {
    let chars: Vec<_> = raw.trim_matches(numeric_space).chars().collect();
    let mut text = String::new();
    let mut digits = 0;
    for (i, c) in chars.iter().copied().enumerate() {
        if let Some(d) = decimal(c) {
            text.push(d);
            digits += 1;
            continue;
        }
        if c == '_' {
            if i == 0
                || i + 1 == chars.len()
                || decimal(chars[i - 1]).is_none()
                || decimal(chars[i + 1]).is_none()
            {
                return None;
            };
            continue;
        }
        if !c.is_ascii() {
            return None;
        };
        text.push(c)
    }
    Some((text, digits))
}
pub fn parse(ttl: Option<&str>, cap: Option<&str>) -> Result<Config, String> {
    let mut cfg = Config {
        ttl_seconds: 7200.,
        max_sessions: 1000,
    };
    if let Some(raw) = ttl {
        let invalid = || format!("{TTL_ENV} must be a positive number");
        let (text, _) = numeric_text(raw).ok_or_else(invalid)?;
        let value = text.parse::<f64>().map_err(|_| invalid())?;
        if !value.is_finite() || value <= 0. {
            return Err(invalid());
        };
        cfg.ttl_seconds = value;
    }
    if let Some(raw) = cap {
        let invalid = || format!("{CAP_ENV} must be a positive integer");
        let (text, digits) = numeric_text(raw).ok_or_else(invalid)?;
        if digits > 4300 {
            return Err(invalid());
        };
        let value = BigInt::parse_bytes(text.as_bytes(), 10).ok_or_else(invalid)?;
        if value.sign() != Sign::Plus {
            return Err(invalid());
        };
        cfg.max_sessions = usize::try_from(&value).unwrap_or(usize::MAX);
    }
    Ok(cfg)
}
pub fn from_env() -> Result<Config, String> {
    fn read(name: &str, kind: &str) -> Result<Option<String>, String> {
        match env::var(name) {
            Ok(value) => Ok(Some(value)),
            Err(env::VarError::NotPresent) => Ok(None),
            Err(_) => Err(format!("{name} must be a positive {kind}")),
        }
    }
    let ttl = read(TTL_ENV, "number")?;
    let cap = read(CAP_ENV, "integer")?;
    parse(ttl.as_deref(), cap.as_deref())
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn python_settings() {
        assert_eq!(
            parse(None, None).unwrap(),
            Config {
                ttl_seconds: 7200.,
                max_sessions: 1000
            }
        );
        for value in ["1.25", "  +١.٢٥  ", "1_2.5e-1", "１.２５"] {
            assert_eq!(parse(Some(value), None).unwrap().ttl_seconds, 1.25)
        }
        for value in ["+٣", " ３ ", "0_3"] {
            assert_eq!(parse(None, Some(value)).unwrap().max_sessions, 3)
        }
        for value in [
            "",
            "0",
            "-1",
            "NaN",
            "inf",
            "1e309",
            "1__2",
            "\u{1c}1.25\u{1f}",
            "١_.٢",
        ] {
            assert!(
                parse(Some(value), None).unwrap_err().contains(TTL_ENV),
                "{value}"
            )
        }
        for value in [
            "",
            "0",
            "-1",
            "1.0",
            "1e3",
            "3__0",
            "0x10",
            "\u{1c}3\u{1f}",
            "𑯱",
        ] {
            assert!(
                parse(None, Some(value)).unwrap_err().contains(CAP_ENV),
                "{value}"
            )
        }
        assert_eq!(
            parse(Some("1e-100"), Some(&"9".repeat(100))).unwrap(),
            Config {
                ttl_seconds: 1e-100,
                max_sessions: usize::MAX
            }
        );
        assert_eq!(parse(Some("1e100"), None).unwrap().ttl_seconds, 1e100);
    }
}
