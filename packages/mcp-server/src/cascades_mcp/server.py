"""
Cascades MCP Server — Model Context Protocol implementation.

Exposes tools, resources, and prompts that AI assistants can use to
interact with the Cascades platform: run diagnostics, manage workflows,
check authentication, and guide users through onboarding.

Run with: python -m cascades_mcp.server
"""

from __future__ import annotations

import json
import os
import sys
from typing import Any, Dict, List, Optional

# Add SDK to path for standalone usage
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "src"))

from cascades_sdk._meta import (
    __version__ as SDK_VERSION,
    SDK_DOCS_URL,
    SDK_AUTH_URL,
    SDK_WORKFLOWS_URL,
    SDK_API_REFERENCE_URL,
    SDK_GETTING_STARTED_URL,
    SDK_EXAMPLES_URL,
)
from cascades_sdk.diagnostics import run_diagnostics, DiagnosticResult, DiagnosticSeverity
from cascades_sdk.diagnostics.healing import HealingEngine


# ─── MCP Tool Definitions ────────────────────────────────

TOOLS = {
    "cascades_diagnostics": {
        "name": "cascades_diagnostics",
        "description": "Run comprehensive diagnostics on the Cascades connection and configuration. Checks version compatibility, network connectivity, authentication, permissions, environment, and workflow validity.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string", "description": "Cascades platform URL"},
                "session_cookie": {"type": "string", "description": "Auth0 session cookie value"},
                "api_key": {"type": "string", "description": "API key (alternative to session cookie)"},
                "sdk_version": {"type": "string", "description": "SDK version to check compatibility"},
                "extension_version": {"type": "string", "description": "VS Code extension version"},
                "mcp_version": {"type": "string", "description": "MCP server version"},
                "required_scopes": {"type": "array", "items": {"type": "string"}},
                "auto_heal": {"type": "boolean", "description": "Apply auto-healing for fixable issues"},
            },
        },
    },
    "cascades_workflow_list": {
        "name": "cascades_workflow_list",
        "description": "List available workflows and their descriptions, inputs, and outputs.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string"},
                "session_cookie": {"type": "string"},
            },
        },
    },
    "cascades_workflow_run": {
        "name": "cascades_workflow_run",
        "description": "Run a workflow and return the result. Provide the workflow ID and input context.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string"},
                "session_cookie": {"type": "string"},
                "workflow_id": {"type": "string", "description": "ID of the workflow to run"},
                "context": {"type": "object", "description": "Workflow input parameters"},
                "execution_mode": {"type": "string", "enum": ["inline", "queued"]},
            },
            "required": ["workflow_id"],
        },
    },
    "cascades_workflow_explain": {
        "name": "cascades_workflow_explain",
        "description": "Get a detailed explanation of what a workflow does, its inputs, outputs, and dependencies.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workflow_id": {"type": "string", "description": "Workflow ID to explain"},
            },
            "required": ["workflow_id"],
        },
    },
    "cascades_authenticate": {
        "name": "cascades_authenticate",
        "description": "Guide the user through authentication setup. Returns instructions and links for getting a session cookie.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string", "description": "Cascades platform URL"},
            },
        },
    },
    "cascades_config_check": {
        "name": "cascades_config_check",
        "description": "Check if the Cascades configuration is valid and complete.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "base_url": {"type": "string"},
                "session_cookie": {"type": "string"},
                "api_key": {"type": "string"},
            },
        },
    },
    "cascades_getting_started": {
        "name": "cascades_getting_started",
        "description": "Get a step-by-step onboarding guide for getting started with Cascades.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
}


# ─── Tool Handlers ────────────────────────────────────────

