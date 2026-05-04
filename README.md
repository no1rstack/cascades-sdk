# Cascades SDK (Python)

Official Python client for **[Cascades](https://cascades.work)** — a **governed execution** system. This project is licensed under the **Business Source License 1.1 (BUSL 1.1)**; see **[License](#license)**. The package provides **capture-mode authoring** (`@task` / `@flow`) to build a **serializable DAG**, plus a **small HTTP client** to register flows, start runs, poll status, and (when your deployment supports it) submit task output.

**PyPI:** [`cascades-sdk`](https://pypi.org/project/cascades-sdk/) · **Repository:** [`no1rstack/cascades-sdk`](https://github.com/no1rstack/cascades-sdk) · **HTTP contract (mirrored):** [`contracts/api.yaml`](./contracts/api.yaml) (source of truth: [`no1rstack/cascades`](https://github.com/no1rstack/cascades/blob/main/contracts/api.yaml))

## What this library is (and is not)

| In scope | Out of scope (handled by the Cascades platform / your deployment) |
|----------|----------------------------------------------------------------------|
| `@task` / `@flow` decorators and **capture-mode** execution to record a DAG | Worker execution, retries, queues, scheduling |
| **Deterministic** DAG JSON (`build_dag_from_flow`, canonicalization helpers) | Full OpenAPI surface beyond the mirrored contract |
| **Thin** `requests`-based client: register flow, trigger run, get run, graphs, `submit_task_output` | Auth0 cookie sessions, Stripe, or other routes not in `contracts/api.yaml` |
| **Sync + async** polling helpers (`wait_for_completion`, `wait_for_completion_async`) | In-process orchestration engine inside this wheel |

The SDK does **not** ship Airflow/Argo/BPMN adapters, W3C PROV builders, CloudEvents emitters, or OpenTelemetry instrumentation — those belong in **documentation or separate packages** if you add them later.

## Install

```bash
pip install cascades-sdk
```

Import namespace: **`cascades_sdk`** (not `cascade_sdk`). Legacy wheel name **`noirstack-cascade-sdk`** is obsolete; use **`cascades-sdk`** only.

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

**Async polling:** `from cascades_sdk import wait_for_completion_async` and `await wait_for_completion_async(client, run_id)`.

**Aliases:** `CascadeClient` and `CascadeSDKError` are kept for backward compatibility; prefer `CascadesClient` / `CascadesSDKError`.

## Capture mode and data at task boundaries

Under `@flow`, task calls are intercepted so the compiler can record **nodes and edges** without running your real side effects on the machine where you compile. Values that end up in the DAG should be **JSON-friendly** (e.g. `str`, `int`, `float`, `bool`, `dict`, `list`, `None`). Avoid pushing live handles (DB connections, open files, arbitrary class instances) across task boundaries if they cannot serialize the way your control plane expects.

`build_dag_from_flow(flow, flow_inputs=None)` — pass `flow_inputs` when the flow function has parameters you need to bind for capture.

## HTTP API surface

The SDK follows paths and payloads described in **`contracts/api.yaml`** in this repo (a mirror of the platform contract). Typical methods today:

- `register_flow(name, dag, version="1.0.0")` → `POST /api/flows/register`
- `trigger_flow(flow_id, inputs)` → `POST /api/runs`
- `get_run(run_id)` → `GET /api/runs/{id}`
- `get_flow_graph` / `get_run_graph` — graph introspection where exposed
- `submit_task_output(run_id, task_id, output, ...)` — optional HITL / manual completion paths; `path_template` overrides the default URL pattern if your deployment differs

If your deployment uses **session cookies** instead of `X-API-Key`, extend or wrap the client — the stock client is oriented around API key headers as in the mirrored contract.

## HTTP contract mirror (maintainers)

Canonical upstream: **[`no1rstack/cascades` → `contracts/api.yaml`](https://github.com/no1rstack/cascades/blob/main/contracts/api.yaml)**. Do not hand-edit the copy here; sync and verify. See **[`contracts/README.md`](./contracts/README.md)**, **`RELEASE.md`**, and:

```bash
./scripts/sync_contract.sh ../cascades/contracts/api.yaml
# or: make sync-contract
```

## Publish to PyPI (maintainers)

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

Or load credentials from a `.env`-style file (e.g. sibling app’s `.env.local`) without printing secrets:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_pypi.ps1 -EnvFile "..\cascades\.env.local"
```

Use **`PYPI_USERNAME`** + **`PYPI_API_KEY`**, or **`TWINE_USERNAME`** + **`TWINE_PASSWORD`**, or a **`PYPI_TOKEN`** / **`PYPI_API_TOKEN`** with username `__token__`. For Warehouse uploads, **`PYPI_URL`** should be `https://upload.pypi.org/legacy/` (or omit for Twine’s default).

## Contributing

Issues and PRs: **[github.com/no1rstack/cascades-sdk](https://github.com/no1rstack/cascades-sdk/issues)**. For **compiler** edge cases, include a **minimal** `@flow` / `@task` snippet and the DAG you expected vs what `build_dag_from_flow` produced.

## License

This project is licensed under the **Business Source License 1.1 (BUSL 1.1)**. See [`LICENSE`](./LICENSE) for full terms.

Non-production, evaluation, and internal research use are permitted under the **Additional Use Grant** in `LICENSE`. Commercial use, SaaS deployment, or offering the Licensed Work as a service requires a commercial agreement with **Noir Stack LLC** — **[https://noirstack.com](https://noirstack.com)**. On the **Change Date** (see `LICENSE`; **2030-05-01**, subject to the four-year rule in the license text), the Licensed Work converts to **GPL-3.0-or-later**.

The Cascades SDK is part of the Cascades system and follows the same licensing model as the platform unless otherwise explicitly stated.
