#!/usr/bin/env python3
"""
Test script to verify port validation in config.py
"""

import os
import sys
from pathlib import Path

# Add the parent directory to path to import test utilities
test_dir = Path(__file__).parent.parent
sys.path.insert(0, str(test_dir))

from tests.utils.test_config_helper import import_config, ConfigTestContext


def safe_import_config():
    """Safely import config module using the test helper"""
    try:
        Settings, ConfigurationError = import_config()
        config = Settings()
        return config, False, None
    except SystemExit as e:
        return None, True, e.code
    except Exception as e:
        # For other exceptions, we still want to know about them
        return None, True, getattr(e, "code", 1)


def test_port_validation():
    """Test port validation in both development and production modes"""

    print("🧪 Testing port validation...")

    # Test cases
    test_cases = [
        # (port_value, environment, should_raise, expected_port)
        ("8000", "development", False, 8000),
        ("8000", "production", False, 8000),
        ("80", "development", False, 80),
        ("65535", "development", False, 65535),
        ("1", "development", False, 1),
        ("invalid", "development", False, 8000),  # fallback to default
        ("invalid", "production", True, None),  # should raise error
        ("0", "development", False, 8000),  # fallback to default
        ("0", "production", True, None),  # should raise error
        ("65536", "development", False, 8000),  # fallback to default
        ("65536", "production", True, None),  # should raise error
        ("-1", "development", False, 8000),  # fallback to default
        ("-1", "production", True, None),  # should raise error
        ("", "development", False, 8000),  # fallback to default
        ("", "production", True, None),  # should raise error
    ]

    for port_value, environment, should_raise, expected_port in test_cases:
        print(f"\n📋 Testing PORT='{port_value}' in {environment} mode...")

        # Store original values
        original_port = os.environ.get("PORT")
        original_env = os.environ.get("ENVIRONMENT")
        original_openai = os.environ.get("OPENAI_API_KEY")

        try:
            # Set environment variables
            os.environ["PORT"] = port_value
            os.environ["ENVIRONMENT"] = environment
            os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"

            # Use safe_import_config to handle SystemExit
            settings, exit_called, exit_code = safe_import_config()

            if should_raise:
                if exit_called and exit_code == 1:
                    print(
                        f"✅ Expected error for PORT='{port_value}' in {environment} mode: SystemExit"
                    )
                elif settings is None:
                    print(
                        f"✅ Expected error for PORT='{port_value}' in {environment} mode: Config failed to load"
                    )
                else:
                    try:
                        actual_port = settings.port
                        assert (
                            False
                        ), f"Expected error for PORT='{port_value}' in {environment} mode, but got port {actual_port}"
                    except Exception as port_error:
                        print(
                            f"✅ Expected error for PORT='{port_value}' in {environment} mode: {type(port_error).__name__}"
                        )
            else:
                assert (
                    settings is not None
                ), f"Unexpected failure for PORT='{port_value}' in {environment} mode: Config import failed"
                actual_port = settings.port
                assert (
                    actual_port == expected_port
                ), f"PORT='{port_value}' in {environment} mode → {actual_port} (expected {expected_port})"
                print(
                    f"✅ PORT='{port_value}' in {environment} mode → {actual_port} (expected)"
                )

        finally:
            # Restore original values
            if original_port is not None:
                os.environ["PORT"] = original_port
            elif "PORT" in os.environ:
                del os.environ["PORT"]

            if original_env is not None:
                os.environ["ENVIRONMENT"] = original_env
            elif "ENVIRONMENT" in os.environ:
                del os.environ["ENVIRONMENT"]

            if original_openai is not None:
                os.environ["OPENAI_API_KEY"] = original_openai
            elif "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

    print("\n🎉 All port validation tests passed!")


def test_port_edge_cases():
    """Test additional edge cases for port validation"""

    print("\n🧪 Testing port edge cases...")

    # Store original values
    original_port = os.environ.get("PORT")
    original_env = os.environ.get("ENVIRONMENT")
    original_openai = os.environ.get("OPENAI_API_KEY")

    try:
        # Test with no PORT environment variable
        os.environ["ENVIRONMENT"] = "development"
        os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"
        if "PORT" in os.environ:
            del os.environ["PORT"]

        settings, exit_called, exit_code = safe_import_config()
        assert (
            settings is not None
        ), "Config should load successfully without PORT env var"
        assert (
            settings.port == 8000
        ), f"No PORT env var should default to 8000, got {settings.port}"
        print("✅ No PORT env var → default port 8000")

        # Test with whitespace
        os.environ["PORT"] = "  8080  "
        settings, exit_called, exit_code = safe_import_config()
        assert (
            settings is not None
        ), "Config should load successfully with whitespace PORT"
        assert (
            settings.port == 8080
        ), f"PORT with whitespace should be 8080, got {settings.port}"
        print("✅ PORT with whitespace → 8080")

        print("✅ All edge case tests passed!")

    finally:
        # Restore original values
        if original_port is not None:
            os.environ["PORT"] = original_port
        elif "PORT" in os.environ:
            del os.environ["PORT"]

        if original_env is not None:
            os.environ["ENVIRONMENT"] = original_env
        elif "ENVIRONMENT" in os.environ:
            del os.environ["ENVIRONMENT"]

        if original_openai is not None:
            os.environ["OPENAI_API_KEY"] = original_openai
        elif "OPENAI_API_KEY" in os.environ:
            del os.environ["OPENAI_API_KEY"]


if __name__ == "__main__":
    try:
        test_port_validation()
        test_port_edge_cases()
        print("\n🎉 All port validation tests completed successfully!")
        sys.exit(0)

    except Exception as e:
        print(f"\n💥 Test script failed with error: {e}")
        sys.exit(1)
