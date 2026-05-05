#Requires -Version 5.0
# Publish @noirstack/cascades-sdk to the npm registry from the cascades-sdk repo.
# Loads NPM_TOKEN / NODE_AUTH_TOKEN from a .env-style file (values are not echoed).
#
# Env file resolution (first match wins) — same defaults as publish_pypi.ps1:
#   1) -EnvFile "C:\path\.env.local"
#   2) process env CASCADES_SDK_ENV_FILE
#   3) default: <repo-parent>\cascades\.env.local

param(
    [string]$EnvFile = "",
    [switch]$DryRun
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$SdkRoot = Split-Path -Parent $PSScriptRoot
$PkgRoot = Join-Path $SdkRoot "packages\cascades-sdk"

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

if (-not $env:NODE_AUTH_TOKEN) {
    if ($env:NPM_TOKEN) {
        [Environment]::SetEnvironmentVariable("NODE_AUTH_TOKEN", $env:NPM_TOKEN, "Process")
    }
}

if (-not $env:NODE_AUTH_TOKEN) {
    Write-Error "No npm credentials: set NPM_TOKEN or NODE_AUTH_TOKEN in $EnvFile"
    exit 2
}

if ($env:NPM_REGISTRY -and $env:NPM_REGISTRY.Trim() -ne "") {
    $nr = $env:NPM_REGISTRY.Trim()
    if ($nr -match "npmjs\.com/package/") {
        Write-Warning "NPM_REGISTRY looks like a project page ($nr), not a registry URL. Clearing for this run; use https://registry.npmjs.org/ or omit NPM_REGISTRY."
        [Environment]::SetEnvironmentVariable("NPM_REGISTRY", "", "Process")
    }
}

$pkgJsonPath = Join-Path $PkgRoot "package.json"
if (-not (Test-Path -LiteralPath $pkgJsonPath)) {
    Write-Error "Missing package: $pkgJsonPath"
    exit 2
}

$pkgRaw = Get-Content -LiteralPath $pkgJsonPath -Raw
if ($pkgRaw -match '"private"\s*:\s*true') {
    Write-Error "Refusing to publish: $pkgJsonPath has private: true"
    exit 2
}
if ($pkgRaw -notmatch '"version"\s*:\s*"([^"]+)"') {
    Write-Error "Could not parse version from $pkgJsonPath"
    exit 2
}
$ReleaseVersion = $Matches[1].Trim()

$genContracts = Join-Path $PkgRoot "contracts"
if (Test-Path -LiteralPath $genContracts) {
    Get-ChildItem -LiteralPath $genContracts -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction Stop
    Remove-Item -LiteralPath $genContracts -Force -ErrorAction SilentlyContinue
}
$genLicense = Join-Path $PkgRoot "LICENSE"
if (Test-Path -LiteralPath $genLicense) {
    Remove-Item -LiteralPath $genLicense -Force -ErrorAction SilentlyContinue
}

Set-Location $PkgRoot

Write-Host "Publishing @noirstack/cascades-sdk@$ReleaseVersion from $PkgRoot"

$publishArgs = @("publish", "--access", "public")
if ($DryRun) {
    $publishArgs += "--dry-run"
}

& npm @publishArgs
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}

if ($DryRun) {
    Write-Host "npm publish --dry-run finished."
}
else {
    Write-Host "npm publish finished."
}
