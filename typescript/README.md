# @vytharion/monorepo-pb (TypeScript)

Generated `@bufbuild/protobuf` TypeScript bindings for the
`monorepo.v1` schemas.

The contents of `src/gen/monorepo/v1/` are produced by `buf generate`
at the repository root -- see `buf.gen.yaml`. Run the generator before
importing the package locally:

```bash
make generate
make ts-install
bun run --cwd typescript -e \
  'import { PROTO_PACKAGE } from "./src/index.ts"; console.log(PROTO_PACKAGE);'
```

The package exposes:

- `@vytharion/monorepo-pb` -- the package root re-exports the canonical
  `PROTO_PACKAGE = "monorepo.v1"` constant so consumers can use it for
  reflection / service routing without parsing strings.
- `@vytharion/monorepo-pb/gen/monorepo/v1` -- the generated namespace
  with `Money`, `Account`, `TransferRequest`, `TransferResponse`,
  `GetAccountRequest`, and `GetAccountResponse` message classes emitted
  by the `buf.build/bufbuild/es` plugin (`target=ts`,
  `import_extension=js`).
- Tree-shake-friendly `.ts` sources -- the package ships as TypeScript
  (no pre-built `dist/`), so consumers using `bun`, `vite`, or any
  modern bundler get full type information and dead-code elimination
  out of the box.

Runtime dependencies:

- `@bufbuild/protobuf` -- the runtime that backs every generated
  message class (`Message`, `proto3`, `JsonValue`, etc).

Dev dependencies:

- `@bufbuild/protoc-gen-es` -- optional, kept for contributors who
  want to regenerate stubs locally without invoking the remote
  `buf.build/bufbuild/es` plugin.
- `typescript` -- the `tsc` driver behind `make ts-check`.
- `@types/bun` -- ambient types so `bun test` files type-check under
  strict mode.

The regeneration workflow is:

```bash
make generate         # buf generate -> emits *_pb.ts files
make ts-install       # bun install inside typescript/
make ts-check         # tsc --noEmit across src/
make ts-test          # bun test
```

A fresh checkout shows zero generated files inside
`src/gen/monorepo/v1/`; the per-directory `index.ts` files plus a
single `.gitignore` are the only tracked entries under `gen/`.
