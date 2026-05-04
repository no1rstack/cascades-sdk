#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

SRC="${1:-../cascades/contracts/api.yaml}"
exec python scripts/sync_contract.py "$SRC"
