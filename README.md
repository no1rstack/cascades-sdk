# Cascades SDK (Python)

PyPI package for the Cascades workflow orchestration control plane.

## Install

```bash
pip install cascades-sdk
```

## Quick start

```python
from cascades_sdk import task, flow, CascadesClient, wait_for_completion
from cascades_sdk.compiler import build_dag_from_flow

@task
def add(a: int, b: int) -> int:
    return a + b

@flow
def math_flow(a: int, b: int):
    return add(a, b)

dag = build_dag_from_flow(math_flow, {"a": 1, "b": 2})

client = CascadesClient(base_url="http://localhost:3000", api_key="your_api_key")
flow_id = client.register_flow("math_flow", dag)
run_id = client.trigger_flow(flow_id, {"a": 1, "b": 2})
result = wait_for_completion(client, run_id)
print(result.get("result"))
```

## What this SDK provides

- `@task` and `@flow` decorators
- Deterministic DAG capture/compilation
- Thin HTTP API client for flow registration and runs
- Polling helpers (sync + async)

## Publish to PyPI

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```
