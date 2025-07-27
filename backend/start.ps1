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

# Ensure virtual environment is activated
if (-not (Test-Path env:VIRTUAL_ENV)) {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Start the application
Write-Host "🔄 Starting application..." -ForegroundColor Blue
python @args
