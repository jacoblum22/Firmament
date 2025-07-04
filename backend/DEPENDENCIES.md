# Dependency Management Guide

## Overview

This project uses pinned dependency versions to ensure reproducible builds and avoid version conflicts. All dependencies are locked to specific versions to guarantee consistent behavior across different environments.

## Dependency Files

### Core Dependencies
- `requirements.txt` - **Production dependencies** with pinned versions
- `requirements.in` - Input file for pip-tools (source of truth)

### Environment-Specific Dependencies
- `requirements-dev.txt` - **Development dependencies** (testing, linting, debugging)
- `requirements-prod.txt` - **Extended production dependencies** (monitoring, security)

### Management Tools
- `Makefile` - Unix/Linux dependency management commands
- `deps.ps1` - Windows PowerShell dependency management script

## Current Pinned Versions

### Core Framework
- `fastapi==0.115.14` - Web framework (Pydantic v2 compatible)
- `uvicorn==0.35.0` - ASGI server
- `pydantic==2.11.7` - Data validation and settings
- `pydantic-settings==2.10.1` - Settings management

### Configuration & Testing
- `python-dotenv==1.1.1` - Environment variable loading
- `pytest==8.4.1` - Testing framework

## Installation Commands

### Quick Setup
```bash
# Production
pip install -r requirements.txt

# Development
pip install -r requirements.txt -r requirements-dev.txt

# Extended Production
pip install -r requirements-prod.txt
```

### Using Management Scripts

#### Windows (PowerShell)
```powershell
# Show help
.\deps.ps1 help

# Install dependencies
.\deps.ps1 install           # Production
.\deps.ps1 install-dev       # Development
.\deps.ps1 setup-dev         # Full dev setup with pre-commit

# Run tests
.\deps.ps1 test-config       # Configuration tests
.\deps.ps1 test              # Full test suite

# Maintenance
.\deps.ps1 security-check    # Security vulnerability scan
.\deps.ps1 format            # Code formatting
.\deps.ps1 lint              # Code linting
```

#### Unix/Linux (Make)
```bash
# Show help
make help

# Install dependencies
make install                 # Production
make install-dev             # Development
make setup-dev               # Full dev setup

# Run tests
make test-config             # Configuration tests
make test                    # Full test suite

# Maintenance
make security-check          # Security vulnerability scan
make format                  # Code formatting
make lint                    # Code linting
```

## Updating Dependencies

### Using pip-tools (Recommended)
```bash
# Install pip-tools
pip install pip-tools

# Update all dependencies
pip-compile requirements.in
pip-compile requirements-dev.in
pip-compile requirements-prod.in

# Or use management script
make update-deps              # Unix/Linux
.\deps.ps1 update-deps        # Windows
```

### Manual Updates
1. Edit the `.in` files with new version constraints
2. Run `pip-compile` to generate new `.txt` files
3. Test thoroughly before committing changes

## Version Compatibility Matrix

| FastAPI | Pydantic | Python | Status |
|---------|----------|--------|--------|
| 0.115.x | 2.11.x   | 3.9+   | ✅ Current |
| 0.110.x | 2.x      | 3.8+   | ✅ Supported |
| 0.104.x | 1.x      | 3.7+   | ❌ Legacy |

## Best Practices

### 1. Pinned Versions
- **Always pin exact versions** in production (`==` not `>=`)
- Use `.in` files for managing version constraints
- Test all updates in development first

### 2. Dependency Categories
- **Core**: Minimal runtime dependencies
- **Development**: Testing, linting, debugging tools
- **Production**: Monitoring, security, performance tools

### 3. Update Strategy
- **Weekly**: Check for security updates
- **Monthly**: Review and test minor updates
- **Quarterly**: Plan major version upgrades

### 4. Security
- Run `safety check` regularly for vulnerability scanning
- Subscribe to security advisories for core dependencies
- Use dependabot or similar tools for automated updates

## Troubleshooting

### Common Issues

#### 1. Version Conflicts
```bash
# Clear environment and reinstall
pip freeze | xargs pip uninstall -y
pip install -r requirements.txt
```

#### 2. Pydantic v1/v2 Conflicts
- Ensure FastAPI >= 0.110.0 for Pydantic v2 support
- Check that all dependencies support Pydantic v2

#### 3. Windows Installation Issues
```powershell
# Use --no-deps to avoid conflicts
pip install --no-deps -r requirements.txt
```

### Verification Commands
```bash
# Check installed versions
pip list | grep -E "(fastapi|pydantic|uvicorn)"

# Test compatibility
python -c "import fastapi, pydantic; print(f'FastAPI: {fastapi.__version__}, Pydantic: {pydantic.__version__}')"

# Run configuration tests
python test_config.py
```

## Future Considerations

### Automated Dependency Management
Consider implementing:
- **Dependabot**: Automated dependency updates
- **Renovate**: More advanced dependency management
- **GitHub Actions**: CI/CD pipeline for dependency testing

### Monitoring
- Set up alerts for security vulnerabilities
- Monitor dependency licenses for compliance
- Track dependency update frequency and stability

## Contributing

When adding new dependencies:
1. Add to appropriate `.in` file with version constraint
2. Run `pip-compile` to update `.txt` files
3. Test thoroughly in development
4. Update this documentation if needed
5. Include rationale in PR description
