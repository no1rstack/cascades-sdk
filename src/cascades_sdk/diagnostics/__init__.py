"""
Cascades Shared Diagnostics — used by SDK, MCP server, and VS Code extension.

Provides a unified diagnostic engine that checks SDK/extension/MCP version
compatibility, network connectivity, authentication, permissions, workflow
validity, and environment configuration. Each check returns a structured
result with human-readable explanations, suggested fixes, and doc links.
"""


import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from .._meta import (
    SDK_DOCS_URL,
    SDK_AUTH_URL,
    SDK_GETTING_STARTED_URL,
    SDK_WORKFLOWS_URL,
    SDK_API_REFERENCE_URL,
)

# ─── Severity ─────────────────────────────────────────────

class DiagnosticSeverity:
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    FATAL = "fatal"

# ─── Result ───────────────────────────────────────────────

@dataclass
class DiagnosticFix:
    description: str
    action: str               # e.g. "open_url", "update_config", "run_command"
    action_data: Dict[str, Any] = field(default_factory=dict)
    auto_heal: bool = False   # can be applied automatically
    doc_url: Optional[str] = None

@dataclass
class DiagnosticResult:
    check_name: str
    status: str                # "passed" | "failed" | "warning" | "skipped"
    severity: str = DiagnosticSeverity.INFO
    message: str = ""
    explanation: str = ""
    suggested_fix: str = ""
    doc_url: Optional[str] = None
    fixes: List[DiagnosticFix] = field(default_factory=list)
    auto_healed: bool = False
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_name": self.check_name,
            "status": self.status,
            "severity": self.severity,
            "message": self.message,
            "explanation": self.explanation,
            "suggested_fix": self.suggested_fix,
            "doc_url": self.doc_url,
            "fixes": [f.__dict__ for f in self.fixes],
            "auto_healed": self.auto_healed,
            "duration_ms": self.duration_ms,
            "details": self.details,
        }

# ─── Check Base ───────────────────────────────────────────

class DiagnosticCheck:
    name: str = ""
    description: str = ""

    def run(self, context: Dict[str, Any]) -> DiagnosticResult:
        raise NotImplementedError

class DiagnosticsEngine:
    """Runs a set of checks and aggregates results."""

    def __init__(self, checks: Optional[List[DiagnosticCheck]] = None):
        self.checks: List[DiagnosticCheck] = checks or []
        self.results: List[DiagnosticResult] = []
        self.context: Dict[str, Any] = {}

    def add_check(self, check: DiagnosticCheck) -> None:
        self.checks.append(check)

    def set_context(self, **kwargs) -> None:
        self.context.update(kwargs)

    def run_all(self) -> List[DiagnosticResult]:
        self.results = []
        for check in self.checks:
            start = time.monotonic()
            try:
                result = check.run(self.context)
            except Exception as e:
                result = DiagnosticResult(
                    check_name=check.name,
                    status="failed",
                    severity=DiagnosticSeverity.ERROR,
                    message=f"Check crashed: {e}",
                    explanation="An unexpected error occurred while running this diagnostic.",
                    suggested_fix="Retry the check. If it persists, check the documentation.",
                    doc_url=f"{SDK_DOCS_URL}/troubleshooting",
                )
            result.duration_ms = (time.monotonic() - start) * 1000
            self.results.append(result)
        return self.results

    def get_summary(self) -> Dict[str, Any]:
        passed = sum(1 for r in self.results if r.status == "passed")
        failed = sum(1 for r in self.results if r.status == "failed")
        warnings = sum(1 for r in self.results if r.status == "warning")
        return {
            "total": len(self.results),
            "passed": passed,
            "failed": failed,
            "warnings": warnings,
            "healthy": failed == 0,
            "auto_healed": any(r.auto_healed for r in self.results),
        }

# ─── Built-in Checks ──────────────────────────────────────

