# PowerShell script for StudyMate Backend Dependency Management
# Usage: .\deps.ps1 <command>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("help", "install", "install-dev", "install-prod", "update-deps", "test", "test-config", "clean", "setup-dev", "security-check", "format", "lint")]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "StudyMate Backend Dependency Management" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  install      - Install production dependencies"
    Write-Host "  install-dev  - Install development dependencies"
    Write-Host "  install-prod - Install production dependencies (alias for install)"
    Write-Host "  update-deps  - Update dependency versions (requires pip-tools)"
    Write-Host "  test         - Run tests"
    Write-Host "  test-config  - Run configuration tests"
    Write-Host "  clean        - Clean virtual environment"
    Write-Host "  setup-dev    - Setup development environment"
    Write-Host "  security-check - Check for security vulnerabilities"
    Write-Host "  format       - Format code with black"
    Write-Host "  lint         - Lint code with flake8 and mypy"
    Write-Host ""
    Write-Host "Usage examples:" -ForegroundColor Cyan
    Write-Host "  .\deps.ps1 install"
    Write-Host "  .\deps.ps1 install-dev"
    Write-Host "  .\deps.ps1 test"
}

function Install-Dependencies {
    Write-Host "Installing production dependencies..." -ForegroundColor Yellow
    pip install --no-deps -r requirements.txt
    Write-Host "Production dependencies installed!" -ForegroundColor Green
}

function Install-DevDependencies {
    Write-Host "Installing development dependencies..." -ForegroundColor Yellow
    pip install --no-deps -r requirements.txt
    pip install --no-deps -r requirements-dev.txt
    Write-Host "Development dependencies installed!" -ForegroundColor Green
}

function Update-Dependencies {
    Write-Host "Updating dependencies..." -ForegroundColor Yellow
    Write-Host "Installing pip-tools if not available..."
    pip install pip-tools
    Write-Host "Compiling requirements..."
    pip-compile requirements.in
    pip-compile requirements-dev.in
    pip-compile requirements-prod.in
    Write-Host "Dependencies updated. Review changes and commit." -ForegroundColor Green
}

function Run-Tests {
    Write-Host "Running tests..." -ForegroundColor Yellow
    python -m pytest tests/ -v
}

function Run-ConfigTests {
    Write-Host "Running configuration tests..." -ForegroundColor Yellow
    python test_config.py
}

function Clean-Environment {
    Write-Host "Cleaning virtual environment..." -ForegroundColor Yellow
    pip freeze | ForEach-Object { if ($_ -notmatch "^-e") { pip uninstall $_.Split("==")[0] -y } }
    Write-Host "Virtual environment cleaned!" -ForegroundColor Green
}

function Setup-DevEnvironment {
    Install-DevDependencies
    Write-Host "Setting up pre-commit hooks..." -ForegroundColor Yellow
    pre-commit install
    Write-Host "Development environment ready!" -ForegroundColor Green
}

function Check-Security {
    Write-Host "Checking for security vulnerabilities..." -ForegroundColor Yellow
    pip install safety
    safety check
}

function Format-Code {
    Write-Host "Formatting code with black..." -ForegroundColor Yellow
    black .
    Write-Host "Code formatted!" -ForegroundColor Green
}

function Lint-Code {
    Write-Host "Linting code..." -ForegroundColor Yellow
    flake8 .
    mypy .
    Write-Host "Code linting completed!" -ForegroundColor Green
}

# Execute command
switch ($Command) {
    "help" { Show-Help }
    "install" { Install-Dependencies }
    "install-dev" { Install-DevDependencies }
    "install-prod" { Install-Dependencies }
    "update-deps" { Update-Dependencies }
    "test" { Run-Tests }
    "test-config" { Run-ConfigTests }
    "clean" { Clean-Environment }
    "setup-dev" { Setup-DevEnvironment }
    "security-check" { Check-Security }
    "format" { Format-Code }
    "lint" { Lint-Code }
    default { Show-Help }
}
