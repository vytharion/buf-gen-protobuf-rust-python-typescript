.PHONY: help install-buf check-buf lint breaking generate test \
	rust-check rust-test rust-clippy \
	python-install python-check python-lint python-test

help:
	@echo "Targets:"
	@echo "  install-buf     - Download a pinned buf CLI release into ~/.local/bin"
	@echo "  check-buf       - Print the buf version (fails if buf is not on PATH)"
	@echo "  lint            - Run buf lint over the proto workspace"
	@echo "  breaking        - Compare current protos against the main branch"
	@echo "  generate        - Run buf generate using buf.gen.yaml (Rust + Python + TypeScript)"
	@echo "  rust-check      - cargo check the monorepo-pb crate (requires make generate first)"
	@echo "  rust-clippy     - cargo clippy with -D warnings on the Rust workspace"
	@echo "  rust-test       - cargo test the monorepo-pb crate"
	@echo "  python-install  - pip install -e python[dev] (requires make generate first)"
	@echo "  python-check    - smoke-import the monorepo_pb Python package"
	@echo "  python-lint     - ruff check the python subproject"
	@echo "  python-test     - pytest inside the python subproject"
	@echo "  test            - Run pytest against the bootstrap + schema + generator checks"

install-buf:
	./scripts/install-buf.sh

check-buf:
	@buf --version

lint:
	buf lint

breaking:
	buf breaking --against '.git#branch=main'

generate:
	buf generate

rust-check:
	cd rust && cargo check --workspace --all-targets

rust-clippy:
	cd rust && cargo clippy --workspace --all-targets -- -D warnings

rust-test:
	cd rust && cargo test --workspace

python-install:
	cd python && pip install -e .[dev]

python-check:
	cd python && python -c "import monorepo_pb; assert monorepo_pb.PROTO_PACKAGE == 'monorepo.v1'; print(monorepo_pb.PROTO_PACKAGE)"

python-lint:
	cd python && ruff check src

python-test:
	cd python && python -m pytest -q

test:
	pytest -q