class VersionCompatibilityCheck(DiagnosticCheck):
    name = "version_compatibility"
    description = "Check SDK, extension, and MCP version compatibility"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        sdk_version = ctx.get("sdk_version", "0.4.0")
        ext_version = ctx.get("extension_version", "0.1.0")
        mcp_version = ctx.get("mcp_version", "0.1.0")
        platform_version = ctx.get("platform_version", "2.3.0")

        result = DiagnosticResult(check_name=self.name, status="passed", severity=DiagnosticSeverity.INFO,
            message=f"SDK v{sdk_version}, Extension v{ext_version}, MCP v{mcp_version}, Platform v{platform_version}",
            explanation="All components are compatible with the current platform version.",
            doc_url=f"{SDK_DOCS_URL}/versioning",
        )
        # Check for major version mismatches
        sdk_major = sdk_version.split(".")[0]
        ext_major = ext_version.split(".")[0]
        if sdk_major != ext_major:
            result.status = "warning"
            result.severity = DiagnosticSeverity.WARNING
            result.message = f"SDK v{sdk_version} and Extension v{ext_version} have different major versions"
            result.explanation = "Using mismatched major versions may cause API incompatibilities."
            result.suggested_fix = f"Update the {'SDK' if sdk_major < ext_major else 'Extension'} to match."
            result.doc_url = f"{SDK_DOCS_URL}/versioning"
        return result


class ConnectivityCheck(DiagnosticCheck):
    name = "connectivity"
    description = "Check network connectivity to the Cascades platform"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        import requests
        base_url = ctx.get("base_url", "https://cascades.work")
        timeout = ctx.get("timeout", 10)

        result = DiagnosticResult(check_name=self.name, status="passed", severity=DiagnosticSeverity.INFO,
            message=f"Connected to {base_url}",
            doc_url=f"{SDK_DOCS_URL}/configuration",
        )

        try:
            start = time.monotonic()
            resp = requests.get(f"{base_url}/api/system/version", timeout=timeout)
            latency = (time.monotonic() - start) * 1000
            result.details["latency_ms"] = round(latency, 1)
            result.details["status_code"] = resp.status_code

            if resp.status_code == 200:
                result.message = f"Connected to {base_url} ({round(latency, 1)}ms)"
                result.details["api_version"] = resp.json().get("apiVersion", "unknown")
            else:
                result.status = "failed"
                result.severity = DiagnosticSeverity.ERROR
                result.message = f"Unexpected status {resp.status_code} from {base_url}"
                result.explanation = "The server responded but with an unexpected status code."
                result.suggested_fix = "Verify the base URL points to a valid Cascades deployment."
                result.doc_url = f"{SDK_DOCS_URL}/troubleshooting"
        except requests.exceptions.ConnectionError:
            result.status = "failed"
            result.severity = DiagnosticSeverity.FATAL
            result.message = f"Cannot connect to {base_url}"
            result.explanation = "The server is unreachable. Check your network and the base URL."
            result.suggested_fix = "Verify the base URL is correct and the server is running."
            result.doc_url = f"{SDK_DOCS_URL}/troubleshooting"
            result.fixes = [
                DiagnosticFix("Open network settings", "open_settings"),
                DiagnosticFix("Test a different URL", "run_command", {"command": f"curl {base_url}/api/system/version"}),
            ]
        except requests.exceptions.Timeout:
            result.status = "failed"
            result.severity = DiagnosticSeverity.ERROR
            result.message = f"Connection to {base_url} timed out after {timeout}s"
            result.explanation = "The server took too long to respond. It may be overloaded or the network is slow."
            result.suggested_fix = "Increase the timeout or check network latency."
            result.doc_url = f"{SDK_DOCS_URL}/troubleshooting"
            result.fixes = [
                DiagnosticFix("Retry with longer timeout", "update_config", {"timeout": 30}),
            ]
        except Exception as e:
            result.status = "failed"
            result.severity = DiagnosticSeverity.ERROR
            result.message = f"Connection error: {e}"
            result.explanation = "An unexpected network error occurred."
            result.suggested_fix = "Check your internet connection and firewall settings."
            result.doc_url = f"{SDK_DOCS_URL}/troubleshooting"

        return result


