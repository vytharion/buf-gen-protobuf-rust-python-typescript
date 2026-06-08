"""Wiring for ``buf generate`` output.

The ``*_pb2.py`` and ``*_pb2_grpc.py`` files under ``monorepo/v1/`` are
overwritten on every regeneration. The hand-written ``__init__.py`` at
each level of the namespace (``gen/``, ``gen/monorepo/``,
``gen/monorepo/v1/``) is intentionally minimal so it survives a
regen-and-diff cycle untouched.

Once ``buf generate`` has run, consumers can reach the stubs via the
proto package path::

    from monorepo_pb.gen.monorepo.v1 import money_pb2, ledger_pb2, ledger_pb2_grpc
"""
from __future__ import annotations

__all__: list[str] = []
