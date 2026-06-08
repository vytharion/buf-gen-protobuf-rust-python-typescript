"""Python-wiring tests for step 5.

Lock down the shape of the ``monorepo_pb`` Python package so a fresh
``buf generate`` followed by ``pip install -e python`` will import
without hand-tweaking. Every assertion reads file contents directly so
the suite stays green on a machine that has no ``buf``, ``pip``, or
generated stubs on disk -- matching the bootstrap, schema, generator,
and Rust-wiring phases before it.
"""
from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYTHON_ROOT = REPO_ROOT / "python"
PACKAGE_ROOT = PYTHON_ROOT / "src" / "monorepo_pb"
GEN_DIR = PACKAGE_ROOT / "gen"
GEN_V1_DIR = GEN_DIR / "monorepo" / "v1"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_python_subproject_uses_src_layout():
    assert PYTHON_ROOT.is_dir(), "python/ subproject must exist"
    assert (PYTHON_ROOT / "src").is_dir(), "python/src/ src-layout root required"
    assert PACKAGE_ROOT.is_dir(), "python/src/monorepo_pb/ package required"


def test_pyproject_toml_exists_with_expected_metadata():
    pyproject = PYTHON_ROOT / "pyproject.toml"
    assert pyproject.is_file(), "python/pyproject.toml must exist"
    text = _read(pyproject)
    assert 'name = "monorepo-pb"' in text, "project name must be monorepo-pb"
    assert re.search(r'requires-python\s*=\s*">=3\.9"', text), (
        "package must declare requires-python >= 3.9"
    )
    assert 'authors = [{ name = "vytharion" }]' in text, (
        "authors must list vytharion (public identity)"
    )


def test_pyproject_declares_protobuf_and_grpcio_dependencies():
    text = _read(PYTHON_ROOT / "pyproject.toml")
    assert re.search(r'"protobuf>=4\.\d+,<6"', text), (
        "package must pin protobuf to the 4.x/5.x series"
    )
    assert re.search(r'"grpcio>=1\.\d+"', text), (
        "package must depend on grpcio (1.60+)"
    )


def test_pyproject_declares_dev_extras_for_codegen_and_lint():
    text = _read(PYTHON_ROOT / "pyproject.toml")
    for dep in ("grpcio-tools", "mypy", "mypy-protobuf", "ruff"):
        assert dep in text, f"dev extras must include {dep}"


def test_pyproject_uses_setuptools_src_layout():
    text = _read(PYTHON_ROOT / "pyproject.toml")
    assert "[tool.setuptools.packages.find]" in text, (
        "pyproject must declare setuptools.packages.find"
    )
    assert 'where = ["src"]' in text, "setuptools must scan the src/ layout"
    assert '"monorepo_pb"' in text, "package-data must target monorepo_pb"


def test_pyproject_declares_pep517_build_backend():
    text = _read(PYTHON_ROOT / "pyproject.toml")
    assert "[build-system]" in text, "pyproject must declare [build-system]"
    assert "setuptools" in text, "build backend must be setuptools"
    assert 'build-backend = "setuptools.build_meta"' in text, (
        "build-backend must be setuptools.build_meta"
    )


def test_pyproject_enables_mypy_strict():
    text = _read(PYTHON_ROOT / "pyproject.toml")
    assert "[tool.mypy]" in text, "pyproject must configure mypy"
    assert "strict = true" in text, "mypy must run in strict mode"


def test_top_level_init_exposes_proto_package_const():
    init = PACKAGE_ROOT / "__init__.py"
    assert init.is_file(), "src/monorepo_pb/__init__.py must exist"
    text = _read(init)
    assert 'PROTO_PACKAGE: str = "monorepo.v1"' in text, (
        "__init__.py must pin the proto package name as a typed const"
    )
    assert '"PROTO_PACKAGE"' in text, (
        "PROTO_PACKAGE must be exported via __all__"
    )


def test_package_carries_pep561_typed_marker():
    marker = PACKAGE_ROOT / "py.typed"
    assert marker.is_file(), "PEP 561 py.typed marker file must exist"
    assert marker.read_bytes() == b"", (
        "py.typed must be an empty marker file"
    )


