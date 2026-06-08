#!/usr/bin/env bash
set -euo pipefail

# Pin a known-good buf release so generated code is reproducible across
# the rust / python / typescript subprojects.
BUF_VERSION="${BUF_VERSION:-1.50.0}"
INSTALL_DIR="${INSTALL_DIR:-${HOME}/.local/bin}"

detect_os() {
  case "$(uname -s)" in
    Linux*)  echo "Linux" ;;
    Darwin*) echo "Darwin" ;;
    *) echo "unsupported" ;;
  esac
}

detect_arch() {
  case "$(uname -m)" in
    x86_64|amd64) echo "x86_64" ;;
    arm64|aarch64) echo "aarch64" ;;
    *) echo "unsupported" ;;
  esac
}

main() {
  local os arch url
  os="$(detect_os)"
  arch="$(detect_arch)"
  if [ "${os}" = "unsupported" ] || [ "${arch}" = "unsupported" ]; then
    echo "Unsupported platform: $(uname -s) $(uname -m)" >&2
    exit 1
  fi
  url="https://github.com/bufbuild/buf/releases/download/v${BUF_VERSION}/buf-${os}-${arch}"
  mkdir -p "${INSTALL_DIR}"
  echo "Downloading buf v${BUF_VERSION} (${os}/${arch}) -> ${INSTALL_DIR}/buf"
  curl -fsSL "${url}" -o "${INSTALL_DIR}/buf"
  chmod +x "${INSTALL_DIR}/buf"
  echo "Installed: $(${INSTALL_DIR}/buf --version 2>&1)"
}

main "$@"
