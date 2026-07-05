"""
Practical code examples for common Cascades SDK use cases.

These examples are designed to be copy-pasted and adapted.
Each example includes the necessary imports, authentication setup,
and step-by-step comments.
"""

# ────────────────────────────────────────────────────────────
# Example 1: OSINT Collection with SpiderFoot
# ────────────────────────────────────────────────────────────
OSINT_SPIDERFOOT_EXAMPLE = """
from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import submit_and_wait

# Initialize the client
client = CascadesClient(
    "https://your-cascades-instance.example.com",
    SessionCookieAuth("your-session-cookie"),
)

# Configure SpiderFoot connector
result = submit_and_wait(client, "osint-intake", {
    "connectors": [{
        "sourceTool": "spiderfoot",
        "baseUrl": "http://your-spiderfoot-server:5001",
        "apiKey": "your-spiderfoot-api-key",
        "scanType": "FINISHED",
    }],
    "deduplicate": True,
    "autoSubmit": True,
}, timeout=7200)

print(f"Total collected: {result.get('totalCollected', '?')}")
print(f"New findings: {result.get('newFindings', '?')}")
print(f"Duplicates skipped: {result.get('duplicatesSkipped', '?')}")
print(f"Submitted to Judicium: {result.get('submittedToJudicium', '?')}")
"""

# ────────────────────────────────────────────────────────────
# Example 2: Maltego Import
# ────────────────────────────────────────────────────────────
MALTEGO_IMPORT_EXAMPLE = """
from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import submit_and_wait

client = CascadesClient(
    "https://your-cascades-instance.example.com",
    SessionCookieAuth("your-session-cookie"),
)

# Import a Maltego CSV export
result = submit_and_wait(client, "osint-intake", {
    "connectors": [{
        "sourceTool": "maltego",
        "filePath": "/path/to/export.csv",
        "fileFormat": "csv",
    }],
    "deduplicate": True,
    "autoSubmit": True,
})

print(f"Imported entities: {result.get('newFindings', '?')}")
"""

# ────────────────────────────────────────────────────────────
# Example 3: Investigation Pipeline
# ────────────────────────────────────────────────────────────
INVESTIGATION_EXAMPLE = """
from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import run_investigation

client = CascadesClient(
    "https://your-cascades-instance.example.com",
    SessionCookieAuth("your-session-cookie"),
)

# Run a full investigation
result = run_investigation(
    client,
    investigation_id="inv-123456",
    sources=["https://feeds.example.com/threat-rss"],
)

print(f"Report ID: {result.get('reportId', '?')}")
print(f"Proof IDs: {result.get('proofIds', [])}")
"""

# ────────────────────────────────────────────────────────────
# Example 4: Evidence Verification with Hexarch Proof
# ────────────────────────────────────────────────────────────
EVIDENCE_VERIFICATION_EXAMPLE = """
from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.workflows import verify_evidence

client = CascadesClient(
    "https://your-cascades-instance.example.com",
    SessionCookieAuth("your-session-cookie"),
)

# Generate and attach a cryptographic proof
result = verify_evidence(
    client,
    evidence_id="ev-789",
    case_id="case-456",
)

print(f"Proof ID: {result.get('proofId', '?')}")
print(f"Verified: {result.get('verified', False)}")
"""

# ────────────────────────────────────────────────────────────
# Example 5: DAG Compilation with @task and @flow
# ────────────────────────────────────────────────────────────
DAG_COMPILATION_EXAMPLE = """
from cascades_sdk import task, flow
from cascades_sdk.compiler import build_dag_from_flow, canonical_json

@task
def fetch_ip_report(ip: str) -> str:
    # In capture mode, this function is NOT executed.
    # Return type hints help document the data flow.
    return f"report for {ip}"

@task
def enrich_with_shodan(ip: str) -> str:
    return f"shodan data for {ip}"

@task
def merge_findings(ip: str, report: str, shodan: str) -> dict:
    return {"ip": ip, "report": report, "shodan": shodan}

@flow
def osint_pipeline(ip: str) -> dict:
    report = fetch_ip_report(ip)
    shodan = enrich_with_shodan(ip)
    return merge_findings(ip, report, shodan)

# Compile the DAG — note: no real API calls are made
dag = build_dag_from_flow(osint_pipeline, {"ip": "8.8.8.8"})

# dag = {
#     "nodes": [
#         {"id": "node-0", "task_name": "fetch_ip_report", "dependencies": []},
#         {"id": "node-1", "task_name": "enrich_with_shodan", "dependencies": []},
#         {"id": "node-2", "task_name": "merge_findings", "dependencies": ["node-0", "node-1"]},
#     ],
#     "edges": [
#         {"from": "node-0", "to": "node-2"},
#         {"from": "node-1", "to": "node-2"},
#     ],
#     "return_node": "node-2",
#     "entrypoints": {"default": {"node": "node-0"}},
# }

# fetch_ip_report and enrich_with_shodan run in parallel (no dependency)
# merge_findings runs after both complete
# Canonical JSON for deterministic comparison
print(canonical_json(dag))
"""

# ────────────────────────────────────────────────────────────
# Example 6: Scheduled Cron Workflow
# ────────────────────────────────────────────────────────────
SCHEDULED_WORKFLOW_EXAMPLE = """
import requests

# Create a trigger for hourly OSINT collection
response = requests.post(
    "https://your-cascades-instance.example.com/api/v1/triggers",
    json={
        "workflowId": "osint-intake",
        "schedule": "0 * * * *",  # every hour
        "inputs": {
            "connectors": [{"sourceTool": "spiderfoot", "baseUrl": "...", "apiKey": "..."}],
        },
    },
    cookies={"__session": "your-session-cookie"},
)
print(response.json())
"""

# ────────────────────────────────────────────────────────────
# Example 7: Error Handling
# ────────────────────────────────────────────────────────────
ERROR_HANDLING_EXAMPLE = """
from cascades_sdk import CascadesClient, SessionCookieAuth
from cascades_sdk.errors import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    TimeoutError,
)
from cascades_sdk.workflows import submit_and_wait

client = CascadesClient(
    "https://your-cascades-instance.example.com",
    SessionCookieAuth("your-session-cookie"),
)

try:
    result = submit_and_wait(client, "osint-intake", {
        "connectors": [{"sourceTool": "spiderfoot", "baseUrl": "...", "apiKey": "..."}]
    })
except AuthenticationError as e:
    print(f"Auth failed: {e}")
    print("→ Re-login and get a fresh session cookie")
except NotFoundError as e:
    print(f"Workflow not found: {e}")
except RateLimitError as e:
    print(f"Rate limited, waiting...")
except TimeoutError as e:
    print(f"Workflow timed out: {e}")
"""
