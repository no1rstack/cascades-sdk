"""Exception hierarchy with consistent mapping from HTTP responses."""

from __future__ import annotations

from typing import Any, Optional

import requests


class CascadesSDKError(Exception):
    """Base exception; carries HTTP context when the failure came from the API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Any = None,
        response_text: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body
        self.response_text = response_text


CascadeSDKError = CascadesSDKError


def _parse_body(response: "requests.Response") -> Any:
    if not response.content:
        return None
    try:
        return response.json()
    except ValueError:
        return None


def _message_from(body: Any, fallback_text: str) -> str:
    if isinstance(body, dict):
        for key in ("message", "title", "error", "detail"):
            val = body.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
    text = (fallback_text or "").strip()
    return text or "Request failed"


def raise_for_status(response: "requests.Response") -> None:
    """Raise a typed SDK error from a non-success ``requests.Response``."""
    if response.ok:
        return
    body = _parse_body(response)
    text = response.text or ""
    message = _message_from(body, text)
    status = response.status_code

    if status == 401:
        raise AuthenticationError(message, status, body, text)
    if status == 404:
        raise NotFoundError(message, status, body, text)
    if status == 400:
        raise ValidationError(message, status, body, text)
    if status == 429:
        raise RateLimitError(message, status, body, text)
    if status == 503:
        if isinstance(body, dict) and body.get("error") == "Execution engine unavailable":
            raise EngineUnavailableError(message, status, body, text)
        raise ServerError(message, status, body, text)
    if status >= 500:
        raise ServerError(message, status, body, text)
    raise CascadesSDKError(message, status, body, text)


class AuthenticationError(CascadesSDKError):
    """HTTP 401 — missing or invalid session / credentials."""


class ValidationError(CascadesSDKError):
    """HTTP 400 — contract / validation failure."""


class NotFoundError(CascadesSDKError):
    """HTTP 404 — resource missing or not permitted for this caller."""


class RateLimitError(CascadesSDKError):
    """HTTP 429 — rate limited."""


class EngineUnavailableError(CascadesSDKError):
    """HTTP 503 — worker queue / execution engine unavailable (contract ``WorkflowEngineUnavailable``)."""


class ServerError(CascadesSDKError):
    """HTTP 5xx — unexpected server failure."""


OrchestrationError = ServerError


class NetworkError(CascadesSDKError):
    """Transport failure before an HTTP response was received."""


class TimeoutError(CascadesSDKError):
    """Request or wait timeout."""
