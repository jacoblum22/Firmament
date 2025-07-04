# StudyMate API Launcher for Windows PowerShell
# Usage: .\start.ps1 [development|production]

param(
    [ValidateSet("development", "production")]
    [string]$Environment = "development",
    [string]$Host = $null,
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

if ($Host) {
    $args += "--host", $Host
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

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "📦 Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
}

# Start the application
Write-Host "🔄 Starting application..." -ForegroundColor Blue
python @args