WORKFLOW_CATALOG = {
    "osint-intake": {
        "name": "OSINT Intake Pipeline",
        "description": "Poll OSINT connectors (SpiderFoot, Maltego, Shodan, etc.) and submit normalized findings to Judicium.",
        "version": "1.0.0",
        "inputs": {
            "connectors": {
                "type": "array",
                "description": "List of connector configurations. Each requires sourceTool (spiderfoot, maltego, shodan, censys, urlscan, virustotal, whois, github) plus type-specific fields like baseUrl, apiKey, filePath.",
            },
            "deduplicate": {"type": "boolean", "default": True, "description": "Skip duplicate findings"},
            "autoSubmit": {"type": "boolean", "default": True, "description": "Auto-submit to Judicium"},
            "investigationId": {"type": "string", "description": "Judicium investigation ID"},
        },
        "outputs": {
            "totalCollected": "Number of findings collected",
            "newFindings": "Number of new (non-duplicate) findings",
            "duplicatesSkipped": "Number of duplicates skipped",
            "submittedToJudicium": "Number submitted to Judicium",
        },
        "dependencies": ["judicium"],
        "example": {
            "connectors": [{"sourceTool": "spiderfoot", "baseUrl": "http://localhost:5001", "apiKey": "YOUR_KEY"}],
            "deduplicate": True,
            "autoSubmit": True,
        },
    },
    "investigation-workflow": {
        "name": "Investigation Pipeline",
        "description": "Full investigation: collect data from sources → analyze with AI → generate Hexarch proof → create Judicium report.",
        "version": "2.3.0",
        "inputs": {
            "investigationId": {"type": "string", "required": True, "description": "Judicium investigation ID"},
            "sources": {"type": "array", "description": "List of source URLs to collect data from"},
        },
        "outputs": {
            "reportId": "Generated Judicium report ID",
            "proofIds": "List of Hexarch proof IDs",
        },
        "dependencies": ["hexarch", "aitracer"],
        "example": {
            "investigationId": "inv-123456",
            "sources": ["https://feeds.example.com/threat-rss"],
        },
    },
    "evidence-verification": {
        "name": "Evidence Verification",
        "description": "Generate a cryptographic Hexarch proof for evidence and attach it to a case in Judicium.",
        "version": "1.0.0",
        "inputs": {
            "evidenceId": {"type": "string", "required": True, "description": "Judicium evidence ID to verify"},
            "caseId": {"type": "string", "required": True, "description": "Case/investigation ID to attach the proof to"},
        },
        "outputs": {
            "proofId": "Generated Hexarch proof ID",
            "verified": "Boolean indicating whether the proof was successfully verified",
        },
        "dependencies": ["hexarch"],
        "example": {
            "evidenceId": "ev-789",
            "caseId": "case-456",
        },
    },
}


