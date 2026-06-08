"""TypeScript-wiring tests for step 6.

Lock down the shape of the ``@vytharion/monorepo-pb`` TypeScript package
so a fresh ``buf generate`` followed by ``bun install`` will type-check
without hand-tweaking. Every assertion reads file contents directly so
the suite stays green on a machine that has no ``buf``, ``bun``, or
generated ``.ts`` stubs on disk -- matching the bootstrap, schema,
generator, Rust-wiring, and Python-wiring phases before it.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TS_ROOT = REPO_ROOT / "typescript"
PACKAGE_ROOT = TS_ROOT / "src"
GEN_DIR = PACKAGE_ROOT / "gen"
GEN_V1_DIR = GEN_DIR / "monorepo" / "v1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _read_package_json() -> dict:
    return json.loads(_read(TS_ROOT / "package.json"))


def test_typescript_subproject_uses_src_layout():
    assert TS_ROOT.is_dir(), "typescript/ subproject must exist"
    assert PACKAGE_ROOT.is_dir(), "typescript/src/ src-layout root required"
    assert GEN_DIR.is_dir(), "typescript/src/gen/ generated-output root required"


def test_typescript_subproject_does_not_carry_legacy_gitkeep():
    assert not (TS_ROOT / ".gitkeep").exists(), (
        "the bootstrap .gitkeep must be removed once real files land"
    )


def test_package_json_exists_with_expected_metadata():
    pkg = TS_ROOT / "package.json"
    assert pkg.is_file(), "typescript/package.json must exist"
    data = _read_package_json()
    assert data.get("name") == "@vytharion/monorepo-pb", (
        "package name must be @vytharion/monorepo-pb"
    )
    assert data.get("version") == "0.1.0", "package version must be 0.1.0"
    assert data.get("type") == "module", (
        "package must declare ESM via \"type\": \"module\""
    )
    assert data.get("license") == "MIT", "package must declare MIT license"


def test_package_json_declares_protobuf_runtime_dependency():
    data = _read_package_json()
    deps = data.get("dependencies", {})
    assert "@bufbuild/protobuf" in deps, (
        "package must depend on @bufbuild/protobuf at runtime"
    )
    version = deps["@bufbuild/protobuf"]
    assert re.match(r"^\^?(?:1|2)\.", version), (
        "@bufbuild/protobuf must be pinned to the 1.x or 2.x series, "
        f"got {version!r}"
    )


def test_package_json_declares_dev_extras_for_codegen_and_typecheck():
    data = _read_package_json()
    dev = data.get("devDependencies", {})
    for dep in ("@bufbuild/protoc-gen-es", "typescript", "@types/bun"):
        assert dep in dev, f"devDependencies must include {dep}"


def test_package_json_exposes_module_and_types_entrypoints():
    data = _read_package_json()
    assert data.get("main"), "package.json must declare a main entrypoint"
    assert data.get("module"), "package.json must declare a module entrypoint"
    assert data.get("types"), "package.json must declare a types entrypoint"
    exports = data.get("exports")
    assert isinstance(exports, dict), "package.json must declare exports map"
    assert "." in exports, "exports must expose the package root via '.'"


def test_package_json_scripts_cover_typecheck_lint_and_test():
    data = _read_package_json()
    scripts = data.get("scripts", {})
    for name in ("check", "lint", "test", "build"):
        assert name in scripts, f"package.json scripts must include {name!r}"
    assert "tsc" in scripts["check"], (
        "check script must invoke tsc for type-checking"
    )
    assert "bun test" in scripts["test"], (
        "test script must invoke bun test (not npm/jest)"
    )


def test_package_json_engine_pins_modern_node_and_bun():
    data = _read_package_json()
    engines = data.get("engines", {})
    assert "node" in engines, "package.json must declare a node engine floor"
    assert "bun" in engines, "package.json must declare a bun engine floor"


def test_tsconfig_enables_strict_mode_and_targets_esnext():
    tsconfig_path = TS_ROOT / "tsconfig.json"
    assert tsconfig_path.is_file(), "typescript/tsconfig.json must exist"
    text = _read(tsconfig_path)
    assert '"strict": true' in text, "tsconfig must enable strict mode"
    assert '"target":' in text, "tsconfig must pin a compile target"
    assert '"module":' in text, "tsconfig must pin a module system"
    assert '"moduleResolution":' in text, (
        "tsconfig must pin a moduleResolution strategy"
    )
    assert '"rootDir": "src"' in text, "tsconfig rootDir must be src/"
    assert '"outDir":' in text, "tsconfig must declare an outDir for build output"


def test_tsconfig_includes_only_src_tree():
    text = _read(TS_ROOT / "tsconfig.json")
    assert '"include":' in text, "tsconfig must declare an include array"
    assert '"src"' in text, "tsconfig include must scan src/"
    assert '"exclude":' in text, "tsconfig must declare an exclude array"
    assert "node_modules" in text, "tsconfig must exclude node_modules"


def test_top_level_index_exposes_proto_package_const():
    index = PACKAGE_ROOT / "index.ts"
    assert index.is_file(), "src/index.ts must exist"
    text = _read(index)
    assert re.search(
        r'export\s+const\s+PROTO_PACKAGE\s*(?::\s*[^=]+)?=\s*"monorepo\.v1"',
        text,
    ), "src/index.ts must export PROTO_PACKAGE = \"monorepo.v1\""


def test_top_level_index_does_not_eager_import_generated_stubs():
    """Importing a generated ``*_pb`` module at the package entrypoint
    would make ``bun install`` order depend on ``buf generate`` having
    already run, which breaks a fresh clone. The regex tolerates
    references inside JSDoc comments (which start with ``*``) but
    rejects real import statements at column 0."""
    text = _read(PACKAGE_ROOT / "index.ts")
    pb_import_re = re.compile(
        r"^\s*import\s+[^;]*_pb(?:\s|;|/|\")", re.MULTILINE
    )
    assert not pb_import_re.search(text), (
        "src/index.ts must not eager-import generated *_pb modules"
    )


def test_gen_index_documents_regeneration_contract():
    index = GEN_DIR / "index.ts"
    assert index.is_file(), "src/gen/index.ts must exist"
    text = _read(index)
    assert "buf generate" in text, (
        "gen/index.ts must reference the buf generate workflow"
    )
    assert "monorepo/v1" in text, (
        "gen/index.ts must document the consumer import path"
    )


def test_gen_namespace_index_files_exist():
    namespace_index = GEN_DIR / "monorepo" / "index.ts"
    v1_index = GEN_V1_DIR / "index.ts"
    assert namespace_index.is_file(), (
        "gen/monorepo/index.ts must exist as a namespace marker"
    )
    assert v1_index.is_file(), (
        "gen/monorepo/v1/index.ts must exist as a namespace marker"
    )


def test_gen_namespace_indexes_do_not_eager_import_generated_stubs():
    """A real (non-comment) import of a ``*_pb`` module at namespace
    load time would make package import order depend on ``buf generate``
    having already run, which breaks ``bun install`` on a fresh
    checkout. The ``^`` anchor with MULTILINE rejects only statements
    that start at column 0 -- example snippets inside ``/** ... */``
    JSDoc blocks (which start with ``*``) are fine."""
    pb_import_re = re.compile(
        r"^\s*import\s+[^;]*_pb(?:\s|;|/|\")", re.MULTILINE
    )
    for index_path in (
        GEN_DIR / "index.ts",
        GEN_DIR / "monorepo" / "index.ts",
        GEN_V1_DIR / "index.ts",
    ):
        text = _read(index_path)
        assert not pb_import_re.search(text), (
            f"{index_path} must not eager-import generated stubs"
        )


def test_gen_gitignore_preserves_index_files_at_every_level():
    gitignore = GEN_DIR / ".gitignore"
    assert gitignore.is_file(), "gen/.gitignore must exist"
    text = _read(gitignore)
    assert "*" in text, ".gitignore must ignore generated artifacts by default"
    for keeper in (
        "!.gitignore",
        "!index.ts",
        "!monorepo",
        "!monorepo/index.ts",
        "!monorepo/v1",
        "!monorepo/v1/index.ts",
    ):
        assert keeper in text, (
            f"gen/.gitignore must explicitly preserve `{keeper}`"
        )


def test_buf_gen_yaml_targets_match_the_typescript_package_layout():
    text = _read(REPO_ROOT / "buf.gen.yaml")
    assert "typescript/src/gen" in text, (
        "buf.gen.yaml must still emit TypeScript output into this package"
    )
    assert "buf.build/bufbuild/es" in text, (
        "buf.gen.yaml must invoke the official bufbuild/es plugin"
    )
    assert "target=ts" in text, (
        "buf.gen.yaml must invoke bufbuild/es with target=ts"
    )


def test_makefile_exposes_typescript_targets():
    text = _read(REPO_ROOT / "Makefile")
    for target in ("ts-install:", "ts-check:", "ts-lint:", "ts-test:"):
        assert target in text, f"Makefile is missing TypeScript target: {target}"
    assert "bun install" in text, (
        "ts-install must invoke `bun install`"
    )
    assert "bun test" in text, "ts-test must invoke `bun test`"
    assert "tsc" in text, "ts-check must shell out to tsc for type-checking"


def test_package_readme_documents_regeneration_workflow():
    readme = TS_ROOT / "README.md"
    assert readme.is_file(), "typescript package README must exist"
    text = _read(readme)
    assert "buf generate" in text, (
        "package README must point contributors at the regeneration command"
    )
    assert "bun install" in text or "ts-install" in text, (
        "package README must show the install workflow"
    )
    assert "@bufbuild/protobuf" in text, (
        "package README must mention the @bufbuild/protobuf runtime"
    )


def test_typescript_files_have_no_operator_private_paths():
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    scan_targets = (
        TS_ROOT / "package.json",
        TS_ROOT / "tsconfig.json",
        TS_ROOT / "README.md",
        PACKAGE_ROOT / "index.ts",
        GEN_DIR / "index.ts",
        GEN_DIR / "monorepo" / "index.ts",
        GEN_V1_DIR / "index.ts",
        GEN_DIR / ".gitignore",
    )
    for path in scan_targets:
        text = _read(path)
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"{path.name} leaks operator-private path: {fragment}"
            )
