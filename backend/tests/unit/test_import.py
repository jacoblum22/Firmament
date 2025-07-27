#!/usr/bin/env python3
"""Test to verify that main.py imports correctly and the FastAPI app is properly configured"""

import sys
import os
from pathlib import Path
import pytest

# Get the backend directory and ensure we're running from there
backend_dir = Path(__file__).parent.parent.parent
os.chdir(backend_dir)

# Clean up any existing test paths that might interfere
paths_to_remove = []
for path in sys.path:
    if "tests" in path and str(backend_dir) in path:
        paths_to_remove.append(path)

for path in paths_to_remove:
    sys.path.remove(path)

# Add backend directory as the first path
sys.path.insert(0, str(backend_dir))

# Add tests directory for test utilities, but after backend
test_dir = backend_dir / "tests"
sys.path.append(str(test_dir))

# Import test utilities directly from the tests.utils module
import importlib.util

test_config_helper_path = test_dir / "utils" / "test_config_helper.py"
spec = importlib.util.spec_from_file_location(
    "test_config_helper", test_config_helper_path
)
if spec and spec.loader:
    test_config_helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(test_config_helper)
else:
    raise ImportError(
        f"Could not load test_config_helper from {test_config_helper_path}"
    )

# Set up required environment variables for the test
os.environ.setdefault("ENVIRONMENT", "development")
os.environ.setdefault("OPENAI_API_KEY", "sk-test1234567890abcdef")


def test_main_module_import():
    """Test that main.py can be imported successfully"""
    from main import app

    assert app is not None, "FastAPI app should not be None"
    assert hasattr(app, "title"), "FastAPI app should have a title attribute"
    assert hasattr(app, "version"), "FastAPI app should have a version attribute"

    print(f"✅ FastAPI app imported successfully: {app.title} v{app.version}")


def test_config_settings():
    """Test that configuration settings work correctly"""
    with test_config_helper.ConfigTestContext(
        ENVIRONMENT="development", OPENAI_API_KEY="sk-test1234567890abcdef"
    ):
        Settings = test_config_helper.import_config_settings()
        settings = Settings()

        assert settings.environment == "development"
        assert settings.debug is True
        assert isinstance(settings.allowed_origins, list)
        assert len(settings.allowed_origins) > 0

        print(
            f"✅ Configuration test passed: {settings.environment} mode, {len(settings.allowed_origins)} CORS origins"
        )


def test_app_properties():
    """Test that the FastAPI app has expected properties"""
    from main import app

    # Test app title and version
    assert app.title == "StudyMate API"
    assert app.version == "2.0.0"

    # Test that routes are attached
    assert len(app.routes) > 0, "App should have routes configured"

    print(
        f"✅ App properties verified: {app.title} v{app.version} with {len(app.routes)} routes"
    )


if __name__ == "__main__":
    # If run directly, execute the tests manually for compatibility
    try:
        test_main_module_import()
        test_config_settings()
        test_app_properties()
        print("\n🎉 All import tests passed successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
