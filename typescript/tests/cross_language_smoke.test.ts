/**
 * Cross-language smoke harness for the TypeScript package.
 *
 * Loads the canonical fixture at `tests/fixtures/cross_language_vector.json`
 * from the repo root, builds a `monorepo.v1.Money` with the pinned field
 * values via the generated `money_pb` stub, encodes it through the
 * `@bufbuild/protobuf` runtime, and compares the on-wire bytes against
 * the hex blob in the fixture. Decoding those bytes back must reproduce
 * the original field values. The Rust and Python harnesses run the
 * identical check; together they guarantee the three runtimes interop on
 * the same byte sequence.
 *
 * This test is skipped automatically when `buf generate` has not yet
 * populated `src/gen/monorepo/v1`. CI runs `make generate` first so the
 * skip branch only fires for fresh local clones.
 */
import { describe, expect, it } from "bun:test";
import { readFileSync, existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(__dirname, "..", "..");
const VECTOR_PATH = resolve(REPO_ROOT, "tests", "fixtures", "cross_language_vector.json");
const GENERATED_MONEY_PATH = resolve(
  REPO_ROOT,
  "typescript",
  "src",
  "gen",
  "monorepo",
  "v1",
  "money_pb.ts",
);

interface CrossLanguageVector {
  proto_package: string;
  money: { currency_code: string; amount_minor_units: number };
  account: { id: string; display_name: string };
  money_wire_bytes_hex: string;
}

function loadVector(): CrossLanguageVector {
  return JSON.parse(readFileSync(VECTOR_PATH, "utf-8")) as CrossLanguageVector;
}

function hexToBytes(hex: string): Uint8Array {
  const out = new Uint8Array(hex.length / 2);
  for (let i = 0; i < hex.length; i += 2) {
    out[i / 2] = Number.parseInt(hex.slice(i, i + 2), 16);
  }
  return out;
}

describe("cross-language smoke (TypeScript)", () => {
  it("locates the canonical vector fixture", () => {
    expect(existsSync(VECTOR_PATH)).toBe(true);
  });

  it("round-trips Money against the canonical wire bytes", async () => {
    if (!existsSync(GENERATED_MONEY_PATH)) {
      console.warn(
        "skipping: generated money_pb.ts unavailable; run `make generate` first",
      );
      return;
    }

    const mod = (await import(GENERATED_MONEY_PATH)) as {
      Money: new (init?: {
        currencyCode?: string;
        amountMinorUnits?: bigint;
      }) => {
        toBinary: () => Uint8Array;
        currencyCode: string;
        amountMinorUnits: bigint;
        fromBinary: (bytes: Uint8Array) => unknown;
      };
    };

    const vector = loadVector();
    const original = new mod.Money({
      currencyCode: vector.money.currency_code,
      amountMinorUnits: BigInt(vector.money.amount_minor_units),
    });

    const encoded = original.toBinary();
    const expected = hexToBytes(vector.money_wire_bytes_hex);
    expect(Array.from(encoded)).toEqual(Array.from(expected));

    const Money = mod.Money as unknown as {
      fromBinary: (bytes: Uint8Array) => {
        currencyCode: string;
        amountMinorUnits: bigint;
      };
    };
    const decoded = Money.fromBinary(encoded);
    expect(decoded.currencyCode).toBe(vector.money.currency_code);
    expect(decoded.amountMinorUnits).toBe(
      BigInt(vector.money.amount_minor_units),
    );
  });
});
