"""Compiler module for deterministic DAG generation from @flow functions."""

from .decorators import task, flow
from .dag_builder import build_dag_from_flow, build_dag_from_flow_json
from .canonical import canonical_json, canonicalize_dag

__all__ = [
    "task",
    "flow",
    "build_dag_from_flow",
    "build_dag_from_flow_json",
    "canonical_json",
    "canonicalize_dag",
]
