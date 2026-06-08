"""Schema-layer tests for step 2.

Lock down the shape of the shared .proto contracts and the buf.yaml
lint + breaking-change configuration. These checks fire purely against
the file contents, so they pass without a buf binary on PATH while
still catching the most common drift modes: stale package names,
missing go_package options, duplicated field numbers, or a buf.yaml
that has been silently downgraded from DEFAULT lint coverage.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PROTO_DIR = REPO_ROOT / "proto"
PROTO_PACKAGE_DIR = PROTO_DIR / "monorepo" / "v1"

GO_PACKAGE_PREFIX = (
    "github.com/vytharion/buf-gen-protobuf-rust-python-typescript"
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _proto_files() -> list[Path]:
    return sorted(PROTO_PACKAGE_DIR.glob("*.proto"))


def test_proto_package_directory_layout():
    assert PROTO_PACKAGE_DIR.is_dir(), (
        "proto/monorepo/v1/ must hold the v1 schemas"
    )
    files = _proto_files()
    assert files, "at least one .proto file is required for v1"


def test_buf_yaml_enables_default_lint_and_file_breaking():
    cfg = PROTO_DIR / "buf.yaml"
    assert cfg.is_file(), "proto/buf.yaml is required"
    text = _read(cfg)
    assert "version: v1" in text, "module buf.yaml must declare version v1"
    assert "lint:" in text, "lint section missing"
    assert "DEFAULT" in text, "lint must use the DEFAULT category"
    assert "breaking:" in text, "breaking section missing"
    assert "FILE" in text, "breaking must use the FILE category"


def test_every_proto_declares_proto3_and_versioned_package():
    for proto_file in _proto_files():
        text = _read(proto_file)
        assert 'syntax = "proto3";' in text, (
            f"{proto_file.name} must use proto3"
        )
        assert "package monorepo.v1;" in text, (
            f"{proto_file.name} must declare package monorepo.v1"
        )


def test_every_proto_has_consistent_go_package_option():
    for proto_file in _proto_files():
        text = _read(proto_file)
        match = re.search(r'option go_package = "([^"]+)";', text)
        assert match, f"{proto_file.name} must set option go_package"
        value = match.group(1)
        assert GO_PACKAGE_PREFIX in value, (
            f"{proto_file.name} go_package must live under the vytharion repo"
        )
        assert value.endswith(";monorepov1"), (
            f"{proto_file.name} go_package must alias the monorepov1 package"
        )


def test_proto_filenames_use_snake_case():
    for proto_file in _proto_files():
        stem = proto_file.stem
        assert re.fullmatch(r"[a-z][a-z0-9_]*", stem), (
            f"{proto_file.name} should be snake_case"
        )


def test_no_duplicate_field_numbers_within_a_message():
    field_pattern = re.compile(
        r"^\s*(?:repeated\s+|optional\s+)?[\w.]+\s+\w+\s*=\s*(\d+)\s*;",
        re.MULTILINE,
    )
    message_pattern = re.compile(r"message\s+\w+\s*\{([^}]*)\}", re.DOTALL)
    for proto_file in _proto_files():
        text = _read(proto_file)
        for body in message_pattern.findall(text):
            numbers = [int(n) for n in field_pattern.findall(body)]
            assert len(numbers) == len(set(numbers)), (
                f"duplicate field number in {proto_file.name}: {numbers}"
            )


def test_ledger_proto_defines_the_transfer_service():
    ledger = PROTO_PACKAGE_DIR / "ledger.proto"
    assert ledger.is_file(), "ledger.proto must exist"
    text = _read(ledger)
    assert re.search(r"service\s+LedgerService\s*\{", text), (
        "LedgerService rpc surface is required"
    )
    assert "rpc Transfer(" in text, "Transfer rpc must be declared"
    assert "rpc GetAccount(" in text, "GetAccount rpc must be declared"


def test_ledger_imports_money_and_well_known_timestamp():
    ledger = PROTO_PACKAGE_DIR / "ledger.proto"
    text = _read(ledger)
    assert 'import "monorepo/v1/money.proto";' in text, (
        "ledger.proto must import the shared Money type"
    )
    assert 'import "google/protobuf/timestamp.proto";' in text, (
        "ledger.proto must import the well-known Timestamp"
    )


def test_money_message_uses_minor_units_to_avoid_floats():
    money = PROTO_PACKAGE_DIR / "money.proto"
    assert money.is_file(), "money.proto must exist for a shared Money type"
    text = _read(money)
    assert "message Money" in text
    assert "int64" in text, "Money must use int64 to avoid float drift"
    assert "double" not in text, (
        "Money must not introduce floating-point fields"
    )
    assert "float" not in text, (
        "Money must not introduce floating-point fields"
    )


def test_makefile_exposes_buf_lint_and_breaking_targets():
    makefile = REPO_ROOT / "Makefile"
    text = _read(makefile)
    for target in ("lint:", "breaking:"):
        assert target in text, f"Makefile is missing target: {target}"
    assert "buf lint" in text, "lint target must invoke buf lint"
    assert "buf breaking" in text, "breaking target must invoke buf breaking"


def test_no_operator_private_paths_in_schemas():
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    shipped_artifacts: list[Path] = [PROTO_DIR / "buf.yaml"]
    shipped_artifacts.extend(_proto_files())
    for candidate in shipped_artifacts:
        text = _read(candidate)
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"{candidate.name} leaks operator-private path: {fragment}"
            )
