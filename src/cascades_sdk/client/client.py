"""Unified HTTP client for every path in ``contracts/api.yaml``."""


from typing import Any, Dict, Iterator, Optional

from ..auth import Auth
from ..http_transport import HttpTransport
from ..sse import iter_sse_json_events


class CascadesClient:
    """
    Public Cascades API client.

    Most routes require ``cookieSession`` auth (see :mod:`cascades_sdk.auth`). ``GET /api/system/version``
    has no security requirement in the contract; you may call it with ``auth=None``.
    """

    def __init__(
        self,
        base_url: str,
        auth: Optional[Auth] = None,
        *,
        timeout: int = 30,
        verify_ssl: bool = True,
        user_agent: Optional[str] = None,
        vendor_headers: bool = False,
    ) -> None:
        """
        :param vendor_headers: When ``True``, add optional ``X-SDK-*`` / ``X-Product`` / ``X-Vendor``
            markers (same mapping as ``vendor_telemetry_headers()`` in ``cascades_sdk._meta``).
        """
        self._http = HttpTransport(
            base_url,
            auth,
            timeout=timeout,
            verify_ssl=verify_ssl,
            user_agent=user_agent,
            vendor_headers=vendor_headers,
        )

    def get_public_api_version(self) -> Dict[str, Any]:
        """``GET /api/system/version`` → ``ApiVersionResponse``."""
        return self._http.request_json("GET", "/api/system/version")

    def submit_workflow_run(self, body: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """``POST /api/workflows/run`` → ``WorkflowRunAccepted``."""
        return self._http.request_json("POST", "/api/workflows/run", json_body=body)

    def clone_catalog_workflow(self, body: Dict[str, Any]) -> Dict[str, Any]:
        """``POST /api/workflows/clone`` → ``WorkflowCloneResponse``."""
        return self._http.request_json("POST", "/api/workflows/clone", json_body=body)

    def iter_run_stream_events(
        self,
        run_id: str,
        *,
        since: Optional[str] = None,
        task_since: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """``GET /api/runs/{id}/stream`` — yields ``RunStreamEvent`` dicts ``{type, data}``."""
        params: Dict[str, Any] = {}
        if since is not None:
            params["since"] = since
        if task_since is not None:
            params["taskSince"] = task_since
        response = self._http.request_stream(
            "GET",
            f"/api/runs/{run_id}/stream",
            params=params or None,
        )
        try:
            yield from iter_sse_json_events(response.iter_lines(decode_unicode=True))
        finally:
            response.close()

    def save_github_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/github", json_body=body)

    def save_gitlab_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/gitlab", json_body=body)

    def save_jira_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/jira", json_body=body)

    def save_servicenow_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/servicenow", json_body=body)

    def save_slack_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/slack", json_body=body)

    def save_pagerduty_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/pagerduty", json_body=body)

    def save_hubspot_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/hubspot", json_body=body)

    def test_hubspot_integration(self) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/hubspot/test", json_body=None)

    def save_salesforce_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/salesforce", json_body=body)

    def test_salesforce_integration(self) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/salesforce/test", json_body=None)

    def save_vercel_integration(self, body: Dict[str, Any]) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/vercel", json_body=body)

    def test_vercel_integration(self) -> Dict[str, Any]:
        return self._http.request_json("POST", "/api/integrations/vercel/test", json_body=None)


CascadeClient = CascadesClient
