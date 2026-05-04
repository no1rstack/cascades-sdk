"""Release, contract, and product metadata.

When the Cascades platform bumps ``info.version`` in ``contracts/api.yaml``, update
``API_CONTRACT_VERSION`` here to match (see ``tests/test_contract_parity.py``).
"""

from __future__ import annotations

from typing import Dict

__version__ = "0.3.0"

# Must match ``info.version`` in ``contracts/api.yaml`` (SDK ↔ platform HTTP boundary).
API_CONTRACT_VERSION = "1.0.0"

# --- Library / product markers (internal + optional HTTP telemetry) ---

SDK_NAME = "cascades-sdk-python"
PRODUCT_NAME = "Cascades"
COMPANY_NAME = "Noir Stack LLC"
SDK_MAINTAINER = "Hira Barton"
SDK_REPOSITORY_URL = "https://github.com/no1rstack/cascades-sdk"


def build_default_user_agent() -> str:
    """Default ``User-Agent`` sent on every request unless overridden on the client."""
    vendor_token = COMPANY_NAME.replace(" ", "+")
    return (
        f"{SDK_NAME}/{__version__} {PRODUCT_NAME} "
        f"(+{SDK_REPOSITORY_URL}; vendor={vendor_token})"
    )


DEFAULT_USER_AGENT = build_default_user_agent()


def vendor_telemetry_headers() -> Dict[str, str]:
    """
    Optional request headers for lightweight client identification.

    Enable via ``CascadesClient(..., vendor_headers=True)``. Names are stable for
    server-side logging or allowlists; values contain no secrets.
    """
    return {
        "X-SDK-Name": SDK_NAME,
        "X-SDK-Version": __version__,
        "X-Product": PRODUCT_NAME,
        "X-Vendor": COMPANY_NAME,
        "X-SDK-Maintainer": SDK_MAINTAINER,
        "X-SDK-Api-Contract": API_CONTRACT_VERSION,
    }
