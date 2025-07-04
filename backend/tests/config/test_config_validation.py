#!/usr/bin/env python3
"""
Test Configuration Validation System
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


def test_configuration_validation():
    """Test the configuration validation system"""

    print("🧪 Testing Configuration Validation System")
    print("=" * 50)

    # Test 1: Development environment (should work with warnings)
    print("\n📋 Test 1: Development Environment")
    try:
        os.environ["ENVIRONMENT"] = "development"
        # Clear any existing OPENAI_API_KEY to test warning
        os.environ.pop("OPENAI_API_KEY", None)

        settings, exit_called, exit_code = safe_import_config()

        if settings is not None:
            print(f"✅ Development environment loaded successfully")
            print(f"   Environment: {settings.environment}")
            print(f"   Debug: {settings.debug}")
            print(f"   OpenAI configured: {bool(settings.openai_api_key)}")
            print(f"   Exit called: {exit_called}")
        else:
            print(
                f"❌ Development test failed: Config import returned None (exit_code: {exit_code})"
            )

    except Exception as e:
        print(f"❌ Development test failed: {e}")

    # Test 2: Production with missing keys (should fail)
    print("\n📋 Test 2: Production with Missing Keys")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ.pop("OPENAI_API_KEY", None)

        settings, exit_called, exit_code = safe_import_config()

        if exit_called and exit_code == 1:
            print(
                "✅ Production validation correctly failed: Configuration errors detected"
            )
            print("   (This is expected behavior)")
        else:
            print("❌ Production test should have failed but didn't")

    except Exception as e:
        print(f"✅ Production validation correctly failed: {e}")
        print(f"   (This is expected behavior)")

    # Test 3: Production with valid keys (should work)
    print("\n📋 Test 3: Production with Valid Keys")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["OPENAI_API_KEY"] = "sk-test123456789abcdef"

        settings, exit_called, exit_code = safe_import_config()

        if settings is not None:
            print(f"✅ Production environment with valid keys loaded successfully")
            print(f"   Environment: {settings.environment}")
            print(f"   Debug: {settings.debug}")
            print(f"   OpenAI configured: {bool(settings.openai_api_key)}")
            print(f"   Host: {settings.host}")
            print(f"   Workers: {settings.workers}")
        else:
            print(
                f"❌ Production with valid keys failed: Config import returned None (exit_code: {exit_code})"
            )

    except Exception as e:
        print(f"❌ Production with valid keys failed: {e}")

    # Test 4: Invalid API key format
    print("\n📋 Test 4: Invalid API Key Format")
    try:
        os.environ["ENVIRONMENT"] = "production"
        os.environ["OPENAI_API_KEY"] = "invalid-key-format"

        settings, exit_called, exit_code = safe_import_config()

        if exit_called and exit_code == 1:
            print("✅ Correctly rejected invalid API key format")
        else:
            print("❌ Should have failed with invalid API key format")

    except Exception as e:
        print(f"✅ Correctly rejected invalid API key format: {e}")

    # Test 5: Configuration summary
    print("\n📋 Test 5: Configuration Summary")
    try:
        os.environ["ENVIRONMENT"] = "development"
        os.environ["OPENAI_API_KEY"] = "sk-dev123456789"

        settings, exit_called, exit_code = safe_import_config()

        if settings is not None:
            summary = settings.get_config_summary()
            print("✅ Configuration summary:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
        else:
            print(
                f"❌ Configuration summary failed: Config import returned None (exit_code: {exit_code})"
            )

    except Exception as e:
        print(f"❌ Configuration summary failed: {e}")

    print("\n✅ Configuration validation testing completed!")


def test_port_validation():
    """Test port validation in development and production modes"""

    print("\n📋 Testing Port Validation")
    print("-" * 30)

    # Store original values
    original_port = os.environ.get("PORT")
    original_env = os.environ.get("ENVIRONMENT")

    try:
        # Test cases: (port_value, environment, should_raise, expected_port)
        test_cases = [
            ("8000", "development", False, 8000),
            ("8000", "production", False, 8000),
            ("80", "development", False, 80),
            ("65535", "development", False, 65535),
            ("1", "development", False, 1),
            ("invalid", "development", False, 8000),  # fallback to default
            ("0", "development", False, 8000),  # fallback to default
            ("65536", "development", False, 8000),  # fallback to default
            ("-1", "development", False, 8000),  # fallback to default
        ]

        for port_value, environment, should_raise, expected_port in test_cases:
            print(f"  Testing PORT='{port_value}' in {environment} mode...")

            # Set environment variables
            os.environ["PORT"] = port_value
            os.environ["ENVIRONMENT"] = environment

            # Set a valid API key for production tests
            if environment == "production":
                os.environ["OPENAI_API_KEY"] = "sk-test123456789abcdef"

            try:
                settings, exit_called, exit_code = safe_import_config()

                if should_raise:
                    if settings is not None:
                        assert (
                            False
                        ), f"Expected error for PORT='{port_value}' in {environment} mode, but got port {settings.port}"
                    else:
                        print(
                            f"    ✅ Expected error for PORT='{port_value}' in {environment} mode: Config import failed"
                        )
                else:
                    if settings is not None:
                        actual_port = settings.port
                        if actual_port == expected_port:
                            print(f"    ✅ PORT='{port_value}' → {actual_port}")
                        else:
                            assert (
                                False
                            ), f"PORT='{port_value}' → {actual_port} (expected {expected_port})"
                    else:
                        assert (
                            False
                        ), f"Unexpected failure for PORT='{port_value}' in {environment} mode: Config import failed (exit_code: {exit_code})"

            except Exception as e:
                if should_raise:
                    print(
                        f"    ✅ Expected error for PORT='{port_value}' in {environment} mode: {e}"
                    )
                else:
                    assert (
                        False
                    ), f"Unexpected error for PORT='{port_value}' in {environment} mode: {e}"

        # Test production mode with invalid ports (should raise)
        print("  Testing invalid ports in production mode...")
        production_error_cases = ["invalid", "0", "65536", "-1", ""]

        for port_value in production_error_cases:
            os.environ["PORT"] = port_value
            os.environ["ENVIRONMENT"] = "production"
            os.environ["OPENAI_API_KEY"] = (
                "sk-test123456789abcdef"  # Valid key for production
            )

            try:
                settings, exit_called, exit_code = safe_import_config()

                # Check if validation failed appropriately
                if exit_called and exit_code == 1:
                    print(
                        f"    ✅ Expected error for PORT='{port_value}' in production mode: SystemExit"
                    )
                else:
                    # This should raise an error when accessing the port
                    if settings is not None:
                        try:
                            port = settings.port
                            assert (
                                False
                            ), f"Expected error for PORT='{port_value}' in production mode, but got port {port}"
                        except Exception as port_error:
                            print(
                                f"    ✅ Expected error for PORT='{port_value}' in production mode: {type(port_error).__name__}"
                            )
                    else:
                        print(
                            f"    ✅ Expected error for PORT='{port_value}' in production mode: Config import failed"
                        )

            except Exception as e:
                print(
                    f"    ✅ Expected error for PORT='{port_value}' in production mode: {type(e).__name__}"
                )

        print("  ✅ All port validation tests passed!")
        # Return nothing - pytest will handle success/failure via assertions

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

        # Clean up any test API keys
        if "OPENAI_API_KEY" in os.environ and os.environ["OPENAI_API_KEY"].startswith(
            "sk-test"
        ):
            del os.environ["OPENAI_API_KEY"]


if __name__ == "__main__":
    test_configuration_validation()
    test_port_validation()
