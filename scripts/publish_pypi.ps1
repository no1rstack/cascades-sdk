#Requires -Version 5.0
# Load PyPI credentials from a .env-style file, build, upload.
# Uses: TWINE_USERNAME + TWINE_PASSWORD, or PYPI_TOKEN / PYPI_API_TOKEN with username __token__.
# Does not print secret values.
#
# Env file resolution (first match wins):
#   1) -EnvFile "C:\path\.env.local"
#   2) process env CASCADES_SDK_ENV_FILE
#   3) default: <repo-parent>\cascades\.env.local  (e.g. ../cascades/.env.local next to cascades-sdk)

param(
    [string]$EnvFile = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SdkRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    $EnvFile = [Environment]::GetEnvironmentVariable("CASCADES_SDK_ENV_FILE", "Process")
}
if ([string]::IsNullOrWhiteSpace($EnvFile)) {
    $EnvFile = Join-Path (Split-Path $SdkRoot -Parent) "cascades\.env.local"
}

if (-not (Test-Path -LiteralPath $EnvFile)) {
    Write-Error "Env file not found: $EnvFile"
    exit 2
}

Get-Content -LiteralPath $EnvFile | ForEach-Object {
    $line = $_.TrimEnd()
    if ($line -match "^\s*#" -or $line -eq "") { return }
    $m = [regex]::Match($line, "^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)$")
    if (-not $m.Success) { return }
    $k = $m.Groups[1].Value
    $v = $m.Groups[2].Value.Trim()
    if ($v.Length -ge 2) {
        $q0 = $v[0]
        $qn = $v[$v.Length - 1]
        if (($q0 -eq '"' -and $qn -eq '"') -or ($q0 -eq "'" -and $qn -eq "'")) {
            $v = $v.Substring(1, $v.Length - 2)
        }
    }
    [Environment]::SetEnvironmentVariable($k, $v, "Process")
}

if (-not $env:TWINE_PASSWORD) {
    if ($env:PYPI_TOKEN) {
        [Environment]::SetEnvironmentVariable("TWINE_USERNAME", "__token__", "Process")
        [Environment]::SetEnvironmentVariable("TWINE_PASSWORD", $env:PYPI_TOKEN, "Process")
    }
    elseif ($env:PYPI_API_TOKEN) {
        [Environment]::SetEnvironmentVariable("TWINE_USERNAME", "__token__", "Process")
        [Environment]::SetEnvironmentVariable("TWINE_PASSWORD", $env:PYPI_API_TOKEN, "Process")
    }
    elseif ($env:PYPI_API_KEY) {
        if ($env:PYPI_USERNAME) {
            [Environment]::SetEnvironmentVariable("TWINE_USERNAME", $env:PYPI_USERNAME, "Process")
        }
        else {
            [Environment]::SetEnvironmentVariable("TWINE_USERNAME", "__token__", "Process")
        }
        [Environment]::SetEnvironmentVariable("TWINE_PASSWORD", $env:PYPI_API_KEY, "Process")
    }
}

if (-not $env:TWINE_PASSWORD) {
    Write-Error "No PyPI credentials: set TWINE_USERNAME+TWINE_PASSWORD, or PYPI_TOKEN / PYPI_API_TOKEN, or PYPI_API_KEY (+ optional PYPI_USERNAME) in $EnvFile"
    exit 2
}
if (-not $env:TWINE_USERNAME) {
    [Environment]::SetEnvironmentVariable("TWINE_USERNAME", "__token__", "Process")
}

Set-Location $SdkRoot

python -m pip install -q build twine
python -m build
python -m twine check dist/*
$dist = Join-Path $SdkRoot "dist"
$files = @()
$files += Get-ChildItem -Path $dist -Filter "*.whl" -ErrorAction SilentlyContinue
$files += Get-ChildItem -Path $dist -Filter "*.tar.gz" -ErrorAction SilentlyContinue
if ($files.Count -eq 0) {
    Write-Error "No wheel or sdist under $dist"
    exit 2
}
$uploadArgs = @("upload") + ($files | ForEach-Object { $_.FullName }) + @("--non-interactive")
if ($env:PYPI_URL -and $env:PYPI_URL.Trim() -ne "") {
    $uploadArgs = @("upload") + ($files | ForEach-Object { $_.FullName }) + @("--repository-url", $env:PYPI_URL.Trim(), "--non-interactive")
}
python -m twine @uploadArgs
Write-Host "PyPI upload finished."
