"""Workflow helper utilities for common operations.

Reduces boilerplate when submitting, tracking, and inspecting workflows.
"""


from typing import Any, Dict, Optional

from .client import CascadesClient
from .client.polling import wait_for_completion
from ._meta import SDK_WORKFLOWS_URL


def submit_and_wait(
    client: CascadesClient,
    workflow_id: str,
    context: Optional[Dict[str, Any]] = None,
    timeout: float = 3600.0,
    *,
    execution_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a workflow and block until it reaches a terminal state.

    This is the most common workflow operation: submit, wait for completion,
    and return the terminal event. Combines ``submit_workflow_run()`` and
    ``wait_for_completion()`` into a single call.

    Args:
        client: An authenticated :class:`CascadesClient` instance.
        workflow_id: The ID of the workflow to execute (from the catalog
            or a previously saved workflow).
        context: Optional key-value pairs passed as workflow inputs.
        timeout: Maximum time in seconds to wait for completion
            (default 1 hour).
        execution_mode: Optional execution mode (``"inline"`` or
            ``"queued"``). When not set, the platform uses its default.

    Returns:
        The terminal SSE event dict with status and output data.

    Raises:
        AuthenticationError: If the session is invalid.
        NotFoundError: If the workflow_id doesn't exist.
        TimeoutError: If the run doesn't complete within ``timeout``.

    See Also:
        - :func:`submit_and_get_run` for just the submission step.
        - :func:`wait_for_completion` for the blocking step alone.
        - Workflow docs: {SDK_WORKFLOWS_URL}
    """
    body: Dict[str, Any] = {"workflowId": workflow_id}
    if context is not None:
        body["context"] = context
    if execution_mode is not None:
        body["executionMode"] = execution_mode

    accepted = client.submit_workflow_run(body)
    run_id = accepted["runId"]
    return wait_for_completion(client, run_id, timeout=timeout)


def submit_and_get_run(
    client: CascadesClient,
    workflow_id: str,
    context: Optional[Dict[str, Any]] = None,
    *,
    execution_mode: Optional[str] = None,
) -> Dict[str, Any]:
    """Submit a workflow and return the accepted response without waiting.

    Useful when you want to submit a workflow and check on it later,
    or when using webhook-based completion notifications.

    Args:
        client: An authenticated :class:`CascadesClient` instance.
        workflow_id: The ID of the workflow to execute.
        context: Optional key-value pairs passed as workflow inputs.
        execution_mode: Optional execution mode (``"inline"`` or
            ``"queued"``).

    Returns:
        The ``WorkflowRunAccepted`` dict with ``runId``, ``executionMode``,
        and status information.

    See Also:
        - :func:`submit_and_wait` for a blocking version.
        - :func:`iter_run_stream_events` for real-time event streaming.
    """
    body: Dict[str, Any] = {"workflowId": workflow_id}
    if context is not None:
        body["context"] = context
    if execution_mode is not None:
        body["executionMode"] = execution_mode
    return client.submit_workflow_run(body)


def run_osint_intake(
    client: CascadesClient,
    connectors: list[Dict[str, Any]],
    *,
    investigation_id: Optional[str] = None,
    deduplicate: bool = True,
    auto_submit: bool = True,
    timeout: float = 7200.0,
) -> Dict[str, Any]:
    """Submit an OSINT intake workflow that polls connectors and submits to Judicium.

    This is a convenience wrapper around the ``osint-intake`` workflow.

    Args:
        client: An authenticated :class:`CascadesClient` instance.
        connectors: List of connector configurations. Each entry should have
            ``sourceTool`` (e.g. ``"spiderfoot"``, ``"maltego"``,
            ``"shodan"``) and source-specific fields like ``baseUrl``,
            ``apiKey``, ``filePath``, etc.
        investigation_id: Optional Judicium investigation ID to associate
            findings with.
        deduplicate: Whether to skip duplicate findings (default True).
        auto_submit: Whether to automatically submit findings to Judicium
            (default True).
        timeout: Maximum time in seconds to wait for completion
            (default 2 hours for long OSINT collections).

    Returns:
        The terminal event dict with collection statistics.

    Example:
        >>> result = run_osint_intake(client, [
        ...     {"sourceTool": "spiderfoot", "baseUrl": "...", "apiKey": "..."},
        ...     {"sourceTool": "maltego", "filePath": "export.csv", "fileFormat": "csv"},
        ... ])
        >>> print(f"Collected {result['totalCollected']} findings")

    See Also:
        - Connector configuration reference: {SDK_WORKFLOWS_URL}/connectors
        - Judicium integration guide: https://cascades.work/docs/judicium
    """
    context: Dict[str, Any] = {
        "connectors": connectors,
        "deduplicate": deduplicate,
        "autoSubmit": auto_submit,
    }
    if investigation_id is not None:
        context["investigationId"] = investigation_id
    return submit_and_wait(client, "osint-intake", context, timeout=timeout)


def run_investigation(
    client: CascadesClient,
    investigation_id: str,
    sources: Optional[list[str]] = None,
    timeout: float = 3600.0,
) -> Dict[str, Any]:
    """Run an investigation workflow: collect → analyze → report.

    Args:
        client: An authenticated :class:`CascadesClient` instance.
        investigation_id: The Judicium investigation ID.
        sources: Optional list of source URLs to collect data from.
            Falls back to placeholder data if empty.
        timeout: Maximum wait time in seconds.

    Returns:
        Terminal event with ``reportId`` and ``proofIds``.

    See Also:
        - Investigation workflow docs: {SDK_WORKFLOWS_URL}/investigation
    """
    context: Dict[str, Any] = {"investigationId": investigation_id}
    if sources is not None:
        context["sources"] = sources
    return submit_and_wait(client, "investigation-workflow", context, timeout=timeout)


def verify_evidence(
    client: CascadesClient,
    evidence_id: str,
    case_id: str,
    timeout: float = 300.0,
) -> Dict[str, Any]:
    """Verify evidence by generating a cryptographic proof and attaching it to a case.

    Args:
        client: An authenticated :class:`CascadesClient` instance.
        evidence_id: The Judicium evidence ID to verify.
        case_id: The Judicium case/investigation ID.
        timeout: Maximum wait time in seconds.

    Returns:
        Terminal event with ``proofId`` and ``verified`` boolean.

    See Also:
        - Evidence verification docs: {SDK_WORKFLOWS_URL}/evidence-verification
        - Hexarch proof system: https://cascades.work/docs/hexarch
    """
    context = {"evidenceId": evidence_id, "caseId": case_id}
    return submit_and_wait(client, "evidence-verification", context, timeout=timeout)


def list_workflows(client: CascadesClient) -> list[Dict[str, Any]]:
    """List all available workflow definitions from the catalog.

    Uses the Cascades API to fetch the workflow catalog. Returns both
    built-in workflows (investigation, evidence-verification, osint-intake)
    and any user-created workflows.

    Args:
        client: An authenticated :class:`CascadesClient` instance.

    Returns:
        A list of workflow definition dicts with ``id``, ``name``,
        ``version``, ``description``, ``collectors``, and ``schedule``.

    See Also:
        - :func:`submit_and_wait` to execute a workflow.
        - Workflow catalog docs: {SDK_WORKFLOWS_URL}/catalog
    """
    return client._http.request_json("GET", "/api/v1/workflows")
