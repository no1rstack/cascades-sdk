"""
Cascades SDK — Python Client for the Cascades Workflow Engine
==============================================================

**cascades-sdk** is more than an API wrapper. It is a developer toolkit for
building, submitting, and monitoring workflows on the Cascades platform.

Quick links:
  - 📖 Documentation:      https://cascades.work/docs
  - 🚀 Getting Started:    https://cascades.work/docs/getting-started
  - 🔑 Authentication:     https://cascades.work/docs/authentication
  - 🔧 Workflow API:       https://cascades.work/docs/api
  - 🧪 Examples:           https://cascades.work/docs/examples
  - 🐛 Issues:             https://github.com/no1rstack/cascades-sdk/issues

Quick start (30 seconds):
    >>> from cascades_sdk import CascadesClient, SessionCookieAuth
    >>> from cascades_sdk.workflows import submit_and_wait
    >>> client = CascadesClient("https://cascades.work", SessionCookieAuth("my-session"))
    >>> result = submit_and_wait(client, "osint-intake", {"connectors": [...]})
    >>> print(result)
"""

from ._meta import (
    API_CONTRACT_VERSION,
    COMPANY_NAME,
    DEFAULT_USER_AGENT,
    PRODUCT_NAME,
    SDK_MAINTAINER,
    SDK_NAME,
    SDK_REPOSITORY_URL,
    SDK_DOCS_URL,
    SDK_GETTING_STARTED_URL,
    SDK_AUTH_URL,
    SDK_WORKFLOWS_URL,
    SDK_API_REFERENCE_URL,
    SDK_EXAMPLES_URL,
    __version__,
    build_default_user_agent,
    vendor_telemetry_headers,
)

from .compiler import (
    build_dag_from_flow,
    build_dag_from_flow_json,
    canonical_json,
    canonicalize_dag,
    flow,
    task,
)

from .client import (
    Auth,
    CascadeClient,
    CascadesClient,
    CascadesSDKError,
    CascadeSDKError,
    AuthenticationError,
    CompositeAuth,
    CookieHeaderAuth,
    EngineUnavailableError,
    HeaderAuth,
    NetworkError,
    NotFoundError,
    OrchestrationError,
    RateLimitError,
    ServerError,
    SessionCookieAuth,
    TimeoutError,
    ValidationError,
    normalize_auth,
    wait_for_completion,
    wait_for_completion_async,
    wait_for_run_terminal,
    wait_for_run_terminal_async,
)

from . import workflows
from . import getting_started
from . import examples

__all__ = [
    # Metadata
    "__version__",
    "API_CONTRACT_VERSION",
    "COMPANY_NAME",
    "DEFAULT_USER_AGENT",
    "PRODUCT_NAME",
    "SDK_MAINTAINER",
    "SDK_NAME",
    "SDK_REPOSITORY_URL",
    "SDK_DOCS_URL",
    "SDK_GETTING_STARTED_URL",
    "SDK_AUTH_URL",
    "SDK_WORKFLOWS_URL",
    "SDK_API_REFERENCE_URL",
    "SDK_EXAMPLES_URL",
    "build_default_user_agent",
    "vendor_telemetry_headers",
    # Compiler
    "task",
    "flow",
    "build_dag_from_flow",
    "build_dag_from_flow_json",
    "canonical_json",
    "canonicalize_dag",
    # Auth
    "Auth",
    "SessionCookieAuth",
    "CookieHeaderAuth",
    "HeaderAuth",
    "CompositeAuth",
    "normalize_auth",
    # Client
    "CascadesClient",
    "CascadeClient",
    # Polling
    "wait_for_completion",
    "wait_for_completion_async",
    "wait_for_run_terminal",
    "wait_for_run_terminal_async",
    # Errors
    "CascadesSDKError",
    "CascadeSDKError",
    "AuthenticationError",
    "ValidationError",
    "NotFoundError",
    "RateLimitError",
    "EngineUnavailableError",
    "ServerError",
    "OrchestrationError",
    "NetworkError",
    "TimeoutError",
    # Modules
    "workflows",
    "getting_started",
    "examples",
]