class AuthenticationCheck(DiagnosticCheck):
    name = "authentication"
    description = "Verify authentication credentials are valid"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        import requests
        base_url = ctx.get("base_url", "https://cascades.work")
        session_cookie = ctx.get("session_cookie") or ctx.get("api_key")

        result = DiagnosticResult(check_name=self.name, status="failed",
            severity=DiagnosticSeverity.FATAL,
            message="No authentication credentials configured",
            explanation="The Cascades API requires authentication via a session cookie or API key.",
            suggested_fix="Set your session cookie or API key in the configuration.",
            doc_url=SDK_AUTH_URL,
            fixes=[
                DiagnosticFix("Open authentication guide", "open_url", {"url": SDK_AUTH_URL}, auto_heal=False),
            ]
        )

        if not session_cookie:
            result.fixes.append(
                DiagnosticFix("Set session cookie now", "run_command", {"command": "authenticate"})
            )
            return result

        try:
            resp = requests.get(
                f"{base_url}/api/system/version",
                cookies={"__session": session_cookie} if session_cookie else None,
                timeout=10,
            )
            if resp.status_code == 200:
                result.status = "passed"
                result.severity = DiagnosticSeverity.INFO
                result.message = "Authentication credentials are valid"
                result.explanation = "The session cookie or API key is correctly configured."
            elif resp.status_code == 401:
                result.status = "failed"
                result.severity = DiagnosticSeverity.ERROR
                result.message = "Authentication failed: invalid or expired credentials"
                result.explanation = "Your session cookie has expired or is invalid."
                result.suggested_fix = "Re-authenticate by logging into your Cascades deployment and getting a fresh session cookie."
                result.doc_url = SDK_AUTH_URL
                result.fixes = [
                    DiagnosticFix("Re-authenticate now", "run_command", {"command": "authenticate"}, auto_heal=True),
                    DiagnosticFix("Open auth docs", "open_url", {"url": SDK_AUTH_URL}),
                ]
        except Exception as e:
            result.status = "failed"
            result.severity = DiagnosticSeverity.ERROR
            result.message = f"Auth check failed: {e}"
            result.explanation = "Could not verify authentication due to a network or server error."
            result.suggested_fix = "Check connectivity first, then retry authentication."
            result.doc_url = SDK_AUTH_URL

        return result


class ConfigurationCheck(DiagnosticCheck):
    name = "configuration"
    description = "Validate environment and configuration"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        base_url = ctx.get("base_url", "")
        issues = []

        # Check base URL format
        if not base_url:
            issues.append("base_url is not set")
        elif not base_url.startswith("http"):
            issues.append(f"base_url should start with http:// or https:// (got: {base_url})")

        if ctx.get("missing_tenant"):
            issues.append("No tenant selected")

        if not issues:
            return DiagnosticResult(check_name=self.name, status="passed",
                severity=DiagnosticSeverity.INFO,
                message="Configuration is valid",
                explanation="All required configuration values are present and correctly formatted.",
                doc_url=f"{SDK_DOCS_URL}/configuration",
            )

        return DiagnosticResult(check_name=self.name, status="failed",
            severity=DiagnosticSeverity.WARNING,
            message=f"Configuration issues found: {'; '.join(issues)}",
            explanation="Some configuration values are missing or incorrectly formatted.",
            suggested_fix="Update the configuration with the correct values.",
            doc_url=f"{SDK_DOCS_URL}/configuration",
            fixes=[
                DiagnosticFix("Open configuration settings", "open_settings"),
            ],
        )


class PermissionCheck(DiagnosticCheck):
    name = "permissions"
    description = "Verify required API scopes and permissions"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        required_scopes = ctx.get("required_scopes", [])
        user_scopes = ctx.get("user_scopes", [])

        if not required_scopes:
            return DiagnosticResult(check_name=self.name, status="passed",
                severity=DiagnosticSeverity.INFO,
                message="No specific permissions required",
            )

        missing = [s for s in required_scopes if s not in user_scopes]
        if not missing:
            return DiagnosticResult(check_name=self.name, status="passed",
                severity=DiagnosticSeverity.INFO,
                message="All required permissions are present",
                explanation=f"The account has all {len(required_scopes)} required scope(s).",
            )

        return DiagnosticResult(check_name=self.name, status="failed",
            severity=DiagnosticSeverity.ERROR,
            message=f"Missing {len(missing)} required scope(s): {', '.join(missing)}",
            explanation="Your account does not have the necessary permissions for this operation.",
            suggested_fix="Contact your administrator to request the missing scopes.",
            doc_url=f"{SDK_DOCS_URL}/authentication#scopes",
        )


