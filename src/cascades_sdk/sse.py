"""Minimal SSE (``text/event-stream``) parsing for run telemetry."""


import json
from typing import Any, Dict, Iterator, List


def iter_sse_json_events(lines: Iterator[str]) -> Iterator[Dict[str, Any]]:
    """
    Parse SSE frames from line iterator (e.g. ``response.iter_lines(decode_unicode=True)``).

    Yields parsed JSON objects from each ``data:`` line for frames named ``telemetry`` (or unnamed).
    Malformed JSON lines are skipped.
    """
    data_lines: List[str] = []
    for raw in lines:
        if raw is None:
            continue
        line = raw.strip("\r")
        if line == "":
            if data_lines:
                payload = "\n".join(data_lines).strip()
                data_lines = []
                if payload:
                    try:
                        yield json.loads(payload)
                    except ValueError:
                        continue
            continue
        if line.startswith(":"):
            continue
        if line.startswith("data:"):
            data_lines.append(line[5:].lstrip())
            continue
        # ignore event:, id:, retry: etc.
    if data_lines:
        payload = "\n".join(data_lines).strip()
        if payload:
            try:
                yield json.loads(payload)
            except ValueError:
                return
