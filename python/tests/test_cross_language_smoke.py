"""Cross-language smoke harness for the Python package.

Loads the canonical fixture at ``tests/fixtures/cross_language_vector.json``
from the repo root, builds a ``monorepo.v1.Money`` with the pinned field
values via the generated ``money_pb2`` stub, encodes it through the
official protobuf runtime, and compares the on-wire bytes against the
hex blob in the fixture. Decoding those bytes back must reproduce the
original field values. The Rust and TypeScript harnesses run the
identical check; together they guarantee the three runtimes interoperate
on the same byte sequence.

This test is skipped automatically when ``buf generate`` has not yet
populated ``monorepo_pb.gen``. CI runs ``make generate`` first so the
skip branch only fires for fresh local clones.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
VECTOR_PATH = REPO_ROOT / "tests" / "fixtures" / "cross_language_vector.json"


def _load_vector() -> dict:
    return json.loads(VECTOR_PATH.read_text(encoding="utf-8"))


def _money_module():
    try:
        from monorepo_pb.gen.monorepo.v1 import money_pb2  # type: ignore[import-not-found]
    except ImportError:
        pytest.skip(
            "monorepo_pb.gen.monorepo.v1.money_pb2 unavailable; run `make generate`"
            " and `make python-install` before this harness",
        )
    return money_pb2


def test_vector_fixture_is_present():
    assert VECTOR_PATH.is_file(), (
        f"canonical cross-language vector must live at {VECTOR_PATH}"
    )


def test_money_round_trips_against_canonical_vector():
    vector = _load_vector()
    money_pb2 = _money_module()

    original = money_pb2.Money(
        currency_code=vector["money"]["currency_code"],
        amount_minor_units=vector["money"]["amount_minor_units"],
    )
    encoded = original.SerializeToString()
    expected = bytes.fromhex(vector["money_wire_bytes_hex"])
    assert encoded == expected, (
        "Python protobuf encoding diverged from the canonical wire bytes"
    )

    decoded = money_pb2.Money()
    decoded.ParseFromString(encoded)
    assert decoded.currency_code == vector["money"]["currency_code"]
    assert decoded.amount_minor_units == vector["money"]["amount_minor_units"]
