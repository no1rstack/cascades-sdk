#!/usr/bin/env python3
"""
Copy the Cascades platform contracts/api.yaml into this repo as contracts/api.yaml
using LF line endings only, then run verify_contract_mirror.py against the source.

Usage:
  python scripts/sync_contract.py
  python scripts/sync_contract.py ../cascades/contracts/api.yaml
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _to_lf(data: bytes) -> bytes:
    return data.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def _default_platform_contract(sdk_root: Path) -> Path:
    return sdk_root.parent / "cascades" / "contracts" / "api.yaml"


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[1]
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "source",
        nargs="?",
        type=Path,
        default=None,
        help="Path to platform contracts/api.yaml (default: ../cascades/contracts/api.yaml next to this repo)",
    )
    args = ap.parse_args(argv)

    src = (args.source or _default_platform_contract(root)).resolve()
    dst = root / "contracts" / "api.yaml"

    if not os.path.exists(src):
        print(f"error: source contract path does not exist: {src}", file=sys.stderr)
        return 2
    if not src.is_file():
        print(f"error: source contract is not a file: {src}", file=sys.stderr)
        return 2

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(_to_lf(src.read_bytes()))

    verify = root / "scripts" / "verify_contract_mirror.py"
    r = subprocess.run(
        [sys.executable, str(verify), "--against", str(src)],
        cwd=str(root),
    )
    if r.returncode == 0:
        print(f"Contract synced and verified.\n  {dst}\n  <= {src}")
    return int(r.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
