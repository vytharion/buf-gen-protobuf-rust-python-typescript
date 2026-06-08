"""Rust-wiring tests for step 4.

Lock down the shape of the ``monorepo-pb`` crate so a fresh
``buf generate`` followed by ``cargo check`` will compile without
hand-tweaking. Every assertion reads file contents directly so the
suite stays green on a machine that has no ``cargo`` or ``buf``
installed -- matching the bootstrap and schema phases before it.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
RUST_ROOT = REPO_ROOT / "rust"
CRATE_ROOT = RUST_ROOT / "crates" / "monorepo-pb"
GEN_DIR = CRATE_ROOT / "src" / "gen"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_workspace_manifest_exists_and_declares_resolver_v2():
    manifest = RUST_ROOT / "Cargo.toml"
    assert manifest.is_file(), "rust/Cargo.toml workspace manifest must exist"
    text = _read(manifest)
    assert "[workspace]" in text, "missing [workspace] section"
    assert 'resolver = "2"' in text, "workspace must opt into resolver v2"


def test_workspace_lists_monorepo_pb_member():
    text = _read(RUST_ROOT / "Cargo.toml")
    assert '"crates/monorepo-pb"' in text, (
        "workspace must list crates/monorepo-pb as a member"
    )


def test_workspace_pins_prost_and_tonic_versions():
    text = _read(RUST_ROOT / "Cargo.toml")
    assert "[workspace.dependencies]" in text, (
        "workspace must centralise dependency versions"
    )
    assert re.search(r'prost\s*=\s*"0\.13"', text), (
        "prost must be pinned to the 0.13 series"
    )
    assert re.search(r"tonic\s*=\s*\{", text), (
        "tonic dependency must use a table form (features/no-default)"
    )
    assert re.search(r'tonic.*version\s*=\s*"0\.12"', text), (
        "tonic must be pinned to the 0.12 series"
    )


def test_workspace_pins_rust_edition_and_msrv():
    text = _read(RUST_ROOT / "Cargo.toml")
    assert 'edition = "2021"' in text, "workspace edition must be 2021"
    assert re.search(r'rust-version\s*=\s*"1\.\d+', text), (
        "workspace must pin an MSRV"
    )


def test_rust_toolchain_file_pins_channel():
    toolchain = RUST_ROOT / "rust-toolchain.toml"
    assert toolchain.is_file(), "rust/rust-toolchain.toml must exist"
    text = _read(toolchain)
    assert re.search(r'channel\s*=\s*"1\.\d+', text), (
        "toolchain file must pin a concrete 1.x channel, not 'stable'"
    )
    assert "clippy" in text, "toolchain must install clippy"
    assert "rustfmt" in text, "toolchain must install rustfmt"


def test_crate_manifest_exists_with_expected_metadata():
    manifest = CRATE_ROOT / "Cargo.toml"
    assert manifest.is_file(), "monorepo-pb crate manifest must exist"
    text = _read(manifest)
    assert 'name = "monorepo-pb"' in text, "crate name must be monorepo-pb"
    assert "edition.workspace = true" in text, (
        "crate must inherit edition from the workspace"
    )
    assert "repository.workspace = true" in text, (
        "crate must inherit repository from the workspace"
    )


def test_crate_depends_on_prost_tonic_and_bytes():
    text = _read(CRATE_ROOT / "Cargo.toml")
    for dep in ("prost", "prost-types", "tonic", "bytes"):
        assert re.search(rf"^{dep}\s*=\s*\{{", text, re.MULTILINE), (
            f"crate must declare workspace dependency on {dep}"
        )
        assert "workspace = true" in text, (
            "crate dependencies must inherit from workspace"
        )


def test_crate_exposes_server_and_client_features():
    text = _read(CRATE_ROOT / "Cargo.toml")
    assert "[features]" in text, "crate must declare a [features] section"
    assert re.search(r"^server\s*=\s*\[", text, re.MULTILINE), (
        "crate must expose a `server` feature for tonic server stubs"
    )
    assert re.search(r"^client\s*=\s*\[", text, re.MULTILINE), (
        "crate must expose a `client` feature for tonic client stubs"
    )


def test_lib_rs_exists_and_declares_gen_module():
    lib = CRATE_ROOT / "src" / "lib.rs"
    assert lib.is_file(), "src/lib.rs must exist"
    text = _read(lib)
    assert "pub mod gen;" in text, "lib.rs must declare `pub mod gen;`"
    assert "pub use gen::monorepo;" in text or "pub use gen::monorepo::v1" in text, (
        "lib.rs must re-export the generated monorepo namespace"
    )


def test_lib_rs_exposes_file_descriptor_set_and_proto_package():
    text = _read(CRATE_ROOT / "src" / "lib.rs")
    assert "FILE_DESCRIPTOR_SET" in text, (
        "lib.rs must expose the prost-emitted FileDescriptorSet"
    )
    assert 'PROTO_PACKAGE: &str = "monorepo.v1"' in text, (
        "lib.rs must pin the proto package name as a const"
    )


def test_lib_rs_enforces_safety_lints():
    text = _read(CRATE_ROOT / "src" / "lib.rs")
    assert "#![forbid(unsafe_code)]" in text, (
        "lib.rs must forbid unsafe code at the crate root"
    )
    assert "#![deny(rust_2018_idioms)]" in text, (
        "lib.rs must deny rust_2018_idioms warnings"
    )


def test_gen_mod_rs_wires_prost_and_tonic_outputs():
    mod = GEN_DIR / "mod.rs"
    assert mod.is_file(), "src/gen/mod.rs must exist"
    text = _read(mod)
    assert "pub mod monorepo" in text, (
        "gen/mod.rs must declare the monorepo module"
    )
    assert "pub mod v1" in text, "gen/mod.rs must declare the v1 sub-module"
    assert 'include!("monorepo.v1.rs")' in text, (
        "gen/mod.rs must include the prost-generated file"
    )
    assert 'include!("monorepo.v1.tonic.rs")' in text, (
        "gen/mod.rs must include the tonic-generated service file"
    )
    assert 'include_bytes!("file_descriptor_set.bin")' in text, (
        "gen/mod.rs must include the prost-emitted FileDescriptorSet bytes"
    )


def test_gen_gitignore_keeps_mod_rs_only():
    gitignore = GEN_DIR / ".gitignore"
    assert gitignore.is_file(), "src/gen/.gitignore must exist"
    text = _read(gitignore)
    assert "*" in text, ".gitignore must ignore generated artifacts by default"
    assert "!mod.rs" in text, ".gitignore must un-ignore mod.rs"
    assert "!.gitignore" in text, (
        ".gitignore must un-ignore itself so the rule survives a regen"
    )


def test_buf_gen_yaml_targets_match_the_rust_crate_layout():
    text = _read(REPO_ROOT / "buf.gen.yaml")
    assert "rust/crates/monorepo-pb/src/gen" in text, (
        "buf.gen.yaml must still emit Rust output into this crate"
    )


def test_makefile_exposes_rust_targets():
    text = _read(REPO_ROOT / "Makefile")
    for target in ("rust-check:", "rust-clippy:", "rust-test:"):
        assert target in text, f"Makefile is missing Rust target: {target}"
    assert "cargo check" in text, "rust-check must shell out to cargo check"
    assert "cargo clippy" in text and "-D warnings" in text, (
        "rust-clippy must enforce -D warnings"
    )
    assert "cargo test" in text, "rust-test must invoke cargo test"


def test_crate_readme_documents_regeneration_workflow():
    readme = CRATE_ROOT / "README.md"
    assert readme.is_file(), "crate README must exist"
    text = _read(readme)
    assert "buf generate" in text, (
        "crate README must point contributors at the regeneration command"
    )
    assert "cargo check" in text, (
        "crate README must show the post-regeneration verification command"
    )


def test_rust_files_have_no_operator_private_paths():
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    scan_targets = (
        RUST_ROOT / "Cargo.toml",
        RUST_ROOT / "rust-toolchain.toml",
        CRATE_ROOT / "Cargo.toml",
        CRATE_ROOT / "src" / "lib.rs",
        GEN_DIR / "mod.rs",
        CRATE_ROOT / "README.md",
    )
    for path in scan_targets:
        text = _read(path)
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"{path.name} leaks operator-private path: {fragment}"
            )
