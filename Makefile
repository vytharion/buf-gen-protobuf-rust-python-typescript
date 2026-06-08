.PHONY: help install-buf check-buf test

help:
	@echo "Targets:"
	@echo "  install-buf  - Download a pinned buf CLI release into ~/.local/bin"
	@echo "  check-buf    - Print the buf version (fails if buf is not on PATH)"
	@echo "  test         - Run pytest against the bootstrap checks"

install-buf:
	./scripts/install-buf.sh

check-buf:
	@buf --version

test:
	pytest -q
