"""Namespace marker for the ``monorepo.v1`` proto package.

The ``*_pb2.py`` and ``*_pb2_grpc.py`` sibling modules are emitted by
``buf generate`` and intentionally not imported here -- doing so would
make package import order depend on the generator having already run.
"""
from __future__ import annotations
