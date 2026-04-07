"""Exception hierarchy for Cascades SDK."""


class CascadesSDKError(Exception):
    """Base exception for Cascades SDK errors."""

    def __init__(self, message: str, status_code: int = None, response_body: dict = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


# Backward-compatible alias
CascadeSDKError = CascadesSDKError


class AuthenticationError(CascadesSDKError):
    """Authentication failed (HTTP 401)."""


class ValidationError(CascadesSDKError):
    """Request validation failed (HTTP 400)."""


class NotFoundError(CascadesSDKError):
    """Resource was not found (HTTP 404)."""


class RateLimitError(CascadesSDKError):
    """Rate limit exceeded (HTTP 429)."""


class OrchestrationError(CascadesSDKError):
    """Control plane orchestration error (HTTP 5xx)."""


class NetworkError(CascadesSDKError):
    """Network communication failed."""


class TimeoutError(CascadesSDKError):
    """Request or polling timeout."""
