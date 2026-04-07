"""Cascades SDK - Python client for Cascades workflow orchestration."""

__version__ = "0.2.0"

from .compiler import (
    task,
    flow,
    build_dag_from_flow,
    build_dag_from_flow_json,
    canonical_json,
    canonicalize_dag,
)

from .client import (
    CascadesClient,
    CascadeClient,
    CascadesSDKError,
    CascadeSDKError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    OrchestrationError,
    NetworkError,
    TimeoutError,
    wait_for_completion,
    wait_for_completion_async,
)

__all__ = [
    "__version__",
    "task",
    "flow",
    "build_dag_from_flow",
    "build_dag_from_flow_json",
    "canonical_json",
    "canonicalize_dag",
    "CascadesClient",
    "CascadeClient",
    "wait_for_completion",
    "wait_for_completion_async",
    "CascadesSDKError",
    "CascadeSDKError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "OrchestrationError",
    "NetworkError",
    "TimeoutError",
]
