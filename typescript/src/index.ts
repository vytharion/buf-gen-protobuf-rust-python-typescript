/**
 * Public surface of the monorepo.v1 TypeScript bindings.
 *
 * The actual message classes live under `./gen/monorepo/v1` after
 * running `buf generate` at the repository root. This entrypoint
 * exposes only the metadata constants that survive a regeneration,
 * mirroring the Rust crate's `lib.rs` and the Python package's
 * `__init__.py` shape.
 *
 * Once `buf generate` has run, consumers can reach the message classes
 * with an explicit subpath:
 *
 *     import { Money, Account } from "@vytharion/monorepo-pb/gen/monorepo/v1";
 */

export const PROTO_PACKAGE = "monorepo.v1" as const;

export type ProtoPackage = typeof PROTO_PACKAGE;
