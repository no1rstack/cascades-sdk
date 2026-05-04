from cascades_sdk.sse import iter_sse_json_events


def test_iter_sse_json_events_parses_telemetry_frame():
    lines = iter(
        [
            "event: telemetry",
            'data: {"type":"run.progress","data":{"runId":"r1","status":"RUNNING"}}',
            "",
        ]
    )
    events = list(iter_sse_json_events(lines))
    assert len(events) == 1
    assert events[0]["type"] == "run.progress"
    assert events[0]["data"]["status"] == "RUNNING"
