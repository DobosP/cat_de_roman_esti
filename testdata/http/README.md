# Frozen request-body reference

`python-body-models.json` contains the unchanged 32 application-model cases
captured from the Django/Pydantic reference and previously held as a Rust raw
string at `rust-backend/src/validation.rs` on base
`ae70c16935d402719b95405685bccbbbea13a3bd`. Extraction changes no JSON byte.

SHA-256: `20748c9e111b54d0e0de6efeef476b77afc7b91bb71144b0aa8194f524e7ca40`.
The Go consumer checks this digest before evaluating any expected error. This
language-neutral fixture has no dependency on Rust source or a Rust compiler.
