//! Pydantic-compatible body validation shared by the native arcade routes.
use crate::{ApiError, httpapi};
use serde_json::{Map, Value, json};

fn issue(
    kind: &str,
    location: &[Value],
    message: &str,
    input: &Value,
    context: Option<Value>,
) -> Value {
    let mut error = json!({"type":kind,"loc":location,"msg":message,"input":input});
    if let Some(context) = context {
        error["ctx"] = context;
    }
    error
}
fn location(parent: &[Value], field: impl Into<Value>) -> Vec<Value> {
    let mut result = parent.to_vec();
    result.push(field.into());
    result
}
fn failure(errors: Vec<Value>) -> ApiError {
    ApiError {
        status: 422,
        detail: Value::Array(errors),
    }
}
fn parsed(raw: &[u8]) -> Result<Value, ApiError> {
    if raw.iter().all(u8::is_ascii_whitespace) {
        return Ok(Value::Null);
    }
    let (mut quoted, mut escaped, mut depth) = (false, false, 0usize);
    for &byte in raw {
        if escaped {
            escaped = false;
            continue;
        }
        if quoted && byte == b'\\' {
            escaped = true;
            continue;
        }
        if byte == b'"' {
            quoted = !quoted;
            continue;
        }
        if !quoted {
            if byte == b'[' || byte == b'{' {
                depth += 1;
            }
            if byte == b']' || byte == b'}' {
                depth = depth.saturating_sub(1);
            }
            if depth > 1024 {
                return Err(ApiError::new(422, "JSON nesting limit exceeded"));
            }
        }
    }
    httpapi::parse_json(raw).map_err(|error| {
        failure(vec![issue(
            "json_invalid",
            &[json!("body")],
            "JSON decode error",
            &json!({}),
            Some(json!({"error":httpapi::json_message(raw,&error)})),
        )])
    })
}
fn object<'a>(
    value: &'a Value,
    name: &str,
    parent: &[Value],
    errors: &mut Vec<Value>,
) -> Option<&'a Map<String, Value>> {
    if let Some(object) = value.as_object() {
        Some(object)
    } else {
        errors.push(issue(
            "model_type",
            parent,
            &format!("Input should be a valid dictionary or instance of {name}"),
            value,
            Some(json!({"class_name":name})),
        ));
        None
    }
}
fn string(
    value: &Value,
    parent: &[Value],
    identifier: bool,
    hash: bool,
    errors: &mut Vec<Value>,
) -> Option<String> {
    let Some(text) = value.as_str() else {
        errors.push(issue(
            "string_type",
            parent,
            "Input should be a valid string",
            value,
            None,
        ));
        return None;
    };
    if identifier {
        let length = text.chars().count();
        if length < 1 {
            errors.push(issue(
                "string_too_short",
                parent,
                "String should have at least 1 character",
                value,
                Some(json!({"min_length":1})),
            ));
            return None;
        }
        if length > 160 {
            errors.push(issue(
                "string_too_long",
                parent,
                "String should have at most 160 characters",
                value,
                Some(json!({"max_length":160})),
            ));
            return None;
        }
    }
    if hash
        && (text.len() != 64
            || !text
                .bytes()
                .all(|c| c.is_ascii_digit() || (b'a'..=b'f').contains(&c)))
    {
        errors.push(issue(
            "string_pattern_mismatch",
            parent,
            "String should match pattern '^[a-f0-9]{64}$'",
            value,
            Some(json!({"pattern":"^[a-f0-9]{64}$"})),
        ));
        return None;
    }
    Some(text.to_owned())
}
fn field(
    object: &Map<String, Value>,
    name: &str,
    parent: &[Value],
    nullable: bool,
    required: bool,
    identifier: bool,
    errors: &mut Vec<Value>,
) -> Option<String> {
    let loc = location(parent, name);
    match object.get(name) {
        Some(Value::Null) if nullable => None,
        Some(value) => string(value, &loc, identifier, false, errors),
        None if required => {
            errors.push(issue(
                "missing",
                &loc,
                "Field required",
                &Value::Object(object.clone()),
                None,
            ));
            None
        }
        None => None,
    }
}
fn extra(object: &Map<String, Value>, allowed: &[&str], parent: &[Value], errors: &mut Vec<Value>) {
    for (key, value) in object {
        if !allowed.contains(&key.as_str()) {
            errors.push(issue(
                "extra_forbidden",
                &location(parent, key.as_str()),
                "Extra inputs are not permitted",
                value,
                None,
            ));
        }
    }
}
fn finish<T>(value: T, errors: Vec<Value>) -> Result<T, ApiError> {
    if errors.is_empty() {
        Ok(value)
    } else {
        Err(failure(errors))
    }
}

