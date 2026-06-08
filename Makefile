.PHONY: help install-buf check-buf lint breaking test

help:
	@echo "Targets:"
	@echo "  install-buf  - Download a pinned buf CLI release into ~/.local/bin"
	@echo "  check-buf    - Print the buf version (fails if buf is not on PATH)"
	@echo "  lint         - Run buf lint over the proto workspace"
	@echo "  breaking     - Compare current protos against the main branch"
	@echo "  test         - Run pytest against the bootstrap + schema checks"

install-buf:
	./scripts/install-buf.sh

check-buf:
	@buf --version

lint:
	buf lint

breaking:
	buf breaking --against '.git#branch=main'

test:
	pytest -q
