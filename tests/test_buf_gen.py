"""Generator-config tests for step 3.

Lock down the shape of ``buf.gen.yaml`` so a single ``buf generate``
invocation fans the shared ``monorepo.v1`` schemas out into three
language targets: Rust (prost + tonic), Python (the official
protocolbuffers + grpc plugins), and TypeScript (``@bufbuild/protobuf``
via ``buf.build/bufbuild/es``).

Every assertion fires against file content directly, so the suite stays
green even when ``buf`` is not installed -- mirroring step 2's approach.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
GEN_CONFIG = REPO_ROOT / "buf.gen.yaml"

RUST_OUT_DIR = "rust/crates/monorepo-pb/src/gen"
PYTHON_OUT_DIR = "python/src/monorepo_pb/gen"
TYPESCRIPT_OUT_DIR = "typescript/src/gen"

REQUIRED_PLUGINS = (
    "buf.build/community/neoeinstein-prost",
    "buf.build/community/neoeinstein-tonic",
    "buf.build/protocolbuffers/python",
    "buf.build/grpc/python",
    "buf.build/bufbuild/es",
)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _plugin_blocks(text: str) -> list[str]:
    """Return one string per ``- plugin:`` block in buf.gen.yaml."""
    lines = text.splitlines()
    blocks: list[list[str]] = []
    current: list[str] = []
    for line in lines:
        if line.startswith("  - plugin:"):
            if current:
                blocks.append(current)
            current = [line]
        elif current and (line.startswith("    ") or line == ""):
            current.append(line)
        elif current:
            blocks.append(current)
            current = []
    if current:
        blocks.append(current)
    return ["\n".join(block) for block in blocks]


def _block_for(plugin_name: str, blocks: list[str]) -> str:
    for block in blocks:
        if plugin_name in block:
            return block
    raise AssertionError(f"plugin block not found for {plugin_name}")


def test_buf_gen_yaml_exists_at_repo_root():
    assert GEN_CONFIG.is_file(), "buf.gen.yaml must live at the repo root"


def test_buf_gen_yaml_declares_v1_with_managed_mode():
    text = _read(GEN_CONFIG)
    assert "version: v1" in text, "buf.gen.yaml must declare version v1"
    assert "managed:" in text, "managed-mode block is required"
    assert "enabled: true" in text, "managed mode must be enabled"


def test_managed_go_package_prefix_lives_under_vytharion_namespace():
    text = _read(GEN_CONFIG)
    match = re.search(
        r"go_package_prefix:\s*\n\s*default:\s*(\S+)", text
    )
    assert match, "managed.go_package_prefix.default must be set"
    prefix = match.group(1)
    assert prefix.startswith(
        "github.com/vytharion/buf-gen-protobuf-rust-python-typescript"
    ), f"go_package_prefix must point at the public vytharion repo, got {prefix!r}"


def test_every_required_plugin_is_declared():
    text = _read(GEN_CONFIG)
    for plugin in REQUIRED_PLUGINS:
        assert plugin in text, f"buf.gen.yaml is missing plugin: {plugin}"


def test_each_plugin_has_its_own_out_directory():
    text = _read(GEN_CONFIG)
    blocks = _plugin_blocks(text)
    assert len(blocks) == len(REQUIRED_PLUGINS), (
        f"expected {len(REQUIRED_PLUGINS)} plugin blocks, found {len(blocks)}"
    )
    for block in blocks:
        assert re.search(r"out:\s*\S+", block), (
            f"plugin block missing `out:` directive:\n{block}"
        )


def test_rust_plugins_share_a_single_output_tree():
    text = _read(GEN_CONFIG)
    blocks = _plugin_blocks(text)
    prost_block = _block_for("neoeinstein-prost", blocks)
    tonic_block = _block_for("neoeinstein-tonic", blocks)
    assert RUST_OUT_DIR in prost_block, (
        "prost plugin must emit into the Rust crate's gen module"
    )
    assert RUST_OUT_DIR in tonic_block, (
        "tonic plugin must emit alongside prost so the service stubs share state"
    )


def test_python_plugins_share_a_single_output_tree():
    text = _read(GEN_CONFIG)
    blocks = _plugin_blocks(text)
    py_block = _block_for("protocolbuffers/python", blocks)
    grpc_block = _block_for("grpc/python", blocks)
    assert PYTHON_OUT_DIR in py_block, (
        "protocolbuffers/python must emit into python/src/monorepo_pb/gen"
    )
    assert PYTHON_OUT_DIR in grpc_block, (
        "grpc/python must emit alongside the message stubs"
    )


def test_typescript_plugin_targets_bufbuild_es_with_ts_output():
    text = _read(GEN_CONFIG)
    blocks = _plugin_blocks(text)
    es_block = _block_for("bufbuild/es", blocks)
    assert TYPESCRIPT_OUT_DIR in es_block, (
        "TypeScript plugin must emit into typescript/src/gen"
    )
    assert "target=ts" in es_block, (
        "bufbuild/es must be invoked with target=ts so we ship .ts sources"
    )


def test_rust_plugins_enable_well_known_type_compilation():
    text = _read(GEN_CONFIG)
    blocks = _plugin_blocks(text)
    prost_block = _block_for("neoeinstein-prost", blocks)
    tonic_block = _block_for("neoeinstein-tonic", blocks)
    assert "compile_well_known_types" in prost_block, (
        "prost must compile WKT so google.protobuf.Timestamp resolves"
    )
    assert "compile_well_known_types" in tonic_block, (
        "tonic must compile WKT to match prost's view of the schemas"
    )


def test_makefile_exposes_generate_target():
    makefile = REPO_ROOT / "Makefile"
    text = _read(makefile)
    assert "generate:" in text, "Makefile is missing the generate target"
    assert "buf generate" in text, (
        "generate target must invoke `buf generate`"
    )


def test_output_directories_live_under_language_subprojects():
    for relpath in (RUST_OUT_DIR, PYTHON_OUT_DIR, TYPESCRIPT_OUT_DIR):
        top = relpath.split("/", 1)[0]
        assert (REPO_ROOT / top).is_dir(), (
            f"output dir {relpath} requires {top}/ subproject to exist"
        )


def test_buf_gen_yaml_has_no_operator_private_paths():
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    text = _read(GEN_CONFIG)
    for fragment in forbidden_fragments:
        assert fragment not in text, (
            f"buf.gen.yaml leaks operator-private path: {fragment}"
        )
