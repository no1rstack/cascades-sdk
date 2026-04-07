"""Deterministic JSON serialization for DAG definitions."""

import json
from typing import Any, Dict


def _normalize(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {key: _normalize(obj[key]) for key in sorted(obj.keys())}
    if isinstance(obj, list):
        return [_normalize(item) for item in obj]
    if isinstance(obj, (str, int, float, bool, type(None))):
        return obj
    return str(obj)


def canonical_json(obj: Any) -> str:
    """Serialize to canonical JSON string with deterministic key ordering."""
    normalized = _normalize(obj)
    return json.dumps(normalized, sort_keys=True, separators=(",", ":"))


def canonicalize_dag(dag: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize DAG for deterministic comparisons."""
    normalized_dag: Dict[str, Any] = {}
    for key in sorted(dag.keys()):
        normalized_dag[key] = _normalize(dag[key])
    return normalized_dag
