"""Decorators for task and flow definitions."""

import functools
from typing import Any, Callable, TypeVar

from .context import FlowContext

T = TypeVar("T", bound=Callable[..., Any])


class _TaskPlaceholder:
    """Placeholder returned by task wrappers during capture mode."""

    def __init__(self, node_id: str, task_name: str):
        self.node_id = node_id
        self.task_name = task_name

    def __repr__(self) -> str:
        return f"<TaskPlaceholder {self.task_name} @ {self.node_id}>"


def task(func: T) -> T:
    """Mark a function as a task in a flow DAG."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        context = FlowContext.get_current()
        if context is not None:
            dependencies = []
            for arg in args:
                if isinstance(arg, _TaskPlaceholder):
                    dependencies.append(arg.node_id)
            for value in kwargs.values():
                if isinstance(value, _TaskPlaceholder):
                    dependencies.append(value.node_id)

            node_id = context.add_node(func, args, kwargs, dependencies)
            return _TaskPlaceholder(node_id, func.__name__)

        return func(*args, **kwargs)

    wrapper._is_task = True  # type: ignore[attr-defined]
    wrapper._task_name = func.__name__  # type: ignore[attr-defined]
    wrapper._original_func = func  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]


def flow(func: T) -> T:
    """Mark a function as a flow definition."""

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper._is_flow = True  # type: ignore[attr-defined]
    wrapper._flow_name = func.__name__  # type: ignore[attr-defined]
    wrapper._original_func = func  # type: ignore[attr-defined]
    return wrapper  # type: ignore[return-value]
