#!/usr/bin/env python3
"""
Fail unless contracts/api.yaml is an exact mirror of the Cascades platform contract.

Compared bytes are normalized to LF line endings so CRLF checkouts do not false-fail.

CI always clones no1rstack/cascades and runs with --against (no dependency on raw GitHub URLs).

Usage:
  python scripts/verify_contract_mirror.py --against ../cascades/contracts/api.yaml
      # recommended locally (and same flags CI uses against a checkout)

  python scripts/verify_contract_mirror.py
      # optional: fetch from raw.githubusercontent.com (public repos only; may 404 if private)

  python scripts/verify_contract_mirror.py --remote-ref abcdef1
      # optional: branch, tag, or full SHA on no1rstack/cascades for remote fetch mode
"""

from __future__ import annotations

import argparse
import sys
import urllib.error
import urllib.request
from pathlib import Path

PLATFORM_RAW = (
    "https://raw.githubusercontent.com/no1rstack/cascades/{ref}/contracts/api.yaml"
)


def _norm(b: bytes) -> bytes:
    return b.replace(b"\r\n", b"\n")


def _read_local_contract(root: Path) -> bytes:
    path = root / "contracts" / "api.yaml"
    if not path.is_file():
        print(f"error: missing SDK contract file: {path}", file=sys.stderr)
        raise SystemExit(2)
    return _norm(path.read_bytes())


def _read_platform_file(path: Path) -> bytes:
    if not path.is_file():
        print(f"error: not a file: {path}", file=sys.stderr)
        raise SystemExit(2)
    return _norm(path.read_bytes())


def _fetch_platform_remote(ref: str) -> bytes:
    url = PLATFORM_RAW.format(ref=ref)
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "cascades-sdk-verify-contract-mirror/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=90) as resp:
            return _norm(resp.read())
    except urllib.error.HTTPError as e:
        print(f"error: HTTP {e.code} fetching {url}", file=sys.stderr)
        raise SystemExit(2) from e
    except urllib.error.URLError as e:
        print(f"error: fetch failed {url}: {e}", file=sys.stderr)
        raise SystemExit(2) from e


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--against",
        type=Path,
        default=None,
        metavar="PATH",
        help="Path to the platform repository's contracts/api.yaml",
    )
    ap.add_argument(
        "--remote-ref",
        default="main",
        metavar="REF",
        help="Git ref on no1rstack/cascades when --against is omitted (default: main)",
    )
    args = ap.parse_args(argv)

    local = _read_local_contract(root)

    if args.against is not None:
        other = _read_platform_file(args.against.resolve())
        label = str(args.against.resolve())
    else:
        other = _fetch_platform_remote(args.remote_ref)
        label = PLATFORM_RAW.format(ref=args.remote_ref)

    if local != other:
        print(
            "error: contracts/api.yaml is not identical to the platform contract "
            "(after LF normalization).",
            file=sys.stderr,
        )
        print(f"  sdk:    {root / 'contracts' / 'api.yaml'} ({len(local)} bytes)", file=sys.stderr)
        print(f"  other:  {label} ({len(other)} bytes)", file=sys.stderr)
        print(
            "  Fix: sync from the Cascades platform repo, e.g.\n"
            "    ./scripts/sync_contract.sh ../cascades/contracts/api.yaml\n"
            "    # or: python scripts/sync_contract.py ../cascades/contracts/api.yaml",
            file=sys.stderr,
        )
        return 1

    print(f"OK: contracts/api.yaml matches platform ({label})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
