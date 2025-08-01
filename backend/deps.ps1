# PowerShell script for Firmament Backend Dependency Management
# Usage: .\deps.ps1 <command>

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("help", "install", "install-dev", "install-prod", "update-deps", "test", "test-unit", "test-integration", "test-config", "test-utils", "clean", "setup-dev", "security-check", "format", "lint")]
    [string]$Command = "help"
)

function Show-Help {
    Write-Host "Firmament Backend Dependency Management" -ForegroundColor Green
    Write-Host "======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Available commands:" -ForegroundColor Yellow
    Write-Host "  install      - Install production dependencies"
    Write-Host "  install-dev  - Install development dependencies"
    Write-Host "  install-prod - Install production dependencies (alias for install)"
    Write-Host "  update-deps  - Update dependency versions (requires pip-tools)"
    Write-Host "  test         - Run all tests"
    Write-Host "  test-unit    - Run unit tests only"
    Write-Host "  test-integration - Run integration tests only"
    Write-Host "  test-config  - Run configuration tests only"
    Write-Host "  test-utils   - Run utility/processing tests only"
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
    Write-Host "  .\deps.ps1 test-unit"
    Write-Host "  .\deps.ps1 test-config"
}

function Install-Dependencies {
    Write-Host "Installing production dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    Write-Host "Production dependencies installed!" -ForegroundColor Green
}

function Install-DevDependencies {
    Write-Host "Installing development dependencies..." -ForegroundColor Yellow
    pip install -r requirements.txt
    pip install -r requirements-dev.txt
    Write-Host "Development dependencies installed!" -ForegroundColor Green
}

function Update-Dependencies {
    Write-Host "Updating dependencies..." -ForegroundColor Yellow
    
    # Check if required .in files exist
    $requiredFiles = @("requirements.in", "requirements-dev.in", "requirements-prod.in")
    $missingFiles = @()
    
    foreach ($file in $requiredFiles) {
        if (-not (Test-Path $file)) {
            $missingFiles += $file
        }
    }
    
    if ($missingFiles.Count -gt 0) {
        Write-Host "Error: Missing required .in files:" -ForegroundColor Red
        foreach ($file in $missingFiles) {
            Write-Host "  - $file" -ForegroundColor Red
        }
        Write-Host "Please create these files before running update-deps." -ForegroundColor Red
        return
    }
    
    # Install pip-tools with error handling
    Write-Host "Installing pip-tools if not available..."
    try {
        pip install pip-tools
        if ($LASTEXITCODE -ne 0) {
            throw "pip-tools installation failed with exit code $LASTEXITCODE"
        }
    }
    catch {
        Write-Host "Error installing pip-tools: $_" -ForegroundColor Red
        return
    }
    
    # Compile requirements with error handling
    Write-Host "Compiling requirements..."
    $compileFiles = @("requirements.in", "requirements-dev.in", "requirements-prod.in")
    
    foreach ($file in $compileFiles) {
        try {
            Write-Host "Compiling $file..."
            pip-compile $file
            if ($LASTEXITCODE -ne 0) {
                throw "Compilation of $file failed with exit code $LASTEXITCODE"
            }
        }
        catch {
            Write-Host "Error compiling $file`: $_" -ForegroundColor Red
            return
        }
    }
    
    Write-Host "Dependencies updated successfully. Review changes and commit." -ForegroundColor Green
}

function Run-Tests {
    Write-Host "Running all tests..." -ForegroundColor Yellow
    python -m pytest tests/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Tests failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "All tests passed!" -ForegroundColor Green
}

function Run-UnitTests {
    Write-Host "Running unit tests..." -ForegroundColor Yellow
    python -m pytest tests/unit/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Unit tests failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Unit tests passed!" -ForegroundColor Green
}

function Run-IntegrationTests {
    Write-Host "Running integration tests..." -ForegroundColor Yellow
    python -m pytest tests/integration/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Integration tests failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Integration tests passed!" -ForegroundColor Green
}

function Run-ConfigTests {
    Write-Host "Running configuration tests..." -ForegroundColor Yellow
    python -m pytest tests/config/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Configuration tests failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Configuration tests passed!" -ForegroundColor Green
}

function Run-UtilsTests {
    Write-Host "Running utility/processing tests..." -ForegroundColor Yellow
    python -m pytest tests/utils/ -v
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Utility tests failed!" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    Write-Host "Utility tests passed!" -ForegroundColor Green
}

function Clean-Environment {
    Write-Host "Cleaning virtual environment..." -ForegroundColor Yellow

    # Verify we're in a virtual environment
    if (-not $env:VIRTUAL_ENV) {
        Write-Host "Warning: Not in a virtual environment. Skipping clean." -ForegroundColor Red
        return
    }

    # Uninstall packages from requirements files
    if (Test-Path "requirements.txt") {
        pip uninstall -r requirements.txt -y
    }
    if (Test-Path "requirements-dev.txt") {
        pip uninstall -r requirements-dev.txt -y
    }

    Write-Host "Virtual environment cleaned!" -ForegroundColor Green
}
function Initialize-DevEnvironment {
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
    "test-unit" { Run-UnitTests }
    "test-integration" { Run-IntegrationTests }
    "test-config" { Run-ConfigTests }
    "test-utils" { Run-UtilsTests }
    "clean" { Clean-Environment }
    "setup-dev" { Setup-DevEnvironment }
    "security-check" { Check-Security }
    "format" { Format-Code }
    "lint" { Lint-Code }
    default { Show-Help }
}
