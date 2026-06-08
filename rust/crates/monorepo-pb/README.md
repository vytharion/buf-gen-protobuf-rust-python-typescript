# monorepo-pb

Generated prost + tonic bindings for the `monorepo.v1` schemas.

The contents of `src/gen/` are produced by `buf generate` at the
repository root — see `buf.gen.yaml`. Run the generator before
building the crate locally:

```bash
make generate
cargo check -p monorepo-pb
```

The crate exposes three things:

- `monorepo_pb::v1` — every prost-generated message struct (`Money`,
  `Account`, `TransferRequest`, ...).
- `monorepo_pb::v1::ledger_service_server` and
  `monorepo_pb::v1::ledger_service_client` — tonic service stubs
  produced by `neoeinstein-tonic`.
- `monorepo_pb::FILE_DESCRIPTOR_SET` — the encoded `FileDescriptorSet`,
  ready to hand to `tonic-reflection`.