pub fn ids(raw: &[u8], model: &str) -> Result<Vec<String>, ApiError> {
    let value = parsed(raw)?;
    let parent = vec![json!("body")];
    let mut errors = Vec::new();
    let mut ids = Vec::new();
    if let Some(object) = object(&value, model, &parent, &mut errors) {
        let loc = location(&parent, "ids");
        match object.get("ids") {
            None => errors.push(issue("missing", &loc, "Field required", &value, None)),
            Some(Value::Array(values)) => {
                for (index, value) in values.iter().enumerate() {
                    if let Some(text) = string(
                        value,
                        &location(&loc, json!(index)),
                        false,
                        false,
                        &mut errors,
                    ) {
                        ids.push(text)
                    }
                }
            }
            Some(value) => errors.push(issue(
                "list_type",
                &loc,
                "Input should be a valid list",
                value,
                None,
            )),
        }
    }
    finish(ids, errors)
}
pub fn text(raw: &[u8], model: &str) -> Result<String, ApiError> {
    let value = parsed(raw)?;
    let parent = vec![json!("body")];
    let mut errors = Vec::new();
    let text = object(&value, model, &parent, &mut errors)
        .and_then(|object| field(object, "text", &parent, false, true, false, &mut errors))
        .unwrap_or_default();
    finish(text, errors)
}
pub fn contexto_guess(raw: &[u8]) -> Result<(String, Option<String>), ApiError> {
    let value = parsed(raw)?;
    let parent = vec![json!("body")];
    let mut errors = Vec::new();
    let (mut text, mut confirm) = (String::new(), None);
    if let Some(object) = object(&value, "GuessBody", &parent, &mut errors) {
        text = field(object, "text", &parent, false, true, false, &mut errors).unwrap_or_default();
        confirm = field(object, "confirm", &parent, true, false, false, &mut errors);
    }
    finish((text, confirm), errors)
}
pub fn pair(raw: &[u8], model: &str, strict: bool) -> Result<(String, String), ApiError> {
    let value = parsed(raw)?;
    let parent = vec![json!("body")];
    let mut errors = Vec::new();
    let (mut a, mut b) = (String::new(), String::new());
    if let Some(object) = object(&value, model, &parent, &mut errors) {
        a = field(object, "a", &parent, false, true, strict, &mut errors).unwrap_or_default();
        b = field(object, "b", &parent, false, true, strict, &mut errors).unwrap_or_default();
        if strict {
            extra(object, &["a", "b"], &parent, &mut errors);
        }
    }
    finish((a, b), errors)
}
pub fn goal(raw: &[u8]) -> Result<Option<String>, ApiError> {
    let value = parsed(raw)?;
    let parent = vec![json!("body")];
    let mut errors = Vec::new();
    let mut goal = None;
    if let Some(object) = object(&value, "GoalBody", &parent, &mut errors) {
        goal = field(object, "goal_id", &parent, true, true, true, &mut errors);
        extra(object, &["goal_id"], &parent, &mut errors);
    }
    finish(goal, errors)
}

