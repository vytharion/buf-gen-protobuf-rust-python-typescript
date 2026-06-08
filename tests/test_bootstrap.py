"""Bootstrap-layer tests for step 1.

These checks lock down the monorepo's skeleton so later steps can rely on
a predictable layout: the buf workspace file points at proto/, every
language subproject has a placeholder directory, and the buf installer
script is present, executable, and pins a specific buf version.
"""
from __future__ import annotations

import os
import stat
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_language_subprojects_exist():
    for sub in ("proto", "rust", "python", "typescript"):
        target = REPO_ROOT / sub
        assert target.is_dir(), f"missing monorepo subdir: {sub}"


def test_buf_workspace_file_lists_proto_directory():
    workspace = REPO_ROOT / "buf.work.yaml"
    assert workspace.is_file(), "buf.work.yaml is required at the repo root"
    text = _read(workspace)
    assert "version: v1" in text
    assert "- proto" in text


def test_install_script_is_executable_and_pins_buf_version():
    script = REPO_ROOT / "scripts" / "install-buf.sh"
    assert script.is_file(), "scripts/install-buf.sh is required"
    mode = script.stat().st_mode
    assert mode & stat.S_IXUSR, "install-buf.sh must be executable"
    text = _read(script)
    assert "BUF_VERSION" in text, "installer must declare a buf version variable"
    assert "bufbuild/buf/releases/download" in text


def test_install_script_has_safe_bash_header():
    script = REPO_ROOT / "scripts" / "install-buf.sh"
    first_line = _read(script).splitlines()[0]
    assert first_line.startswith("#!/usr/bin/env bash")
    body = _read(script)
    assert "set -euo pipefail" in body, "shell script must fail fast"


def test_makefile_exposes_buf_targets():
    makefile = REPO_ROOT / "Makefile"
    assert makefile.is_file(), "Makefile is required"
    text = _read(makefile)
    for target in ("install-buf:", "check-buf:", "test:"):
        assert target in text, f"Makefile is missing target: {target}"


def test_no_operator_private_paths_committed():
    # this test exists to detect leaks, so it deliberately mentions the
    # patterns -- skip scanning itself to avoid a self-referential failure
    forbidden_fragments = ("/Users/", "/app/", "claude_runner")
    shipped_artifacts = (
        REPO_ROOT / "Makefile",
        REPO_ROOT / "buf.work.yaml",
        REPO_ROOT / "scripts" / "install-buf.sh",
        REPO_ROOT / "pyproject.toml",
        REPO_ROOT / "README.md",
    )
    for candidate in shipped_artifacts:
        text = _read(candidate)
        for fragment in forbidden_fragments:
            assert fragment not in text, (
                f"{candidate.name} leaks operator-private path: {fragment}"
            )


def test_environment_supports_python_runner():
    # sanity-check: pytest itself ran us, so this is mostly a stake-in-the-ground
    # documenting the python version contract for step 1's tooling
    import sys
    assert sys.version_info >= (3, 9), "python 3.9+ is required to run these tests"
    assert os.environ.get("PATH"), "PATH must be set for later buf invocations"
