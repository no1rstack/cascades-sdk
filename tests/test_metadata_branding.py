from cascades_sdk import (
    DEFAULT_USER_AGENT,
    PRODUCT_NAME,
    SDK_NAME,
    __version__,
    vendor_telemetry_headers,
)
from cascades_sdk.http_transport import HttpTransport


def test_default_user_agent_identifies_sdk_product_and_repo():
    assert SDK_NAME in DEFAULT_USER_AGENT
    assert __version__ in DEFAULT_USER_AGENT
    assert PRODUCT_NAME in DEFAULT_USER_AGENT
    assert "github.com" in DEFAULT_USER_AGENT


def test_vendor_telemetry_headers_stable_keys():
    h = vendor_telemetry_headers()
    assert h["X-SDK-Name"] == SDK_NAME
    assert h["X-SDK-Version"] == __version__
    assert "X-Product" in h and "X-Vendor" in h
    assert h["X-SDK-Maintainer"] == "Hira Barton"
    assert h["X-SDK-Api-Contract"]


def test_vendor_headers_merged_when_enabled():
    t = HttpTransport("https://example.test", None, vendor_headers=True)
    merged = t._merge_headers(None)
    assert merged["X-SDK-Name"] == SDK_NAME
    assert merged["User-Agent"] == DEFAULT_USER_AGENT
