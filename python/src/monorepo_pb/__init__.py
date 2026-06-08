"""Public surface of the monorepo.v1 Python bindings.

The actual proto + grpc stub modules live under :mod:`monorepo_pb.gen`
after running ``buf generate`` at the repository root. This top-level
module exposes only the metadata constants that survive a regeneration,
mirroring the Rust crate's :mod:`monorepo_pb` (lib.rs) shape.
"""
from __future__ import annotations

PROTO_PACKAGE: str = "monorepo.v1"

__all__ = ["PROTO_PACKAGE"]
