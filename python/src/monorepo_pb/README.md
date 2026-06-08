# monorepo-pb (Python)

Generated `protobuf` + `grpc` Python bindings for the `monorepo.v1`
schemas.

The contents of `src/monorepo_pb/gen/monorepo/v1/` are produced by
`buf generate` at the repository root -- see `buf.gen.yaml`. Run the
generator before importing the package locally:

```bash
make generate
make python-install
python -c "from monorepo_pb.gen.monorepo.v1 import money_pb2; print(money_pb2.Money.DESCRIPTOR.full_name)"
```

The package exposes:

- `monorepo_pb.PROTO_PACKAGE` -- the canonical proto package name
  (`"monorepo.v1"`), kept as a module-level constant so consumers can
  use it for reflection / service discovery without parsing strings.
- `monorepo_pb.gen.monorepo.v1` -- the generated namespace with
  `money_pb2`, `ledger_pb2`, and `ledger_pb2_grpc` modules.
- A `py.typed` marker (PEP 561) so `mypy --strict` consumers pick up
  the inline type stubs that `protoc-gen-python` and `mypy-protobuf`
  emit alongside the `*_pb2.py` files.

The regeneration workflow is:

```bash
make generate         # buf generate -> emits *_pb2.py / *_pb2_grpc.py
make python-check     # smoke-imports the package
make python-test      # pytest inside the python/ subproject
```

A fresh checkout shows zero generated files inside
`src/monorepo_pb/gen/monorepo/v1/`; the per-directory `__init__.py`
files plus a single `.gitignore` are the only tracked entries under
`gen/`.
