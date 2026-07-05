"""Exception hierarchy with consistent mapping from HTTP responses.

Every error includes a link to the relevant documentation to help
developers quickly troubleshoot issues.
"""

from __future__ import annotations

from typing import Any, Optional

import requests

from ._meta import SDK_DOCS_URL, SDK_AUTH_URL, SDK_WORKFLOWS_URL


class CascadesSDKError(Exception):
    """Base exception; carries HTTP context when the failure came from the API."""

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_body: Any = None,
        response_text: Optional[str] = None,
        doc_url: Optional[str] = None,
    ) -> None:
        self.status_code = status_code
        self.response_body = response_body
        self.response_text = response_text
        self.doc_url = doc_url
        parts = [message]
        if doc_url:
            parts.append(f"\n  → Docs: {doc_url}")
        super().__init__("".join(parts))


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
    """HTTP 401 — missing or invalid session / credentials.

    See https://cascades.work/docs/authentication for setup instructions.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("doc_url", SDK_AUTH_URL)
        msg = (
            "Authentication failed. Your session cookie may be expired or invalid.\n"
            "  → Get a new session by logging in at your Cascades deployment.\n"
            "  → Pass it to SessionCookieAuth or CookieHeaderAuth."
        )
        if args and isinstance(args[0], str):
            args = (f"{msg}\n  Server: {args[0]}",) + args[1:]
        else:
            args = (msg,) + args
        super().__init__(*args, **kwargs)


class ValidationError(CascadesSDKError):
    """HTTP 400 — contract / validation failure.

    See https://cascades.work/docs/api for the expected request schema.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("doc_url", f"{SDK_DOCS_URL}/api")
        super().__init__(*args, **kwargs)


class NotFoundError(CascadesSDKError):
    """HTTP 404 — resource missing or not permitted for this caller.

    Verify the resource ID (workflowId, runId, etc.) is correct.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("doc_url", SDK_WORKFLOWS_URL)
        super().__init__(*args, **kwargs)


class RateLimitError(CascadesSDKError):
    """HTTP 429 — rate limited.

    Reduce request frequency or contact Noir Stack LLC to increase your rate limit.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("doc_url", f"{SDK_DOCS_URL}/rate-limits")
        super().__init__(*args, **kwargs)


class EngineUnavailableError(CascadesSDKError):
    """HTTP 503 — worker queue / execution engine unavailable.

    The workflow was accepted but the execution engine is offline or
    requires a worker queue. See docs for deployment configuration.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("doc_url", SDK_WORKFLOWS_URL)
        super().__init__(*args, **kwargs)


class ServerError(CascadesSDKError):
    """HTTP 5xx — unexpected server failure.

    Retry the request. If the error persists, check the platform status
    or contact support.
    """


OrchestrationError = ServerError


class NetworkError(CascadesSDKError):
    """Transport failure before an HTTP response was received.

    Check your network connectivity and verify the base URL is correct.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        kwargs.setdefault("doc_url", f"{SDK_DOCS_URL}/troubleshooting")
        super().__init__(*args, **kwargs)


class TimeoutError(CascadesSDKError):
    """Request or wait timeout.

    The operation took longer than the configured timeout. For long-running
    workflows, increase the timeout or use async polling.
    """
