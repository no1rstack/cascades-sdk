"""Wait for workflow run terminal state via the contract SSE stream."""

from __future__ import annotations

import asyncio
import time
from typing import Any, Callable, Dict, FrozenSet, Optional

from .client import CascadesClient
from ..errors import TimeoutError as SDKTimeoutError

_TERMINAL: FrozenSet[str] = frozenset({"SUCCESS", "FAILED", "CANCELLED"})


def _terminal_event(ev: Dict[str, Any]) -> bool:
    t = ev.get("type")
    data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
    if t in ("run.completed", "run.failed"):
        return True
    if t == "run.progress" and data.get("status") in _TERMINAL:
        return True
    return False


def _status_from_event(ev: Dict[str, Any]) -> Optional[str]:
    data = ev.get("data")
    if isinstance(data, dict):
        s = data.get("status")
        if isinstance(s, str):
            return s
    return None


def wait_for_completion(
    client: CascadesClient,
    run_id: str,
    timeout: float = 3600.0,
    poll_interval: float = 1.0,
    on_status_change: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    """
    Block until the run reaches a terminal status (SSE).

    ``poll_interval`` is ignored (kept for backward compatibility with older poll-based callers).
    ``on_status_change`` receives uppercase ``WorkflowRunStatus`` strings from stream payloads.
    """
    del poll_interval
    start = time.monotonic()
    last_status: Optional[str] = None
    last_ev: Optional[Dict[str, Any]] = None

    for ev in client.iter_run_stream_events(run_id):
        if time.monotonic() - start > timeout:
            raise SDKTimeoutError(f"Run {run_id} did not complete within {timeout}s")
        if not isinstance(ev, dict):
            continue
        last_ev = ev
        status = _status_from_event(ev)
        if status and status != last_status:
            if on_status_change:
                on_status_change(status)
            last_status = status
        if _terminal_event(ev):
            t = ev.get("type")
            data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
            if t in ("run.completed", "run.failed"):
                return ev
            return {"type": t, "data": data}

    if last_ev is not None:
        return last_ev
    raise SDKTimeoutError(f"Run {run_id}: stream ended before any terminal event")


async def wait_for_completion_async(
    client: CascadesClient,
    run_id: str,
    timeout: float = 3600.0,
    poll_interval: float = 1.0,
    on_status_change: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    return await asyncio.to_thread(
        wait_for_completion,
        client,
        run_id,
        timeout,
        poll_interval,
        on_status_change,
    )


wait_for_run_terminal = wait_for_completion
wait_for_run_terminal_async = wait_for_completion_async