def test_gen_init_documents_regeneration_contract():
    init = GEN_DIR / "__init__.py"
    assert init.is_file(), "src/monorepo_pb/gen/__init__.py must exist"
    text = _read(init)
    assert "buf generate" in text, (
        "gen/__init__.py must reference the buf generate workflow"
    )
    assert "monorepo_pb.gen.monorepo.v1" in text, (
        "gen/__init__.py must document the consumer import path"
    )


def test_gen_namespace_init_files_exist():
    namespace_init = GEN_DIR / "monorepo" / "__init__.py"
    v1_init = GEN_V1_DIR / "__init__.py"
    assert namespace_init.is_file(), (
        "gen/monorepo/__init__.py must exist as a namespace marker"
    )
    assert v1_init.is_file(), (
        "gen/monorepo/v1/__init__.py must exist as a namespace marker"
    )


def test_gen_namespace_inits_do_not_eager_import_generated_stubs():
    """A real (non-docstring) import of a `*_pb2` module at package
    load time would make import order depend on `buf generate` having
    already run, which breaks `pip install -e python` on a fresh
    checkout. The `^` anchor with MULTILINE rejects only statements
    that start at column 0 -- indented examples inside docstrings are
    fine."""
    pb2_import_re = re.compile(
        r"^(?:from\s+\S+\s+)?import\s+[\w,\s]*_pb2", re.MULTILINE
    )
    for init_path in (
        GEN_DIR / "__init__.py",
        GEN_DIR / "monorepo" / "__init__.py",
        GEN_V1_DIR / "__init__.py",
    ):
        text = _read(init_path)
        assert not pb2_import_re.search(text), (
            f"{init_path} must not eager-import generated stubs"
        )


def test_gen_gitignore_preserves_init_files_at_every_level():
    gitignore = GEN_DIR / ".gitignore"
    assert gitignore.is_file(), "gen/.gitignore must exist"
    text = _read(gitignore)
    assert "*" in text, ".gitignore must ignore generated artifacts by default"
    for keeper in (
        "!.gitignore",
        "!__init__.py",
        "!monorepo",
        "!monorepo/__init__.py",
        "!monorepo/v1",
        "!monorepo/v1/__init__.py",
    ):
        assert keeper in text, (
            f"gen/.gitignore must explicitly preserve `{keeper}`"
        )


def test_buf_gen_yaml_targets_match_the_python_package_layout():
    text = _read(REPO_ROOT / "buf.gen.yaml")
    assert "python/src/monorepo_pb/gen" in text, (
        "buf.gen.yaml must still emit Python output into this package"
    )
    assert "buf.build/protocolbuffers/python" in text, (
        "buf.gen.yaml must invoke the official protobuf python plugin"
    )
    assert "buf.build/grpc/python" in text, (
        "buf.gen.yaml must invoke the official grpc/python plugin"
    )


def test_makefile_exposes_python_targets():
    text = _read(REPO_ROOT / "Makefile")
    for target in ("python-install:", "python-check:", "python-lint:", "python-test:"):
        assert target in text, f"Makefile is missing Python target: {target}"
    assert "pip install -e .[dev]" in text, (
        "python-install must invoke `pip install -e .[dev]`"
    )
    assert "import monorepo_pb" in text, (
        "python-check must smoke-import the monorepo_pb package"
    )
    assert "ruff check" in text, "python-lint must shell out to ruff check"
    assert "python -m pytest" in text, (
        "python-test must invoke `python -m pytest`"
    )


def test_package_readme_documents_regeneration_workflow():
    readme = PACKAGE_ROOT / "README.md"
    assert readme.is_file(), "python package README must exist"
    text = _read(readme)
    assert "buf generate" in text, (
        "package README must point contributors at the regeneration command"
    )
    assert "pip install" in text or "python-install" in text, (
        "package README must show the install workflow"
    )
    assert "py.typed" in text, (
        "package README must mention the PEP 561 marker"
    )


def test_python_files_have_no_operator_private_paths():
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    scan_targets = (
        PYTHON_ROOT / "pyproject.toml",
        PACKAGE_ROOT / "__init__.py",
        PACKAGE_ROOT / "README.md",
        GEN_DIR / "__init__.py",
        GEN_DIR / "monorepo" / "__init__.py",
        GEN_V1_DIR / "__init__.py",
        GEN_DIR / ".gitignore",
    )
    for path in scan_targets:
        text = _read(path)
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"{path.name} leaks operator-private path: {fragment}"
            )
