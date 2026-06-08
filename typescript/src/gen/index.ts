/**
 * Wiring for `buf generate` output (TypeScript target).
 *
 * The `*_pb.ts` files under `monorepo/v1/` are emitted by the
 * `buf.build/bufbuild/es` plugin and overwritten on every regeneration.
 * The hand-written `index.ts` files at each level of the namespace
 * (`gen/`, `gen/monorepo/`, `gen/monorepo/v1/`) are intentionally
 * minimal so they survive a regen-and-diff cycle untouched.
 *
 * Once `buf generate` has run, consumers can reach the message classes
 * through the proto package path:
 *
 *     import { Money } from "@vytharion/monorepo-pb/gen/monorepo/v1";
 */

export {};
