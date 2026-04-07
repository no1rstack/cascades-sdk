"""TypedDict contracts for Cascades SDK."""

from typing import Any, List, Optional, TypedDict


class Node(TypedDict, total=False):
    id: str
    task_name: str
    dependencies: List[str]


class Edge(TypedDict):
    from_node: str
    to_node: str


class DAGDefinition(TypedDict, total=False):
    nodes: List[Node]
    edges: List[dict]
    return_node: Optional[str]
    entrypoints: dict


class FlowRun(TypedDict, total=False):
    run_id: str
    flow_id: str
    status: str
    result: Optional[Any]
    error: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
