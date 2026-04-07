"""DAG builder - extract DAG from @flow functions in capture mode."""

import inspect
from typing import Any, Callable, Dict, Optional

from .context import FlowContext
from .decorators import _TaskPlaceholder
from .canonical import canonical_json


def _build_args_for_capture(flow_func: Callable, flow_inputs: Optional[Dict[str, Any]]) -> tuple:
    sig = inspect.signature(flow_func)
    if not sig.parameters:
        return tuple()

    if flow_inputs is not None:
        bound = sig.bind_partial(**flow_inputs)
        args = []
        for name, param in sig.parameters.items():
            if name in bound.arguments:
                args.append(bound.arguments[name])
            elif param.default is not inspect._empty:
                args.append(param.default)
            else:
                args.append(None)
        return tuple(args)

    return tuple(None for _ in sig.parameters)


def build_dag_from_flow(flow_func: Callable, flow_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build deterministic DAG structure from a @flow-decorated function."""
    if not getattr(flow_func, "_is_flow", False):
        raise ValueError(f"{flow_func.__name__} is not decorated with @flow")

    context = FlowContext()
    args = _build_args_for_capture(flow_func, flow_inputs)

    with context:
        result = flow_func(*args)
        if isinstance(result, _TaskPlaceholder):
            context.set_return_node(result.node_id)

    dag: Dict[str, Any] = {
        "nodes": context.nodes,
        "edges": context.edges,
    }

    if context.return_node_id:
        dag["return_node"] = context.return_node_id

    if context.nodes:
        dag["entrypoints"] = {"default": {"node": context.nodes[0]["id"]}}

    return dag


def build_dag_from_flow_json(flow_func: Callable, flow_inputs: Optional[Dict[str, Any]] = None) -> str:
    """Build DAG and return canonical JSON payload."""
    dag = build_dag_from_flow(flow_func, flow_inputs=flow_inputs)
    return canonical_json(dag)
