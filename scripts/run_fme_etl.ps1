$ErrorActionPreference = "Stop"

# Project root is one level above the scripts folder.
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# Allow users to override these paths using environment variables.
$FmeExecutable = if ($env:FME_EXE) {
    $env:FME_EXE
}
else {
    "C:\Program Files\FME\fme.exe"
}

$FmeWorkspace = if ($env:FME_WORKSPACE) {
    $env:FME_WORKSPACE
}
else {
    Join-Path $ProjectRoot "fme_workspaces\roads_to_postgis.fmw"
}

if (-not (Test-Path $FmeExecutable)) {
    throw "FME executable not found: $FmeExecutable"
}

if (-not (Test-Path $FmeWorkspace)) {
    throw @"
FME workspace not found: $FmeWorkspace

Set the FME_WORKSPACE environment variable to your local workspace path.
Example:
`$env:FME_WORKSPACE = 'C:\path\to\roads_to_postgis.fmw'
"@
}

Write-Host "Starting FME ETL..."
Write-Host "Workspace: $FmeWorkspace"

& $FmeExecutable $FmeWorkspace

if ($LASTEXITCODE -ne 0) {
    throw "FME ETL failed with exit code $LASTEXITCODE"
}

Write-Host "FME ETL completed successfully."