pub fn exploration_create(raw: &[u8]) -> Result<(Option<Value>, Option<String>), ApiError> {
    let value = parsed(raw)?;
    let parent = vec![json!("body")];
    let mut errors = Vec::new();
    let (mut progress, mut goal) = (None, None);
    if let Some(object) = object(&value, "CreateBody", &parent, &mut errors) {
        if let Some(input) = object.get("progress").filter(|value| !value.is_null()) {
            let loc = location(&parent, "progress");
            if let Some(record) = self::object(input, "Progress", &loc, &mut errors) {
                field(record, "world_id", &loc, false, true, true, &mut errors);
                let hash_loc = location(&loc, "recipe_hash");
                if let Some(hash) = record.get("recipe_hash") {
                    string(hash, &hash_loc, false, true, &mut errors);
                } else {
                    errors.push(issue("missing", &hash_loc, "Field required", input, None));
                }
                let discover_loc = location(&loc, "discoveries");
                match record.get("discoveries") {
                    None => errors.push(issue(
                        "missing",
                        &discover_loc,
                        "Field required",
                        input,
                        None,
                    )),
                    Some(Value::Array(rows)) => {
                        if rows.len() > 256 {
                            errors.push(issue("too_long",&discover_loc,&format!("List should have at most 256 items after validation, not {}",rows.len()),&Value::Array(rows.clone()),Some(json!({"field_type":"List","max_length":256,"actual_length":rows.len()}))));
                        } else {
                            for (index, row) in rows.iter().enumerate() {
                                let row_loc = location(&discover_loc, json!(index));
                                if let Some(ids) = row.as_array() {
                                    for (index, id) in ids.iter().enumerate() {
                                        string(
                                            id,
                                            &location(&row_loc, json!(index)),
                                            true,
                                            false,
                                            &mut errors,
                                        );
                                    }
                                } else {
                                    errors.push(issue(
                                        "list_type",
                                        &row_loc,
                                        "Input should be a valid list",
                                        row,
                                        None,
                                    ));
                                }
                            }
                        }
                    }
                    Some(value) => errors.push(issue(
                        "list_type",
                        &discover_loc,
                        "Input should be a valid list",
                        value,
                        None,
                    )),
                }
                extra(
                    record,
                    &["world_id", "recipe_hash", "discoveries"],
                    &loc,
                    &mut errors,
                );
                progress = Some(input.clone());
            }
        }
        goal = field(object, "goal_id", &parent, true, false, true, &mut errors);
        extra(object, &["progress", "goal_id"], &parent, &mut errors);
    }
    finish((progress, goal), errors)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn record_extra_errors_preserve_original_json_key_order_at_every_level() {
        let error = pair(br#"{"z":1,"a":"x","b":"y","c":2}"#, "PairBody", true).unwrap_err();
        assert_eq!(error.detail[0]["loc"], json!(["body", "z"]));
        assert_eq!(error.detail[1]["loc"], json!(["body", "c"]));
        let raw = format!(
            r#"{{"extra_z":1,"progress":{{"unknown_z":1,"world_id":"world","recipe_hash":"{}","discoveries":[],"unknown_a":2}},"extra_a":3}}"#,
            "a".repeat(64)
        );
        let error = exploration_create(raw.as_bytes()).unwrap_err();
        let locations: Vec<Value> = error
            .detail
            .as_array()
            .unwrap()
            .iter()
            .map(|error| error["loc"].clone())
            .collect();
        assert_eq!(
            locations,
            vec![
                json!(["body", "progress", "unknown_z"]),
                json!(["body", "progress", "unknown_a"]),
                json!(["body", "extra_z"]),
                json!(["body", "extra_a"])
            ]
        );
    }
    #[test]
    fn arrays_and_strings_keep_model_error_locations() {
        let error = ids(br#"{"ids":[1,null,"ok"]}"#, "MatchBody").unwrap_err();
        assert_eq!(error.status, 422);
        assert_eq!(
            error.detail,
            json!([{"type":"string_type","loc":["body","ids",0],"msg":"Input should be a valid string","input":1},{"type":"string_type","loc":["body","ids",1],"msg":"Input should be a valid string","input":null}])
        );
        assert_eq!(
            text(b"[]", "MoveBody").unwrap_err().detail[0]["ctx"]["class_name"],
            json!("MoveBody")
        );
        assert!(pair(br#"{"a":"x","b":"y","ignored":true}"#, "CombineBody", false).is_ok());
    }
    #[test]
    fn records_forbid_extra_and_enforce_unicode_lengths_hash_and_checkpoint_bounds() {
        assert_eq!(
            pair(br#"{"a":"","b":7,"extra":true}"#, "PairBody", true)
                .unwrap_err()
                .detail
                .as_array()
                .unwrap()
                .len(),
            3
        );
        let long = "ș".repeat(161);
        assert_eq!(
            goal(&serde_json::to_vec(&json!({"goal_id":long})).unwrap())
                .unwrap_err()
                .detail[0]["ctx"]["max_length"],
            json!(160)
        );
        let progress = json!({"world_id":"world","recipe_hash":"A".repeat(64),"discoveries":[]});
        assert_eq!(
            exploration_create(&serde_json::to_vec(&json!({"progress":progress})).unwrap())
                .unwrap_err()
                .detail[0]["type"],
            json!("string_pattern_mismatch")
        );
        let progress = json!({"world_id":"world","recipe_hash":"a".repeat(64),"discoveries":vec![json!([]);257]});
        assert_eq!(
            exploration_create(&serde_json::to_vec(&json!({"progress":progress})).unwrap())
                .unwrap_err()
                .detail[0]["type"],
            json!("too_long")
        );
        assert_eq!(goal(b"{}").unwrap_err().detail[0]["type"], json!("missing"));
        assert_eq!(goal(br#"{"goal_id":null}"#).unwrap(), None);
        assert!(exploration_create(b"{}").is_ok());
    }
    #[test]
    fn frozen_python_pydantic_models_match_all_validation_errors() {
        // Captured directly from the Python application models with Pydantic.
        let vectors: Value = serde_json::from_str(r###"[{"kind":"ids","model":"MatchBody","raw":"null","error":[{"type":"model_type","loc":["body"],"msg":"Input should be a valid dictionary or instance of MatchBody","input":null,"ctx":{"class_name":"MatchBody"}}]},{"kind":"ids","model":"MatchBody","raw":"[]","error":[{"type":"model_type","loc":["body"],"msg":"Input should be a valid dictionary or instance of MatchBody","input":[],"ctx":{"class_name":"MatchBody"}}]},{"kind":"ids","model":"MatchBody","raw":"{}","error":[{"type":"missing","loc":["body","ids"],"msg":"Field required","input":{}}]},{"kind":"ids","model":"MatchBody","raw":"{\"ids\": null}","error":[{"type":"list_type","loc":["body","ids"],"msg":"Input should be a valid list","input":null}]},{"kind":"ids","model":"MatchBody","raw":"{\"ids\": [1, null, true, \"x\"]}","error":[{"type":"string_type","loc":["body","ids",0],"msg":"Input should be a valid string","input":1},{"type":"string_type","loc":["body","ids",1],"msg":"Input should be a valid string","input":null},{"type":"string_type","loc":["body","ids",2],"msg":"Input should be a valid string","input":true}]},{"kind":"ids","model":"MatchBody","raw":"{\"ids\": []}","error":null},{"kind":"contexto","model":"GuessBody","raw":"null","error":[{"type":"model_type","loc":["body"],"msg":"Input should be a valid dictionary or instance of GuessBody","input":null,"ctx":{"class_name":"GuessBody"}}]},{"kind":"contexto","model":"GuessBody","raw":"{}","error":[{"type":"missing","loc":["body","text"],"msg":"Field required","input":{}}]},{"kind":"contexto","model":"GuessBody","raw":"{\"confirm\": 2, \"text\": 1}","error":[{"type":"string_type","loc":["body","text"],"msg":"Input should be a valid string","input":1},{"type":"string_type","loc":["body","confirm"],"msg":"Input should be a valid string","input":2}]},{"kind":"contexto","model":"GuessBody","raw":"{\"confirm\": null, \"text\": \"x\"}","error":null},{"kind":"contexto","model":"GuessBody","raw":"{\"extra\": 1, \"text\": \"x\"}","error":null},{"kind":"text","model":"MoveBody","raw":"false","error":[{"type":"model_type","loc":["body"],"msg":"Input should be a valid dictionary or instance of MoveBody","input":false,"ctx":{"class_name":"MoveBody"}}]},{"kind":"text","model":"MoveBody","raw":"{}","error":[{"type":"missing","loc":["body","text"],"msg":"Field required","input":{}}]},{"kind":"text","model":"MoveBody","raw":"{\"text\": []}","error":[{"type":"string_type","loc":["body","text"],"msg":"Input should be a valid string","input":[]}]},{"kind":"text","model":"MoveBody","raw":"{\"extra\": 1, \"text\": \"x\"}","error":null},{"kind":"pair","model":"CombineBody","raw":"{}","error":[{"type":"missing","loc":["body","a"],"msg":"Field required","input":{}},{"type":"missing","loc":["body","b"],"msg":"Field required","input":{}}]},{"kind":"pair","model":"CombineBody","raw":"{\"a\": 1, \"b\": false}","error":[{"type":"string_type","loc":["body","a"],"msg":"Input should be a valid string","input":1},{"type":"string_type","loc":["body","b"],"msg":"Input should be a valid string","input":false}]},{"kind":"pair","model":"CombineBody","raw":"{\"a\": \"x\", \"b\": \"y\", \"extra\": 1}","error":null},{"kind":"strict_pair","model":"PairBody","raw":"{\"a\": \"\", \"b\": null, \"extra\": 1}","error":[{"type":"string_too_short","loc":["body","a"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}},{"type":"string_type","loc":["body","b"],"msg":"Input should be a valid string","input":null},{"type":"extra_forbidden","loc":["body","extra"],"msg":"Extra inputs are not permitted","input":1}]},{"kind":"strict_pair","model":"PairBody","raw":"{\"a\": \"șșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșș\", \"b\": \"y\"}","error":[{"type":"string_too_long","loc":["body","a"],"msg":"String should have at most 160 characters","input":"șșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșș","ctx":{"max_length":160}}]},{"kind":"strict_pair","model":"PairBody","raw":"{\"a\": \"șșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșșș\", \"b\": \"y\"}","error":null},{"kind":"goal","model":"GoalBody","raw":"{}","error":[{"type":"missing","loc":["body","goal_id"],"msg":"Field required","input":{}}]},{"kind":"goal","model":"GoalBody","raw":"{\"goal_id\": null}","error":null},{"kind":"goal","model":"GoalBody","raw":"{\"extra\": 1, \"goal_id\": []}","error":[{"type":"string_type","loc":["body","goal_id"],"msg":"Input should be a valid string","input":[]},{"type":"extra_forbidden","loc":["body","extra"],"msg":"Extra inputs are not permitted","input":1}]},{"kind":"goal","model":"GoalBody","raw":"{\"goal_id\": \"\"}","error":[{"type":"string_too_short","loc":["body","goal_id"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}}]},{"kind":"create","model":"CreateBody","raw":"null","error":[{"type":"model_type","loc":["body"],"msg":"Input should be a valid dictionary or instance of CreateBody","input":null,"ctx":{"class_name":"CreateBody"}}]},{"kind":"create","model":"CreateBody","raw":"{}","error":null},{"kind":"create","model":"CreateBody","raw":"{\"progress\": {}}","error":[{"type":"missing","loc":["body","progress","world_id"],"msg":"Field required","input":{}},{"type":"missing","loc":["body","progress","recipe_hash"],"msg":"Field required","input":{}},{"type":"missing","loc":["body","progress","discoveries"],"msg":"Field required","input":{}}]},{"kind":"create","model":"CreateBody","raw":"{\"progress\": []}","error":[{"type":"model_type","loc":["body","progress"],"msg":"Input should be a valid dictionary or instance of Progress","input":[],"ctx":{"class_name":"Progress"}}]},{"kind":"create","model":"CreateBody","raw":"{\"progress\": {\"discoveries\": [], \"recipe_hash\": \"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA\", \"world_id\": \"world\"}}","error":[{"type":"string_pattern_mismatch","loc":["body","progress","recipe_hash"],"msg":"String should match pattern '^[a-f0-9]{64}$'","input":"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA","ctx":{"pattern":"^[a-f0-9]{64}$"}}]},{"kind":"create","model":"CreateBody","raw":"{\"extra\": 1, \"progress\": {\"discoveries\": [1, [\"\", 17], []], \"recipe_hash\": \"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\", \"world_id\": \"\"}}","error":[{"type":"string_too_short","loc":["body","progress","world_id"],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}},{"type":"list_type","loc":["body","progress","discoveries",0],"msg":"Input should be a valid list","input":1},{"type":"string_too_short","loc":["body","progress","discoveries",1,0],"msg":"String should have at least 1 character","input":"","ctx":{"min_length":1}},{"type":"string_type","loc":["body","progress","discoveries",1,1],"msg":"Input should be a valid string","input":17},{"type":"extra_forbidden","loc":["body","extra"],"msg":"Extra inputs are not permitted","input":1}]},{"kind":"create","model":"CreateBody","raw":"{\"goal_id\": null, \"progress\": {\"discoveries\": [], \"recipe_hash\": \"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\", \"world_id\": \"world\"}}","error":null}]"###).unwrap();
        for case in vectors.as_array().unwrap() {
            let raw = case["raw"].as_str().unwrap().as_bytes();
            let model = case["model"].as_str().unwrap();
            let result = match case["kind"].as_str().unwrap() {
                "ids" => ids(raw, model).map(|_| ()),
                "contexto" => contexto_guess(raw).map(|_| ()),
                "text" => text(raw, model).map(|_| ()),
                "pair" => pair(raw, model, false).map(|_| ()),
                "strict_pair" => pair(raw, model, true).map(|_| ()),
                "goal" => goal(raw).map(|_| ()),
                "create" => exploration_create(raw).map(|_| ()),
                other => panic!("unknown model {other}"),
            };
            if case["error"].is_null() {
                assert!(result.is_ok(), "{}", case["raw"]);
            } else {
                let failure = result.unwrap_err();
                assert_eq!(failure.status, 422);
                assert_eq!(
                    failure.detail, case["error"],
                    "model {model}; raw {}",
                    case["raw"]
                );
            }
        }
    }
}
