# Test Configuration Helper

This utility provides a standardized way to handle config imports and environment variable management across all test files.

## Problem Solved

Many test files were having issues with:
- Import errors for `Settings` and `ConfigurationError` classes
- Proper module reloading when testing with different environment variables
- Environment variable cleanup after tests
- Path resolution to the backend directory

## Usage

### Basic Import

```python
from utils.test_config_helper import import_config, import_config_settings

# Import both Settings and ConfigurationError
Settings, ConfigurationError = import_config()

# Import just Settings
Settings = import_config_settings()
```

### Using ConfigTestContext (Recommended)

```python
from utils.test_config_helper import ConfigTestContext, import_config_settings

# Test with specific environment variables
with ConfigTestContext(PORT="8080", ENVIRONMENT="development"):
    Settings = import_config_settings()
    config = Settings()
    print(f"Port: {config.port}")
# Environment variables are automatically cleaned up
```

### Convenience Functions

```python
from utils.test_config_helper import test_config_with_port, test_config_development

# Create config with specific port
config = test_config_with_port("8080", "development")

# Create development config
config = test_config_development()
```

### Decorator for Environment Variables

```python
from utils.test_config_helper import with_env_vars

@with_env_vars(PORT="8080", ENVIRONMENT="development")
def test_something():
    # Test code here - environment variables are set automatically
    pass
```

## Key Features

1. **Automatic Path Resolution**: Correctly finds the backend directory from any test file
2. **Module Reloading**: Properly clears and reloads the config module for fresh imports
3. **Environment Cleanup**: Automatically restores original environment variables
4. **Type Safety**: No more linter errors about unknown import symbols
5. **Context Management**: Clean, readable test code with automatic cleanup

## Quick Migration for Existing Tests

### 1. Update Imports
Replace the old pattern:
```python
import importlib
from pathlib import Path

backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))
```

With:
```python
from pathlib import Path

test_dir = Path(__file__).parent.parent
sys.path.insert(0, str(test_dir))

from utils.test_config_helper import import_config, ConfigTestContext
```

### 2. Replace safe_import_config Functions
Replace complex `safe_import_config` functions with:
```python
def safe_import_config():
    """Safely import config module using the test helper"""
    try:
        Settings, ConfigurationError = import_config()
        config = Settings()
        return config, False, None
    except SystemExit as e:
        return None, True, e.code
    except Exception as e:
        return None, True, getattr(e, 'code', 1)
```

### 3. Use ConfigTestContext in Tests
Replace manual environment variable management:
```python
# OLD WAY
os.environ["PORT"] = "8080"
os.environ["ENVIRONMENT"] = "development"
# ... test code ...
# Manual cleanup required
```

With ConfigTestContext:
```python
# NEW WAY
with ConfigTestContext(PORT="8080", ENVIRONMENT="development"):
    Settings = import_config_settings()
    config = Settings()
    # ... test code ...
    # Automatic cleanup!
```

## Migration Guide

### Before (Old Pattern):
```python
import os
import sys
import importlib
from pathlib import Path

backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

def test_something():
    os.environ["PORT"] = "8080"
    if "config" in sys.modules:
        importlib.reload(sys.modules["config"])
    from config import settings  # ❌ Linter error
    # ... test code
```

### After (New Pattern):
```python
from utils.test_config_helper import ConfigTestContext, import_config_settings

def test_something():
    with ConfigTestContext(PORT="8080"):
        Settings = import_config_settings()  # ✅ No linter errors
        config = Settings()
        # ... test code
    # ✅ Automatic cleanup
```

## Functions Reference

- `import_config()` - Import Settings and ConfigurationError classes
- `import_config_settings()` - Import just the Settings class
- `ConfigTestContext(**env_vars)` - Context manager for environment variables
- `create_test_config(port, environment, openai_api_key)` - Create config with specific values
- `test_config_with_port(port, environment)` - Convenience function for port testing
- `test_config_development()` - Development environment config
- `test_config_production()` - Production environment config
- `with_env_vars(**env_vars)` - Decorator for environment variables
