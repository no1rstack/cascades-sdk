# Cascades SDK (Python)

Official Python client for **[Cascades](https://cascades.work)** — a **governed execution** system. This project is licensed under the **Business Source License 1.1 (BUSL 1.1)**; see **[License](#license)**. The package provides **capture-mode authoring** (`@task` / `@flow`) to build a **serializable DAG**, plus an **HTTP client** aligned with the mirrored OpenAPI contract.

**PyPI:** [`cascades-sdk`](https://pypi.org/project/cascades-sdk/) · **Repository:** [`no1rstack/cascades-sdk`](https://github.com/no1rstack/cascades-sdk) · **HTTP contract (mirrored):** [`contracts/api.yaml`](./contracts/api.yaml) (source of truth: [`no1rstack/cascades`](https://github.com/no1rstack/cascades/blob/main/contracts/api.yaml))

## What this library is (and is not)

| In scope | Out of scope (handled by the Cascades platform / your deployment) |
|----------|----------------------------------------------------------------------|
| `@task` / `@flow` decorators and **capture-mode** execution to record a DAG | Worker execution, retries, queues, scheduling |
| **Deterministic** DAG JSON (`build_dag_from_flow`, canonicalization helpers) | Routes omitted from `contracts/api.yaml` (see platform `/openapi.json` for the full app) |
| **`CascadesClient`** — every path in `contracts/api.yaml` (workflows, runs SSE, integrations, system version) | Auth0 login UI, Stripe webhooks, internal admin routes |
| **Auth helpers** (`SessionCookieAuth`, `CookieHeaderAuth`, `HeaderAuth`, `CompositeAuth`) matching contract security | Issuing session cookies (browser / Auth0 flow) |
| **`wait_for_completion`** / **`wait_for_completion_async`** — block on **SSE** (`GET /api/runs/{id}/stream`) until a terminal run status | In-process orchestration engine inside this wheel |

The SDK does **not** ship Airflow/Argo/BPMN adapters, W3C PROV builders, CloudEvents emitters, or OpenTelemetry instrumentation — those belong in **documentation or separate packages** if you add them later.

## Install

```bash
pip install cascades-sdk
```

Import namespace: **`cascades_sdk`** (not `cascade_sdk`). Legacy wheel name **`noirstack-cascade-sdk`** is obsolete; use **`cascades-sdk`** only.

## Contract version parity

`cascades_sdk.API_CONTRACT_VERSION` must match `info.version` in `contracts/api.yaml`. When the platform bumps that field, mirror the YAML and update `src/cascades_sdk/_meta.py` before releasing (`tests/test_contract_parity.py` enforces this).

## Quick start

```python
from cascades_sdk import CascadesClient, SessionCookieAuth, wait_for_completion
from cascades_sdk.compiler import build_dag_from_flow

# Session value from your Auth0-backed deployment (__session by default).
client = CascadesClient(
    "https://your-cascades-host",
    SessionCookieAuth("paste-session-cookie-value-here"),
)

version = client.get_public_api_version()  # GET /api/system/version (no auth required)
accepted = client.submit_workflow_run({"workflowId": "your-catalog-id"})  # camelCase response keys
run_id = accepted["runId"]

# Blocks on SSE until SUCCESS / FAILED / CANCELLED (see contracts/api.yaml Runs tag).
terminal_event = wait_for_completion(client, run_id, timeout=3600.0)
print(terminal_event)
```

**Async:** `from cascades_sdk import wait_for_completion_async` and `await wait_for_completion_async(client, run_id)`.

**Optional header auth** (only if your tenant documents it): `CompositeAuth(SessionCookieAuth("..."), HeaderAuth({"X-Custom-Token": "..."}))`.

**Optional product markers:** pass `vendor_headers=True` to `CascadesClient` to add stable `X-SDK-*` / `X-Product` / `X-Vendor` headers (see `vendor_telemetry_headers()` in `cascades_sdk._meta`). The default `User-Agent` already names the SDK, **Cascades**, repo URL, and **Noir Stack LLC**.

**Aliases:** `CascadeClient` and `CascadeSDKError` are kept for backward compatibility; prefer `CascadesClient` / `CascadesSDKError`.

## Capture mode and data at task boundaries

Under `@flow`, task calls are intercepted so the compiler can record **nodes and edges** without running your real side effects on the machine where you compile. Values that end up in the DAG should be **JSON-friendly** (e.g. `str`, `int`, `float`, `bool`, `dict`, `list`, `None`). Avoid pushing live handles (DB connections, open files, arbitrary class instances) across task boundaries if they cannot serialize the way your control plane expects.

`build_dag_from_flow(flow, flow_inputs=None)` — pass `flow_inputs` when the flow function has parameters you need to bind for capture.

## HTTP API surface

The client mirrors **`contracts/api.yaml`** only (16 paths), including:

- `get_public_api_version()` → `GET /api/system/version`
- `submit_workflow_run(body)` → `POST /api/workflows/run`
- `clone_catalog_workflow(body)` → `POST /api/workflows/clone`
- `iter_run_stream_events(run_id, since=..., task_since=...)` → `GET /api/runs/{id}/stream` (SSE `RunStreamEvent` payloads)
- `save_*_integration` / `test_*_integration` → `POST /api/integrations/...`

JSON keys on the wire match the deployment (camelCase as in the contract). Typed hints live under `cascades_sdk.types` for common response bodies.

## HTTP contract mirror (maintainers)

Canonical upstream: **[`no1rstack/cascades` → `contracts/api.yaml`](https://github.com/no1rstack/cascades/blob/main/contracts/api.yaml)**. Do not hand-edit the copy here; sync and verify. See **[`contracts/README.md`](./contracts/README.md)**, **`RELEASE.md`**, and:

```bash
./scripts/sync_contract.sh ../cascades/contracts/api.yaml
# or: make sync-contract
```

## Publish to PyPI (maintainers)

**Preferred:** GitHub **Actions → Publish to PyPI** (`workflow_dispatch`) using a [trusted publisher](https://docs.pypi.org/trusted-publishers/) — see **`RELEASE.md`** for the one-time PyPI UI steps (no `PYPI_*` secret stored in GitHub).

**Local / token file:** build, check, then upload with Twine:

```bash
python -m build
python -m twine check dist/*
python -m twine upload dist/*
```

On Windows, load variables from a `.env`-style file (default: `..\cascades\.env.local`; override with **`-EnvFile`** or **`CASCADES_SDK_ENV_FILE`**):

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\publish_pypi.ps1
# or:  ... -EnvFile "C:\path\to\.env.local"
```

Use **`PYPI_USERNAME`** + **`PYPI_API_KEY`**, or **`TWINE_USERNAME`** + **`TWINE_PASSWORD`**, or **`PYPI_TOKEN`** / **`PYPI_API_TOKEN`** (script maps token to `__token__` + password). Optional **`PYPI_URL`**: use an **upload** endpoint (e.g. `https://upload.pypi.org/legacy/` or TestPyPI’s upload URL). Do **not** use a project page URL (`https://pypi.org/project/...`).

## Contributing

Issues and PRs: **[github.com/no1rstack/cascades-sdk](https://github.com/no1rstack/cascades-sdk/issues)**. For **compiler** edge cases, include a **minimal** `@flow` / `@task` snippet and the DAG you expected vs what `build_dag_from_flow` produced.

## License

This project is licensed under the **Business Source License 1.1 (BUSL 1.1)**. See [`LICENSE`](./LICENSE) for full terms.

Non-production, evaluation, and internal research use are permitted under the **Additional Use Grant** in `LICENSE`. Commercial use, SaaS deployment, or offering the Licensed Work as a service requires a commercial agreement with **Noir Stack LLC** — **[https://noirstack.com](https://noirstack.com)**. On the **Change Date** (see `LICENSE`; **2030-05-01**, subject to the four-year rule in the license text), the Licensed Work converts to **GPL-3.0-or-later**.

The Cascades SDK is part of the Cascades system and follows the same licensing model as the platform unless otherwise explicitly stated.
