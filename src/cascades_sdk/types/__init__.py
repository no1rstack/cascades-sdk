"""TypedDict shapes mirroring ``contracts/api.yaml`` component schemas (wire-format / camelCase)."""


from typing import Any, Dict, Literal, TypedDict


class ApiVersionResponse(TypedDict):
    apiVersion: Literal["v1"]


class WorkflowRunRequestBody(TypedDict, total=False):
    workflowId: str
    context: Dict[str, Any]


class WorkflowRunAccepted(TypedDict, total=False):
    runId: str
    workflowId: str
    catalogItemId: str
    workflowDefinitionSnapshotId: str
    definitionHash: str
    taskRuns: int
    executionMode: Literal["queued", "inline"]
    message: str


class WorkflowCloneRequest(TypedDict):
    catalogItemId: str


class WorkflowCloneResponse(TypedDict):
    catalogItemId: str
    workflowRowId: str
    definitionId: str
    name: str


class RunStreamEvent(TypedDict):
    type: str
    data: Dict[str, Any]


class WorkflowValidationError(TypedDict, total=False):
    error: Literal["Workflow validation failed"]
    code: str
    message: str
    details: Dict[str, Any]


class WorkflowEngineUnavailable(TypedDict, total=False):
    error: Literal["Execution engine unavailable"]
    reason: Literal["worker_queue_required"]
    message: str


class WorkflowNotFound(TypedDict):
    error: Literal["Workflow not found"]
    reason: Literal["not_found", "invalid_definition"]
    workflowId: str


class IntegrationTestOk(TypedDict):
    ok: Literal[True]
