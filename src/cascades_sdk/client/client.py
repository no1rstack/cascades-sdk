"""HTTP client for Cascades control plane API."""

from typing import Any, Dict, Optional

import requests

from .errors import (
    CascadesSDKError,
    AuthenticationError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    OrchestrationError,
    NetworkError,
    TimeoutError as SDKTimeoutError,
)


class CascadesClient:
    """Thin HTTP client for Cascades flow registration and execution APIs."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: int = 30,
        verify_ssl: bool = True,
        task_output_path_template: str = "/api/runs/{run_id}/tasks/{task_id}/output",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.task_output_path_template = task_output_path_template

        self.session = requests.Session()
        self.session.headers.update(
            {
                "X-API-Key": api_key,
                "Content-Type": "application/json",
                "User-Agent": "cascades-sdk-python/0.2.0",
            }
        )

    def _request(
        self,
        method: str,
        path: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json,
                params=params,
                headers=headers,
                timeout=self.timeout,
                verify=self.verify_ssl,
            )
        except requests.exceptions.Timeout as exc:
            raise SDKTimeoutError(f"Request timeout after {self.timeout}s") from exc
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"Network error: {exc}") from exc

        try:
            response_body = response.json() if response.content else {}
        except ValueError:
            response_body = {"raw": response.text}

        if response.status_code == 401:
            raise AuthenticationError("Authentication failed - check API key", 401, response_body)
        if response.status_code == 400:
            raise ValidationError(response_body.get("title", "Validation failed"), 400, response_body)
        if response.status_code == 404:
            raise NotFoundError(response_body.get("title", "Resource not found"), 404, response_body)
        if response.status_code == 429:
            raise RateLimitError(response_body.get("title", "Rate limit exceeded"), 429, response_body)
        if response.status_code >= 500:
            raise OrchestrationError(response_body.get("title", "Server error"), response.status_code, response_body)
        if not response.ok:
            raise CascadesSDKError(f"HTTP {response.status_code}: {response.text}", response.status_code, response_body)

        return response_body

    def register_flow(self, flow_name: str, dag: Dict[str, Any], version: str = "1.0.0") -> str:
        response = self._request(
            "POST",
            "/api/flows/register",
            json={"name": flow_name, "version": version, "dag": dag},
        )
        return response["id"]

    def trigger_flow(self, flow_id: str, inputs: Dict[str, Any]) -> str:
        response = self._request("POST", "/api/runs", json={"flow_id": flow_id, "input": inputs})
        return response["run_id"]

    def get_run(self, run_id: str) -> Dict[str, Any]:
        run = self._request("GET", f"/api/runs/{run_id}")
        status = run.get("status")
        if isinstance(status, str):
            run["status"] = status.lower()

        if "result" not in run and "output" in run:
            run["result"] = run.get("output")

        return run

    def get_flow_graph(self, flow_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/flows/definitions/{flow_id}/graph")

    def get_run_graph(self, run_id: str) -> Dict[str, Any]:
        return self._request("GET", f"/api/flow-runs/{run_id}/graph")

    def submit_task_output(
        self,
        run_id: str,
        task_id: str,
        output: Any,
        metadata: Optional[Dict[str, Any]] = None,
        path_template: Optional[str] = None,
    ) -> Dict[str, Any]:
        template = path_template or self.task_output_path_template
        path = template.format(run_id=run_id, task_id=task_id)
        payload: Dict[str, Any] = {"output": output}
        if metadata:
            payload["metadata"] = metadata
        return self._request("POST", path, json=payload)


# Backward-compatible alias
CascadeClient = CascadesClient
