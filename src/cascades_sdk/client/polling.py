"""Polling utilities for run completion."""

import asyncio
import time
from typing import Any, Callable, Dict, Optional

from .client import CascadesClient
from .errors import TimeoutError as SDKTimeoutError


def wait_for_completion(
    client: CascadesClient,
    run_id: str,
    timeout: int = 300,
    poll_interval: float = 1.0,
    on_status_change: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    start_time = time.time()
    last_status = None

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise SDKTimeoutError(f"Run {run_id} did not complete within {timeout}s")

        run = client.get_run(run_id)
        status = run.get("status")

        if status != last_status and on_status_change and isinstance(status, str):
            on_status_change(status)
            last_status = status

        if status in ("completed", "failed", "canceled", "cancelled", "timedout", "crashed"):
            return run

        time.sleep(poll_interval)


async def wait_for_completion_async(
    client: CascadesClient,
    run_id: str,
    timeout: int = 300,
    poll_interval: float = 1.0,
    on_status_change: Optional[Callable[[str], None]] = None,
) -> Dict[str, Any]:
    start_time = time.time()
    last_status = None

    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            raise SDKTimeoutError(f"Run {run_id} did not complete within {timeout}s")

        run = await asyncio.to_thread(client.get_run, run_id)
        status = run.get("status")

        if status != last_status and on_status_change and isinstance(status, str):
            on_status_change(status)
            last_status = status

        if status in ("completed", "failed", "canceled", "cancelled", "timedout", "crashed"):
            return run

        await asyncio.sleep(poll_interval)
