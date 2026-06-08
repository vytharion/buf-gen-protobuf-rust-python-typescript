//! Cross-language smoke harness for the Rust crate.
//!
//! Reads `tests/fixtures/cross_language_vector.json` from the repo root,
//! builds a `monorepo.v1.Money` with the canonical field values, encodes
//! it through prost, and compares the on-wire bytes against the hex blob
//! pinned in the fixture. Decoding those same bytes back must reproduce
//! the original field values. The Python and TypeScript harnesses run the
//! identical check; together they guarantee that all three runtimes
//! interoperate on the same byte sequence.
//!
//! This test only runs after `buf generate` has populated `src/gen/`.

use std::fs;
use std::path::PathBuf;

use monorepo_pb::v1::Money;
use prost::Message;

const VECTOR_RELATIVE_PATH: &str = "tests/fixtures/cross_language_vector.json";

fn repo_root() -> PathBuf {
    let crate_dir = PathBuf::from(env!("CARGO_MANIFEST_DIR"));
    crate_dir
        .ancestors()
        .nth(3)
        .expect("repo root sits three levels above the crate manifest")
        .to_path_buf()
}

fn load_vector() -> serde_json::Value {
    let path = repo_root().join(VECTOR_RELATIVE_PATH);
    let raw = fs::read_to_string(&path).expect("vector fixture must be readable");
    serde_json::from_str(&raw).expect("vector fixture must be valid JSON")
}

fn decode_hex(hex: &str) -> Vec<u8> {
    assert!(hex.len() % 2 == 0, "hex string must have even length");
    (0..hex.len())
        .step_by(2)
        .map(|i| u8::from_str_radix(&hex[i..i + 2], 16).expect("hex digit"))
        .collect()
}

#[test]
fn money_round_trips_against_canonical_vector() {
    let vector = load_vector();
    let currency = vector["money"]["currency_code"]
        .as_str()
        .expect("money.currency_code")
        .to_string();
    let minor_units = vector["money"]["amount_minor_units"]
        .as_i64()
        .expect("money.amount_minor_units");
    let expected_hex = vector["money_wire_bytes_hex"]
        .as_str()
        .expect("money_wire_bytes_hex");

    let original = Money {
        currency_code: currency.clone(),
        amount_minor_units: minor_units,
    };
    let encoded = original.encode_to_vec();
    assert_eq!(
        encoded,
        decode_hex(expected_hex),
        "Rust prost encoding diverged from the canonical wire bytes",
    );

    let decoded = Money::decode(&*encoded).expect("Money must decode");
    assert_eq!(decoded.currency_code, currency);
    assert_eq!(decoded.amount_minor_units, minor_units);
}
