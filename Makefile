.PHONY: help install-buf check-buf lint breaking generate test

help:
	@echo "Targets:"
	@echo "  install-buf  - Download a pinned buf CLI release into ~/.local/bin"
	@echo "  check-buf    - Print the buf version (fails if buf is not on PATH)"
	@echo "  lint         - Run buf lint over the proto workspace"
	@echo "  breaking     - Compare current protos against the main branch"
	@echo "  generate     - Run buf generate using buf.gen.yaml (Rust + Python + TypeScript)"
	@echo "  test         - Run pytest against the bootstrap + schema + generator checks"

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

test:
	pytest -q