def handle_tool_call(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    if tool_name == "cascades_diagnostics":
        return handle_diagnostics(arguments)
    elif tool_name == "cascades_workflow_list":
        return handle_workflow_list()
    elif tool_name == "cascades_workflow_run":
        return handle_workflow_run(arguments)
    elif tool_name == "cascades_workflow_explain":
        return handle_workflow_explain(arguments)
    elif tool_name == "cascades_authenticate":
        return handle_authenticate(arguments)
    elif tool_name == "cascades_config_check":
        return handle_config_check(arguments)
    elif tool_name == "cascades_getting_started":
        return handle_getting_started()
    else:
        return {"content": [{"type": "text", "text": f"Unknown tool: {tool_name}"}], "isError": True}


def handle_diagnostics(args: Dict[str, Any]) -> Dict[str, Any]:
    results, summary = run_diagnostics(**args)
    auto_heal = args.get("auto_heal", False)

    healed_count = 0
    if auto_heal:
        engine = HealingEngine()
        outcomes = engine.heal_all(results, args)
        healed_count = sum(1 for o in outcomes if o.success)

    lines = []
    lines.append(f"# Cascades Diagnostics Report")
    lines.append(f"")
    lines.append(f"**Summary:** {summary.get('passed', 0)} passed, {summary.get('failed', 0)} failed, {summary.get('warnings', 0)} warnings")
    lines.append(f"**Status:** {'✅ Healthy' if summary.get('healthy') else '❌ Issues found'}")
    if auto_heal:
        lines.append(f"**Auto-healed:** {healed_count} issue(s) resolved automatically")
    lines.append(f"")

    for r in results:
        icon = {"passed": "✅", "failed": "❌", "warning": "⚠️", "skipped": "⏭️"}.get(r.status, "❓")
        lines.append(f"## {icon} {r.check_name}")
        lines.append(f"**Status:** {r.status} | **Severity:** {r.severity} | **Duration:** {r.duration_ms:.0f}ms")
        lines.append(f"")
        lines.append(f"{r.message}")
        if r.explanation:
            lines.append(f"> {r.explanation}")
        if r.suggested_fix:
            lines.append(f"")
            lines.append(f"**Suggested fix:** {r.suggested_fix}")
        if r.doc_url:
            lines.append(f"**Docs:** {r.doc_url}")
        if r.fixes:
            lines.append(f"")
            lines.append(f"**Available fixes:**")
            for f in r.fixes:
                auto = " (auto)" if f.auto_heal else ""
                lines.append(f"  - {f.description}{auto}")
        lines.append(f"")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_workflow_list() -> Dict[str, Any]:
    lines = []
    lines.append("# Available Workflows")
    lines.append(f"")
    for wid, wf in WORKFLOW_CATALOG.items():
        lines.append(f"## {wf['name']} (`{wid}`)")
        lines.append(f"**Version:** {wf['version']}")
        lines.append(f"**Description:** {wf['description']}")
        lines.append(f"**Dependencies:** {', '.join(wf.get('dependencies', []))}")
        lines.append(f"")
        lines.append(f"### Inputs")
        for name, schema in wf.get("inputs", {}).items():
            req = " (required)" if schema.get("required") else ""
            default = f" (default: {schema.get('default', '')})" if "default" in schema else ""
            lines.append(f"- `{name}`: {schema.get('description', '')}{req}{default}")
        lines.append(f"")
        lines.append(f"### Outputs")
        for name, desc in wf.get("outputs", {}).items():
            lines.append(f"- `{name}`: {desc}")
        lines.append(f"")
        lines.append(f"[Workflow docs]({SDK_WORKFLOWS_URL})")
        lines.append(f"")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_workflow_run(args: Dict[str, Any]) -> Dict[str, Any]:
    workflow_id = args.get("workflow_id", "")
    if workflow_id not in WORKFLOW_CATALOG:
        return {
            "content": [{"type": "text", "text": f"❌ Unknown workflow: '{workflow_id}'. Available: {', '.join(WORKFLOW_CATALOG.keys())}"}],
            "isError": True,
        }

    wf = WORKFLOW_CATALOG[workflow_id]
    base_url = args.get("base_url", "")
    session_cookie = args.get("session_cookie", "")

    if not session_cookie and not args.get("api_key"):
        return {
            "content": [{"type": "text", "text": f"❌ Authentication required. Set session_cookie or api_key.\n\nDocs: {SDK_AUTH_URL}"}],
            "isError": True,
        }

    # Build the API call
    ctx = args.get("context", {})
    example = wf.get("example", {})

    lines = []
    lines.append(f"# Running `{wf['name']}` (`{workflow_id}`)")
    lines.append(f"")
    lines.append(f"To execute this workflow, make a POST request to:")
    lines.append(f"")
    lines.append(f"```")
    lines.append(f"POST {base_url or 'https://cascades.work'}/api/v1/workflows/{workflow_id}/run")
    lines.append(f"Content-Type: application/json")
    lines.append(f"Cookie: __session=<your-cookie>")
    lines.append(f"")
    if ctx:
        lines.append(json.dumps(ctx, indent=2))
    else:
        lines.append(json.dumps(example, indent=2))
    lines.append(f"```")
    lines.append(f"")
    lines.append(f"### Inputs")
    for name, schema in wf.get("inputs", {}).items():
        req = " (required)" if schema.get("required") else ""
        lines.append(f"- `{name}`: {schema.get('description', '')}{req}")
    lines.append(f"")
    lines.append(f"### Expected outputs")
    for name, desc in wf.get("outputs", {}).items():
        lines.append(f"- `{name}`: {desc}")
    lines.append(f"")
    lines.append(f"[Workflow docs]({SDK_WORKFLOWS_URL})")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_workflow_explain(args: Dict[str, Any]) -> Dict[str, Any]:
    workflow_id = args.get("workflow_id", "")
    if workflow_id not in WORKFLOW_CATALOG:
        # Check if it looks like a generic explanation request
        lines = []
        lines.append(f"# Workflow: `{workflow_id}`")
        lines.append(f"")
        lines.append(f"Workflows are DAGs (directed acyclic graphs) of tasks. Each task is a node;")
        lines.append(f"edges define the data flow between tasks. The Cascades engine executes the graph")
        lines.append(f"in topological order, running independent tasks in parallel.")
        lines.append(f"")
        lines.append(f"### Built-in workflows:")
        for wid, wf in WORKFLOW_CATALOG.items():
            lines.append(f"- `{wid}`: {wf['name']} — {wf['description'][:80]}...")
        lines.append(f"")
        lines.append(f"[Workflow docs]({SDK_WORKFLOWS_URL})")
        return {"content": [{"type": "text", "text": "\n".join(lines)}]}

    wf = WORKFLOW_CATALOG[workflow_id]
    lines = []
    lines.append(f"# {wf['name']} (`{workflow_id}`)")
    lines.append(f"")
    lines.append(f"**Version:** {wf['version']}")
    lines.append(f"**Description:** {wf['description']}")
    lines.append(f"**Dependencies:** {', '.join(wf.get('dependencies', []))}")
    lines.append(f"")
    lines.append(f"## Required Inputs")
    for name, schema in wf.get("inputs", {}).items():
        req = " ⚠️ required" if schema.get("required") else ""
        default = f" (default: {schema.get('default', '')})" if "default" in schema else ""
        lines.append(f"- `{name}`{req}: {schema.get('description', '')}{default}")
    lines.append(f"")
    lines.append(f"## Outputs")
    for name, desc in wf.get("outputs", {}).items():
        lines.append(f"- `{name}`: {desc}")
    lines.append(f"")
    lines.append(f"## Example")
    lines.append(f"```json")
    lines.append(json.dumps(wf.get("example", {}), indent=2))
    lines.append(f"```")
    lines.append(f"")
    lines.append(f"[Workflow docs]({SDK_WORKFLOWS_URL})")
    lines.append(f"[API reference]({SDK_API_REFERENCE_URL})")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_authenticate(args: Dict[str, Any]) -> Dict[str, Any]:
    base_url = args.get("base_url", "https://cascades.work")
    return {
        "content": [{"type": "text", "text": f"""
# Cascades Authentication

To authenticate with the Cascades API, you need a session cookie.

## Steps

1. **Open your Cascades deployment** in a browser:
   → [{base_url}]({base_url})

2. **Log in** via Auth0 (your identity provider).

3. **Get your session cookie**:
   - Chrome: F12 → Application → Cookies → `{base_url}` → Copy `__session`
   - Firefox: F12 → Storage → Cookies → Copy `__session`

4. **Use the cookie** in your SDK code:
   ```python
   from cascades_sdk import CascadesClient, SessionCookieAuth
   client = CascadesClient("{base_url}", SessionCookieAuth("PASTE_COOKIE_HERE"))
   ```

## Alternative: API Key

If your deployment supports API keys, use HeaderAuth:
```python
from cascades_sdk import HeaderAuth
client = CascadesClient("{base_url}", HeaderAuth({{"X-API-Key": "your-key"}}))
```

## Troubleshooting

- Cookie expired? → Re-login and get a fresh one.
- 401 errors? → Your session may have expired.
- 403 errors? → Your account may lack permissions.

📖 [Authentication docs]({SDK_AUTH_URL})
"""}.strip()}
    ]


def handle_config_check(args: Dict[str, Any]) -> Dict[str, Any]:
    results, summary = run_diagnostics(**args)
    errors = [r for r in results if r.status == "failed"]
    warnings = [r for r in results if r.status == "warning"]

    lines = []
    lines.append(f"# Cascades Configuration Check")
    lines.append(f"")
    if not errors and not warnings:
        lines.append(f"✅ All checks passed — configuration is valid.")
    else:
        if errors:
            lines.append(f"## ❌ Errors ({len(errors)})")
            for e in errors:
                lines.append(f"- **{e.check_name}**: {e.message}")
                if e.suggested_fix:
                    lines.append(f"  → Fix: {e.suggested_fix}")
                if e.doc_url:
                    lines.append(f"  → Docs: {e.doc_url}")
        if warnings:
            lines.append(f"## ⚠️ Warnings ({len(warnings)})")
            for w in warnings:
                lines.append(f"- **{w.check_name}**: {w.message}")
        lines.append(f"")
        lines.append(f"Run `cascades_diagnostics` with `auto_heal: true` to attempt automatic fixes.")

    return {"content": [{"type": "text", "text": "\n".join(lines)}]}


def handle_getting_started() -> Dict[str, Any]:
    return {
        "content": [{"type": "text", "text": f"""
# 🚀 Cascades — Getting Started

Welcome! Follow these steps to go from zero to your first workflow execution.

---

## Step 1: Install the SDK
```bash
pip install cascades-sdk
```

## Step 2: Authenticate
Run `cascades_authenticate` to get your session cookie.
📖 [Auth docs]({SDK_AUTH_URL})

## Step 3: Verify Connection
Run `cascades_config_check` with your base_url and session_cookie.

## Step 4: List Available Workflows
Run `cascades_workflow_list` to see what workflows you can execute.

## Step 5: Run Your First Workflow
Run `cascades_workflow_run` with `workflow_id: "osint-intake"` and a connector config.
📖 [Workflow docs]({SDK_WORKFLOWS_URL})

## Step 6: Check Results
Use the run ID from the workflow execution to check status.

## Step 7: Next Steps
- 📖 [Full documentation]({SDK_DOCS_URL})
- 🧪 [Examples]({SDK_EXAMPLES_URL})
- 🔧 [API reference]({SDK_API_REFERENCE_URL})
- 🐛 [Report issues](https://github.com/no1rstack/cascades-sdk/issues)
"""}.strip()}
    ]


# ─── MCP Server Main ──────────────────────────────────────

def main():
    """Run the MCP server using stdio transport (for use with AI assistants)."""
    import sys

    # Read JSON-RPC requests from stdin, write responses to stdout
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            request = json.loads(line)
        except json.JSONDecodeError:
            continue

        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "0.1.0",
                    "capabilities": {
                        "tools": {},
                        "resources": {},
                        "prompts": {},
                    },
                    "serverInfo": {
                        "name": "cascades-mcp",
                        "version": "0.1.0",
                    },
                },
            }
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "tools": list(TOOLS.values()),
                },
            }
        elif method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})
            result = handle_tool_call(tool_name, arguments)
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": result,
            }
        elif method == "resources/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "resources": [
                        {
                            "uri": "cascades://docs/getting-started",
                            "name": "Getting Started Guide",
                            "description": "Step-by-step onboarding guide",
                        },
                        {
                            "uri": "cascades://docs/authentication",
                            "name": "Authentication Guide",
                            "description": "How to authenticate with Cascades",
                        },
                        {
                            "uri": "cascades://docs/workflows",
                            "name": "Workflow Guide",
                            "description": "Available workflows and how to use them",
                        },
                        {
                            "uri": "cascades://docs/api",
                            "name": "API Reference",
                            "description": "Cascades API reference",
                        },
                    ],
                },
            }
        elif method == "resources/read":
            uri = params.get("uri", "")
            if uri == "cascades://docs/getting-started":
                text = handle_getting_started()["content"][0]["text"]
            elif uri == "cascades://docs/authentication":
                text = handle_authenticate({})["content"][0]["text"]
            elif uri == "cascades://docs/workflows":
                text = handle_workflow_list()["content"][0]["text"]
            else:
                text = f"Resource not found: {uri}"
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "contents": [
                        {
                            "uri": uri,
                            "mimeType": "text/markdown",
                            "text": text,
                        }
                    ],
                },
            }
        elif method == "prompts/list":
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "prompts": [
                        {
                            "name": "cascades_getting_started",
                            "description": "Guided onboarding through Cascades setup and first workflow",
                        },
                        {
                            "name": "cascades_diagnostics_run",
                            "description": "Run diagnostics and get a health report",
                        },
                    ],
                },
            }
        elif method == "prompts/get":
            prompt_name = params.get("name", "")
            if prompt_name == "cascades_getting_started":
                text = handle_getting_started()["content"][0]["text"]
            elif prompt_name == "cascades_diagnostics_run":
                text = handle_diagnostics({})["content"][0]["text"]
            else:
                text = f"Prompt not found: {prompt_name}"
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "messages": [
                        {
                            "role": "assistant",
                            "content": {
                                "type": "text",
                                "text": text,
                            },
                        }
                    ],
                },
            }
        elif method == "notifications/initialized":
            continue
        else:
            response = {
                "jsonrpc": "2.0",
                "id": req_id,
                "error": {"code": -32601, "message": f"Method not found: {method}"},
            }

        sys.stdout.write(json.dumps(response) + "\n")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
