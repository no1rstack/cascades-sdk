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

$pyprojectPath = Join-Path $SdkRoot "pyproject.toml"
$pyprojectRaw = Get-Content -LiteralPath $pyprojectPath -Raw
if ($pyprojectRaw -notmatch '(?m)^version\s*=\s*"([^"]+)"') {
    Write-Error "Could not parse version from $pyprojectPath"
    exit 2
}
$ReleaseVersion = $Matches[1].Trim()

$dist = Join-Path $SdkRoot "dist"
if (Test-Path -LiteralPath $dist) {
    # Do not use -LiteralPath with "*": it will not expand and stale wheels remain (wrong twine check / uploads).
    Get-ChildItem -LiteralPath $dist -Force | Remove-Item -Recurse -Force -ErrorAction Stop
}
else {
    New-Item -ItemType Directory -Path $dist | Out-Null
}

# Common mistake: PYPI_URL copied from a browser project tab — Twine needs the upload API, not /project/…
if ($env:PYPI_URL -and $env:PYPI_URL.Trim() -ne "") {
    $candidate = $env:PYPI_URL.Trim()
    if ($candidate -match "pypi\.org/project/") {
        Write-Warning "PYPI_URL is a project page ($candidate), not an upload endpoint. Clearing for this run; use https://upload.pypi.org/legacy/ or omit PYPI_URL. Fix your .env file."
        [Environment]::SetEnvironmentVariable("PYPI_URL", "", "Process")
    }
}

python -m pip install -q build twine
python -m build

# Only this release — never upload stale wheels/sdists (they may target a legacy PyPI project name).
$wheel = Get-ChildItem -Path $dist -Filter "cascades_sdk-$ReleaseVersion-*.whl" -ErrorAction SilentlyContinue | Select-Object -First 1
$sdist = Get-ChildItem -Path $dist -Filter "cascades_sdk-$ReleaseVersion.tar.gz" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $wheel -or -not $sdist) {
    Write-Error "Expected one wheel cascades_sdk-$ReleaseVersion-*.whl and one sdist cascades_sdk-$ReleaseVersion.tar.gz under $dist."
    exit 2
}

python -m twine check $wheel.FullName $sdist.FullName

Write-Host "Uploading only: $($wheel.Name), $($sdist.Name) (pyproject version $ReleaseVersion)"

$files = @($wheel, $sdist)
$uploadArgs = @("upload") + ($files | ForEach-Object { $_.FullName }) + @("--non-interactive")
if ($env:PYPI_URL -and $env:PYPI_URL.Trim() -ne "") {
    $ru = $env:PYPI_URL.Trim()
    $uploadArgs = @("upload") + ($files | ForEach-Object { $_.FullName }) + @("--repository-url", $ru, "--non-interactive")
}
python -m twine @uploadArgs
Write-Host "PyPI upload finished."
