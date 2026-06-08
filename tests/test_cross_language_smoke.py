"""Cross-language smoke + CI gate tests for step 7.

Step 7 pulls every preceding step into one verifiable shape: a single
canonical wire-bytes vector lives at ``tests/fixtures/cross_language_vector.json``,
three language-specific smoke harnesses (Rust integration test, Python
pytest, TypeScript bun test) round-trip a ``monorepo.v1.Money`` against
those bytes, and a ``.github/workflows/ci.yml`` workflow runs ``buf
lint``, ``buf breaking``, and the three smoke jobs on every PR.

These assertions read file contents directly so the suite stays green on
a machine that has no ``cargo``, ``bun``, ``buf``, or generated stubs --
matching every prior step's posture. The smoke harnesses themselves
verify the runtime parity; this module verifies the harnesses are wired
up so a regression cannot land without tripping a gate.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
VECTOR_PATH = REPO_ROOT / "tests" / "fixtures" / "cross_language_vector.json"
CI_WORKFLOW = REPO_ROOT / ".github" / "workflows" / "ci.yml"
RUST_SMOKE = REPO_ROOT / "rust" / "crates" / "monorepo-pb" / "tests" / "cross_language_smoke.rs"
PYTHON_SMOKE = REPO_ROOT / "python" / "tests" / "test_cross_language_smoke.py"
TS_SMOKE = REPO_ROOT / "typescript" / "tests" / "cross_language_smoke.test.ts"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _load_vector() -> dict:
    return json.loads(_read(VECTOR_PATH))


def test_canonical_vector_fixture_exists():
    assert VECTOR_PATH.is_file(), (
        "tests/fixtures/cross_language_vector.json must exist"
    )


def test_canonical_vector_declares_proto_package_and_money_shape():
    vector = _load_vector()
    assert vector["proto_package"] == "monorepo.v1", (
        "vector must pin the monorepo.v1 package"
    )
    money = vector["money"]
    assert money["currency_code"] == "USD", "vector currency_code must be USD"
    assert isinstance(money["amount_minor_units"], int), (
        "vector amount_minor_units must be a JSON integer"
    )
    assert money["amount_minor_units"] > 0, (
        "vector amount_minor_units must be a positive minor-unit count"
    )


def test_canonical_vector_pins_account_metadata():
    vector = _load_vector()
    account = vector["account"]
    assert account["id"].startswith("acct_"), (
        "vector account.id must follow the acct_<slug> shape"
    )
    assert account["display_name"], "vector account.display_name must be non-empty"


def test_canonical_money_wire_bytes_match_the_proto3_encoding():
    """Recompute the expected proto3 wire bytes for the canonical Money
    in pure Python and assert they match the vector's hex blob. This
    keeps the three language harnesses honest -- if the vector ever
    drifts from the actual proto3 encoding, every smoke job would still
    agree with each other but disagree with reality. This check anchors
    the vector to the protocol itself."""
    vector = _load_vector()
    currency = vector["money"]["currency_code"].encode("utf-8")
    amount = int(vector["money"]["amount_minor_units"])

    expected = bytearray()
    expected.append(0x0A)  # field 1, wire type 2 (length-delimited)
    expected.append(len(currency))
    expected.extend(currency)
    expected.append(0x10)  # field 2, wire type 0 (varint)
    while True:
        byte = amount & 0x7F
        amount >>= 7
        if amount:
            expected.append(byte | 0x80)
        else:
            expected.append(byte)
            break

    assert bytes(expected).hex() == vector["money_wire_bytes_hex"], (
        "vector money_wire_bytes_hex must be the proto3 encoding of the "
        "pinned Money fields"
    )


def test_rust_smoke_harness_exists_and_round_trips_money():
    assert RUST_SMOKE.is_file(), (
        "rust/crates/monorepo-pb/tests/cross_language_smoke.rs must exist"
    )
    text = _read(RUST_SMOKE)
    assert "cross_language_vector.json" in text, (
        "Rust smoke must load the canonical vector by name"
    )
    assert "use monorepo_pb::v1::Money;" in text, (
        "Rust smoke must build the Money message from the crate's public surface"
    )
    assert "encode_to_vec" in text, (
        "Rust smoke must encode Money through prost"
    )
    assert "Money::decode" in text, (
        "Rust smoke must decode the bytes back through prost"
    )
    assert "#[test]" in text, "Rust smoke must register at least one #[test]"


def test_python_smoke_harness_exists_and_round_trips_money():
    assert PYTHON_SMOKE.is_file(), (
        "python/tests/test_cross_language_smoke.py must exist"
    )
    text = _read(PYTHON_SMOKE)
    assert "cross_language_vector.json" in text, (
        "Python smoke must load the canonical vector by name"
    )
    assert "monorepo_pb.gen.monorepo.v1" in text, (
        "Python smoke must reach the generated stubs via the package path"
    )
    assert "money_pb2" in text, "Python smoke must import money_pb2"
    assert "SerializeToString" in text, (
        "Python smoke must serialise Money through the protobuf runtime"
    )
    assert "ParseFromString" in text, (
        "Python smoke must parse the wire bytes back into Money"
    )


def test_typescript_smoke_harness_exists_and_round_trips_money():
    assert TS_SMOKE.is_file(), (
        "typescript/tests/cross_language_smoke.test.ts must exist"
    )
    text = _read(TS_SMOKE)
    assert "cross_language_vector.json" in text, (
        "TypeScript smoke must load the canonical vector by name"
    )
    assert "money_pb" in text, (
        "TypeScript smoke must import the generated money_pb module"
    )
    assert "toBinary" in text, (
        "TypeScript smoke must encode Money via @bufbuild/protobuf"
    )
    assert "fromBinary" in text, (
        "TypeScript smoke must decode the wire bytes back into Money"
    )
    assert 'from "bun:test"' in text, (
        "TypeScript smoke must run under the bun test runner"
    )


def test_all_three_smoke_harnesses_reference_the_money_wire_bytes_hex_key():
    """Pin the contract from a different angle: every language harness
    must consult the same JSON key for the canonical bytes. Drift on
    this key would silently disable parity checking in one language."""
    for path in (RUST_SMOKE, PYTHON_SMOKE, TS_SMOKE):
        text = _read(path)
        assert "money_wire_bytes_hex" in text, (
            f"{path.name} must read the money_wire_bytes_hex vector key"
        )


def test_ci_workflow_exists_at_standard_github_path():
    assert CI_WORKFLOW.is_file(), (
        ".github/workflows/ci.yml must exist for GitHub Actions to pick it up"
    )


def test_ci_workflow_runs_on_push_and_pull_request_to_main():
    text = _read(CI_WORKFLOW)
    assert re.search(r"^on:", text, re.MULTILINE), "workflow must declare an `on:` block"
    assert "push:" in text, "workflow must trigger on push"
    assert "pull_request:" in text, "workflow must trigger on pull_request"
    assert "branches: [main]" in text, (
        "workflow must scope triggers to the main branch"
    )


def test_ci_workflow_pins_a_buf_version_via_env():
    text = _read(CI_WORKFLOW)
    assert re.search(r'BUF_VERSION:\s*"\d+\.\d+\.\d+"', text), (
        "workflow must pin BUF_VERSION to a concrete x.y.z release"
    )


def test_ci_workflow_enforces_buf_lint_and_buf_breaking_gates():
    text = _read(CI_WORKFLOW)
    assert "buf lint" in text, "workflow must run `buf lint`"
    assert "buf breaking" in text, "workflow must run `buf breaking`"
    assert ".git#branch=main" in text, (
        "buf breaking must diff against the main branch"
    )
    assert "bufbuild/buf-setup-action" in text, (
        "workflow must use the official buf setup action"
    )


def test_ci_workflow_runs_all_three_language_smoke_jobs():
    text = _read(CI_WORKFLOW)
    for job in ("rust-smoke:", "python-smoke:", "typescript-smoke:"):
        assert job in text, f"workflow is missing job: {job}"
    assert "make rust-test" in text, "rust-smoke must invoke `make rust-test`"
    assert "make python-test" in text, "python-smoke must invoke `make python-test`"
    assert "make ts-test" in text, "typescript-smoke must invoke `make ts-test`"


def test_ci_language_jobs_depend_on_the_proto_gates():
    """Language smoke jobs must not start until `buf lint` + `buf
    breaking` have passed -- otherwise a broken schema would burn three
    runners before the cheap proto gate even reported."""
    text = _read(CI_WORKFLOW)
    needs_lines = re.findall(r"needs:\s*proto-gates", text)
    assert len(needs_lines) >= 3, (
        "rust-smoke, python-smoke, and typescript-smoke must each `needs: proto-gates`"
    )


def test_ci_workflow_invokes_buf_generate_before_language_tests():
    text = _read(CI_WORKFLOW)
    # Each smoke job must call make generate (which shells out to
    # `buf generate`) before running the language-native test step.
    assert text.count("make generate") >= 3, (
        "each language smoke job must run `make generate` before testing"
    )


def test_ci_workflow_uses_pinned_action_versions():
    text = _read(CI_WORKFLOW)
    assert "actions/checkout@v4" in text, "checkout action must be pinned to v4"
    assert "actions/setup-python@v5" in text, "setup-python must be pinned to v5"
    assert "oven-sh/setup-bun@v2" in text, "setup-bun must be pinned to v2"


def test_makefile_exposes_smoke_and_ci_targets():
    text = _read(REPO_ROOT / "Makefile")
    for target in ("smoke:", "ci:"):
        assert target in text, f"Makefile is missing target: {target}"
    assert re.search(r"smoke:\s*rust-test\s+python-test\s+ts-test", text), (
        "smoke target must fan out to all three language test runners"
    )
    assert re.search(r"ci:\s*lint\s+breaking\s+generate\s+smoke", text), (
        "ci target must compose lint + breaking + generate + smoke"
    )


def test_rust_workspace_pins_serde_json_for_smoke_harness():
    """The Rust smoke harness reads the JSON vector via serde_json, so
    the workspace must vend a version pinned in workspace.dependencies
    and the crate must opt in via dev-dependencies."""
    workspace = _read(REPO_ROOT / "rust" / "Cargo.toml")
    assert re.search(r'serde_json\s*=\s*"1\.', workspace), (
        "rust/Cargo.toml workspace must pin serde_json 1.x"
    )
    crate = _read(REPO_ROOT / "rust" / "crates" / "monorepo-pb" / "Cargo.toml")
    assert "serde_json" in crate, (
        "monorepo-pb crate must list serde_json as a dev-dependency"
    )
    # Ensure it's a dev-dep, not a runtime dep -- prevents the smoke
    # harness leaking JSON parsing into the library's public surface.
    dev_section = crate.split("[dev-dependencies]", 1)[1]
    assert "serde_json" in dev_section, (
        "serde_json must live under [dev-dependencies], not [dependencies]"
    )


def test_cross_language_files_have_no_operator_private_paths():
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    scan_targets = (
        VECTOR_PATH,
        CI_WORKFLOW,
        RUST_SMOKE,
        PYTHON_SMOKE,
        TS_SMOKE,
        REPO_ROOT / "Makefile",
    )
    for path in scan_targets:
        text = _read(path)
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"{path.name} leaks operator-private path: {fragment}"
            )
