"""
Getting Started with Cascades SDK
==================================

This module provides a structured onboarding experience for new Cascades users.
Follow the steps below in order. Each step links to relevant documentation.

Quick Start (30 seconds)
------------------------

.. code-block:: python

    from cascades_sdk import CascadesClient, SessionCookieAuth
    from cascades_sdk.workflows import submit_and_wait

    # 1. Authenticate (see step 1 below for how to get your session cookie)
    client = CascadesClient(
        "https://your-cascades-instance.example.com",
        SessionCookieAuth("your-session-cookie"),
    )

    # 2. Run a workflow
    result = submit_and_wait(client, "osint-intake", {
        "connectors": [{"sourceTool": "spiderfoot", "baseUrl": "...", "apiKey": "..."}]
    })
    print("Done!", result)


Installation
------------

.. code-block:: bash

    pip install cascades-sdk

Requires Python 3.8+ and the ``requests`` library (installed automatically).


Step 1: Authentication
----------------------

Cascades uses Auth0 session cookies for API authentication.

**Getting your session cookie:**

1. Open your Cascades deployment in a browser (e.g. https://cascades.work)
2. Log in via Auth0
3. Open Developer Tools (F12) → Application → Cookies
4. Copy the ``__session`` cookie value
5. Pass it to the SDK:

.. code-block:: python

    from cascades_sdk import CascadesClient, SessionCookieAuth

    client = CascadesClient(
        "https://your-cascades-instance.example.com",
        SessionCookieAuth("paste-session-cookie-here"),
    )

For automation scenarios, you can also use header-based auth:

.. code-block:: python

    from cascades_sdk import HeaderAuth, CompositeAuth

    auth = CompositeAuth(
        SessionCookieAuth("session-value"),
        HeaderAuth({"X-API-Key": "your-api-key"}),
    )

**Troubleshooting:**

- **401 Unauthorized**: Your session cookie expired. Re-login and get a fresh cookie.
- **403 Forbidden**: Your account lacks the required permissions.

📖 `Authentication docs <https://cascades.work/docs/authentication>`_


Step 2: Verify Connectivity
---------------------------

.. code-block:: python

    version = client.get_public_api_version()
    print(f"Connected to Cascades API v{version['apiVersion']}")

If this succeeds, your client is properly configured.


Step 3: Run Your First Workflow
-------------------------------

The simplest workflow is ``osint-intake``, which polls OSINT connectors
and submits findings to Judicium.

.. code-block:: python

    from cascades_sdk.workflows import submit_and_wait

    result = submit_and_wait(client, "osint-intake", {
        "connectors": [{"sourceTool": "spiderfoot", "baseUrl": "...", "apiKey": "..."}],
        "deduplicate": True,
        "autoSubmit": True,
    })
    print(f"Collected {result['totalCollected']} findings")

📖 `Workflow docs <https://cascades.work/docs/workflows>`_


Step 4: Explore Other Workflows
-------------------------------

The Cascades platform includes several built-in workflows:

- **osint-intake** — Poll OSINT connectors and submit to Judicium
- **investigation-workflow** — Full investigation pipeline (collect → analyze → report)
- **evidence-verification** — Generate cryptographic proofs for evidence

.. code-block:: python

    from cascades_sdk.workflows import run_investigation, verify_evidence

    # Run an investigation
    result = run_investigation(client, investigation_id="your-investigation-id")

    # Verify evidence with a cryptographic proof
    result = verify_evidence(client, evidence_id="ev-123", case_id="case-456")


Step 5: DAG Compilation (Advanced)
----------------------------------

For custom workflows, use the ``@task`` / ``@flow`` decorators to define
DAGs that compile to deterministic JSON.

.. code-block:: python

    from cascades_sdk import task, flow
    from cascades_sdk.compiler import build_dag_from_flow

    @task
    def fetch_data(url: str) -> str:
        return f"data from {url}"

    @task
    def analyze(data: str) -> str:
        return f"analysis of {data}"

    @flow
    def my_pipeline(url: str):
        data = fetch_data(url)
        return analyze(data)

    dag = build_dag_from_flow(my_pipeline, {"url": "https://example.com"})
    print(dag)
    # {'nodes': [...], 'edges': [...], 'return_node': 'node-1', 'entrypoints': ...}

📖 `DAG compiler docs <https://cascades.work/docs/workflows/dag>`_


Next Steps
----------

- 📖 `Full API Reference <https://cascades.work/docs/api>`_
- 🔧 `Configuration Guide <https://cascades.work/docs/configuration>`_
- 🧪 `Examples & Recipes <https://cascades.work/docs/examples>`_
- 🐛 `Issue Tracker <https://github.com/no1rstack/cascades-sdk/issues>`_

For detailed documentation on each module, use Python's ``help()`` function:

.. code-block:: python

    from cascades_sdk import workflows
    help(workflows.submit_and_wait)
"""

from ._meta import SDK_GETTING_STARTED_URL, SDK_DOCS_URL

__doc__ = __doc__  # make the module docstring accessible
