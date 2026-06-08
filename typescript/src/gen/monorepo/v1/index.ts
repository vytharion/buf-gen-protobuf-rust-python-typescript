/**
 * Namespace marker for the `monorepo.v1` proto package.
 *
 * The `money_pb.ts` and `ledger_pb.ts` sibling modules are emitted by
 * `buf generate` and intentionally not re-exported here -- doing so
 * would make module import order depend on the generator having
 * already run.
 *
 * After `buf generate` has been invoked, consumers import the
 * generated symbols directly from the sibling files:
 *
 *     import { Money } from "@vytharion/monorepo-pb/gen/monorepo/v1/money_pb.js";
 */

export {};