class WorkflowConfigCheck(DiagnosticCheck):
    name = "workflow_config"
    description = "Validate workflow configuration"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        workflow = ctx.get("workflow", {})

        if not workflow:
            return DiagnosticResult(check_name=self.name, status="skipped",
                severity=DiagnosticSeverity.INFO,
                message="No workflow to validate",
            )

        issues = []
        workflow_id = workflow.get("id") or workflow.get("workflowId")
        if not workflow_id:
            issues.append("Workflow ID is required")
        if workflow.get("connectors") and not isinstance(workflow["connectors"], list):
            issues.append("collectors must be a list")
        if workflow.get("inputs") and not isinstance(workflow["inputs"], dict):
            issues.append("inputs must be a dict")

        if not issues:
            return DiagnosticResult(check_name=self.name, status="passed",
                severity=DiagnosticSeverity.INFO,
                message=f"Workflow '{workflow_id}' configuration is valid",
                doc_url=SDK_WORKFLOWS_URL,
            )

        return DiagnosticResult(check_name=self.name, status="failed",
            severity=DiagnosticSeverity.WARNING,
            message=f"Workflow '{workflow_id}' has {len(issues)} issue(s): {'; '.join(issues)}",
            explanation="The workflow configuration contains validation errors.",
            suggested_fix="Review the workflow configuration and fix the issues listed above.",
            doc_url=SDK_WORKFLOWS_URL,
            fixes=[
                DiagnosticFix("Open workflow builder", "open_url", {"url": f"{SDK_DOCS_URL.replace('/docs', '/builder')}"}),
            ],
        )


class NetworkLatencyCheck(DiagnosticCheck):
    name = "network_latency"
    description = "Measure network latency to the platform"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        import requests
        base_url = ctx.get("base_url", "https://cascades.work")

        latencies = []
        for _ in range(3):
            start = time.monotonic()
            try:
                requests.get(f"{base_url}/api/system/version", timeout=5)
                latencies.append((time.monotonic() - start) * 1000)
            except Exception:
                latencies.append(-1)

        valid = [l for l in latencies if l > 0]
        if not valid:
            return DiagnosticResult(check_name=self.name, status="failed",
                severity=DiagnosticSeverity.ERROR,
                message="Could not measure latency",
                explanation="All connectivity probes failed.",
                suggested_fix="Check your network connection.",
            )

        avg_latency = sum(valid) / len(valid)
        result = DiagnosticResult(check_name=self.name, status="passed",
            severity=DiagnosticSeverity.INFO,
            message=f"Average latency: {avg_latency:.0f}ms ({len(valid)}/{len(latencies)} probes succeeded)",
            details={"avg_latency_ms": round(avg_latency, 1), "probes": len(valid), "total": len(latencies)},
        )

        if avg_latency > 2000:
            result.status = "warning"
            result.severity = DiagnosticSeverity.WARNING
            result.message = f"High latency detected: {avg_latency:.0f}ms average"
            result.explanation = "High network latency may cause slow API responses and timeouts."
            result.suggested_fix = "Check your network connection or move to a closer region."
            result.doc_url = f"{SDK_DOCS_URL}/troubleshooting"

        return result


class EnvironmentCheck(DiagnosticCheck):
    name = "environment"
    description = "Check environment configuration (dev vs production)"

    def run(self, ctx: Dict[str, Any]) -> DiagnosticResult:
        env = ctx.get("environment", os.environ.get("CASCADES_ENV", "production"))
        base_url = ctx.get("base_url", "")

        result = DiagnosticResult(check_name=self.name, status="passed",
            severity=DiagnosticSeverity.INFO,
            message=f"Environment: {env}",
            details={"environment": env, "base_url": base_url},
        )

        if env == "production" and "localhost" in base_url:
            result.status = "warning"
            result.severity = DiagnosticSeverity.WARNING
            result.message = f"Environment is '{env}' but base_url points to localhost"
            result.explanation = "Using a localhost URL in production mode is unusual and may indicate a misconfiguration."
            result.suggested_fix = "Set CASCADES_ENV=development when using a local server."
            result.doc_url = f"{SDK_DOCS_URL}/configuration"

        return result


# ─── Engine factory ────────────────────────────────────────

def create_default_engine() -> DiagnosticsEngine:
    """Create a DiagnosticsEngine with all built-in checks pre-registered."""
    engine = DiagnosticsEngine()
    engine.add_check(VersionCompatibilityCheck())
    engine.add_check(ConfigurationCheck())
    engine.add_check(ConnectivityCheck())
    engine.add_check(AuthenticationCheck())
    engine.add_check(NetworkLatencyCheck())
    engine.add_check(PermissionCheck())
    engine.add_check(EnvironmentCheck())
    engine.add_check(WorkflowConfigCheck())
    return engine


def run_diagnostics(**context) -> Tuple[List[DiagnosticResult], Dict[str, Any]]:
    """Convenience: create engine, set context, run all checks, return results + summary."""
    engine = create_default_engine()
    engine.set_context(**context)
    results = engine.run_all()
    summary = engine.get_summary()
    return results, summary
