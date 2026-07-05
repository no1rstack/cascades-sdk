"""Central HTTP session and request/response handling for the Cascades API."""


from typing import Any, Dict, Mapping, Optional

import requests

from ._meta import DEFAULT_USER_AGENT, vendor_telemetry_headers
from .auth import Auth
from .errors import (
    AuthenticationError,
    CascadesSDKError,
    EngineUnavailableError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TimeoutError as SDKTimeoutError,
    ValidationError,
    raise_for_status,
)


class HttpTransport:
    """Shared ``requests.Session``, headers, timeouts, and error normalization."""

    def __init__(
        self,
        base_url: str,
        auth: Optional[Auth],
        *,
        timeout: int = 30,
        verify_ssl: bool = True,
        user_agent: Optional[str] = None,
        vendor_headers: bool = False,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.auth = auth
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.user_agent = user_agent or DEFAULT_USER_AGENT
        self._vendor_headers = vendor_headers

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "application/json, text/plain, */*",
            }
        )

    def _merge_headers(self, extra: Optional[Mapping[str, str]]) -> Dict[str, str]:
        merged: Dict[str, str] = {}
        for k, v in self.session.headers.items():
            if isinstance(v, str):
                merged[str(k)] = v
        if self._vendor_headers:
            merged.update(vendor_telemetry_headers())
        if self.auth is not None:
            merged.update(dict(self.auth.request_headers()))
        if extra:
            merged.update(dict(extra))
        return merged

    def request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
        stream: bool = False,
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        hdrs = self._merge_headers(headers)
        if json_body is not None:
            hdrs.setdefault("Content-Type", "application/json")
        req_timeout: Any = self.timeout
        if stream:
            # Long-lived SSE: no read timeout; connect still bounded.
            req_timeout = (self.timeout, None)
        try:
            return self.session.request(
                method=method.upper(),
                url=url,
                json=json_body,
                params=dict(params) if params else None,
                headers=hdrs,
                timeout=req_timeout,
                verify=self.verify_ssl,
                stream=stream,
            )
        except requests.exceptions.Timeout as exc:
            raise SDKTimeoutError(f"Request timeout after {self.timeout}s") from exc
        except requests.exceptions.ConnectionError as exc:
            raise NetworkError(f"Connection failed: {exc}") from exc
        except requests.exceptions.RequestException as exc:
            raise NetworkError(f"Network error: {exc}") from exc

    def request_json(
        self,
        method: str,
        path: str,
        *,
        json_body: Any = None,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> Any:
        response = self.request(
            method,
            path,
            json_body=json_body,
            params=params,
            headers=headers,
            stream=False,
        )
        raise_for_status(response)
        if not response.content:
            return None
        ct = (response.headers.get("Content-Type") or "").split(";")[0].strip().lower()
        if ct == "application/json" or ct.endswith("+json"):
            try:
                return response.json()
            except ValueError as exc:
                raise CascadesSDKError(
                    "Invalid JSON in success response",
                    status_code=response.status_code,
                    response_body={"raw": response.text},
                ) from exc
        try:
            return response.json()
        except ValueError:
            return {"raw": response.text}

    def request_stream(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Mapping[str, Any]] = None,
        headers: Optional[Mapping[str, str]] = None,
    ) -> requests.Response:
        response = self.request(method, path, params=params, headers=headers, stream=True)
        if not response.ok:
            # Drain body for error parsing
            try:
                response.content
            except Exception:
                pass
            raise_for_status(response)
        return response
