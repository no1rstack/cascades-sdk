"""Parity checks between the wheel and ``contracts/api.yaml``."""

from pathlib import Path

from cascades_sdk import API_CONTRACT_VERSION


def _info_version_from_contract() -> str:
    text = (Path(__file__).resolve().parents[1] / "contracts" / "api.yaml").read_text(encoding="utf-8")
    in_info = False
    for line in text.splitlines():
        if line.startswith("info:"):
            in_info = True
            continue
        if in_info:
            if line and not line[0].isspace():
                break
            stripped = line.strip()
            if stripped.startswith("version:"):
                _, _, rhs = stripped.partition(":")
                rhs = rhs.split("#", 1)[0].strip()
                return rhs.strip().strip('"').strip("'")
    raise AssertionError("Could not parse info.version from contracts/api.yaml")


def test_api_contract_version_matches_openapi_info():
    assert API_CONTRACT_VERSION == _info_version_from_contract()
