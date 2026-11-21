# StudyMate API Launcher for Windows PowerShell
# Usage: .\start.ps1 [development|production]

param(
    [ValidateSet("development", "production")]
    [string]$Environment = "development",
    [string]$ApplicationHostname = $null,
    [int]$Port = $null,
    [switch]$Reload,
    [int]$Workers = $null
)

Write-Host "🚀 StudyMate API Launcher" -ForegroundColor Green
Write-Host "=========================" -ForegroundColor Green

# Set environment variable
$env:ENVIRONMENT = $Environment

# Build arguments
$args = @("start.py", "--env", $Environment)

if ($ApplicationHostname) {
    $args += "--host", $ApplicationHostname
}

if ($Port) {
    $args += "--port", $Port
}

if ($Reload) {
    $args += "--reload"
}

if ($Workers) {
    $args += "--workers", $Workers
}

# Ensure virtual environment is activated.
# Looks for a venv in (in order):
#   1. $env:FIRMAMENT_VENV  — set this env var to point at a venv outside the project
#   2. venv\  inside the backend directory  (created with: python -m venv venv)
if (-not (Test-Path env:VIRTUAL_ENV)) {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow

    $customVenv = $env:FIRMAMENT_VENV
    $localVenv  = Join-Path $PSScriptRoot "venv\Scripts\Activate.ps1"

    if ($customVenv -and (Test-Path "$customVenv\Scripts\Activate.ps1")) {
        & "$customVenv\Scripts\Activate.ps1"
    } elseif (Test-Path $localVenv) {
        & $localVenv
    } else {
        Write-Host "❌ No virtual environment found." -ForegroundColor Red
        Write-Host "   Option A: create one inside backend/: python -m venv venv" -ForegroundColor Yellow
        Write-Host "   Option B: set \$env:FIRMAMENT_VENV to your existing venv path" -ForegroundColor Yellow
        exit 1
    }
}

# Start the application
Write-Host "🔄 Starting application..." -ForegroundColor Blue
python @args
