"""Flow execution context for DAG capture mode."""

from typing import Any, Dict, List, Optional
import threading


class FlowContext:
    """Context manager that captures task calls to build a DAG."""

    _thread_local = threading.local()

    def __init__(self) -> None:
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, str]] = []
        self.return_node_id: Optional[str] = None
        self.node_counter = 0

    def add_node(self, task_func: Any, args: tuple, kwargs: dict, dependencies: List[str]) -> str:
        node_id = f"node-{self.node_counter}"
        self.node_counter += 1

        task_name = getattr(task_func, "_task_name", task_func.__name__)
        node = {
            "id": node_id,
            "task_name": task_name,
            "dependencies": dependencies,
        }
        self.nodes.append(node)

        for dep_id in dependencies:
            self.add_edge(dep_id, node_id)

        return node_id

    def add_edge(self, from_node: str, to_node: str) -> None:
        edge = {"from": from_node, "to": to_node}
        if edge not in self.edges:
            self.edges.append(edge)

    def set_return_node(self, node_id: str) -> None:
        self.return_node_id = node_id

    @classmethod
    def get_current(cls) -> Optional["FlowContext"]:
        return getattr(cls._thread_local, "context", None)

    @classmethod
    def set_current(cls, context: Optional["FlowContext"]) -> None:
        cls._thread_local.context = context

    def __enter__(self) -> "FlowContext":
        FlowContext.set_current(self)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        FlowContext.set_current(None)
        return False
