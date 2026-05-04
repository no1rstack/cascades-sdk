#Requires -Version 5.0
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Split-Path -Parent $ScriptDir
Set-Location $Root

if ($args.Count -ge 1) {
  python scripts/sync_contract.py $args[0]
} else {
  python scripts/sync_contract.py
}
