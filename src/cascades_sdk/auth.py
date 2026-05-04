"""Authentication strategies aligned with ``contracts/api.yaml`` security schemes."""

from __future__ import annotations

from typing import Dict, List, Mapping, Optional, Protocol, Tuple


class Auth(Protocol):
    """Produces HTTP headers merged into each request (case-sensitive names as sent on the wire)."""

    def request_headers(self) -> Mapping[str, str]:
        ...


class SessionCookieAuth:
    """
    ``cookieSession`` scheme: Auth0-style session cookie (contract default name ``__session``).

    Pass the raw cookie **value** only, or use :class:`CookieHeaderAuth` for a full ``Cookie`` header
    copied from the browser.
    """

    __slots__ = ("_cookie_name", "_cookie_value")

    def __init__(self, cookie_value: str, *, cookie_name: str = "__session") -> None:
        if not cookie_value:
            raise ValueError("cookie_value must be non-empty")
        self._cookie_name = cookie_name
        self._cookie_value = cookie_value

    def request_headers(self) -> Mapping[str, str]:
        return {"Cookie": f"{self._cookie_name}={self._cookie_value}"}


class CookieHeaderAuth:
    """Use when you already have a full ``Cookie`` header string (multiple cookies supported)."""

    __slots__ = ("_header",)

    def __init__(self, cookie_header: str) -> None:
        if not cookie_header or not cookie_header.strip():
            raise ValueError("cookie_header must be non-empty")
        self._header = cookie_header.strip()

    def request_headers(self) -> Mapping[str, str]:
        return {"Cookie": self._header}


class HeaderAuth:
    """
    Fixed extra headers per request (e.g. deployment-specific ``Authorization`` or API keys).

    The public contract documents ``cookieSession``; tenants may document additional headers
    for automation — supply them here.
    """

    __slots__ = ("_headers",)

    def __init__(self, headers: Mapping[str, str]) -> None:
        if not headers:
            raise ValueError("headers must be non-empty")
        self._headers = dict(headers)

    def request_headers(self) -> Mapping[str, str]:
        return dict(self._headers)


class CompositeAuth:
    """Merge headers from several strategies (later keys override earlier ones)."""

    __slots__ = ("_parts",)

    def __init__(self, *parts: Auth) -> None:
        if not parts:
            raise ValueError("CompositeAuth requires at least one Auth strategy")
        self._parts = tuple(parts)

    def request_headers(self) -> Mapping[str, str]:
        merged: Dict[str, str] = {}
        for p in self._parts:
            merged.update(p.request_headers())
        return merged


def normalize_auth(
    auth: Optional[Auth] = None,
    *,
    cookie: Optional[str] = None,
    cookie_name: str = "__session",
    headers: Optional[Mapping[str, str]] = None,
) -> Optional[Auth]:
    """
    Convenience: build :class:`CompositeAuth` from optional cookie value and/or static headers.

    Exactly one of ``auth``, ``cookie``, or ``headers`` should be used in application code; this
    helper exists for ergonomic construction in scripts.
    """
    if auth is not None and (cookie is not None or headers is not None):
        raise ValueError("Pass either auth=... or cookie=/headers=, not both")
    if auth is not None:
        return auth
    parts: List[Auth] = []
    if cookie is not None:
        parts.append(SessionCookieAuth(cookie, cookie_name=cookie_name))
    if headers is not None:
        parts.append(HeaderAuth(dict(headers)))
    if not parts:
        return None
    if len(parts) == 1:
        return parts[0]
    return CompositeAuth(*parts)
