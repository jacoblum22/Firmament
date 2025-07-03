#!/usr/bin/env python3
"""
Test Configuration Validation System
"""
import os
import sys
import importlib
from pathlib import Path

# Add the backend directory to Python path to import config
backend_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_dir))


def safe_import_config():
    """Safely import config module, handling SystemExit exceptions"""
    # Temporarily capture sys.exit to prevent it from terminating the test
    original_exit = sys.exit
    exit_called = False
    exit_code = None

    def mock_exit(code=0):
        nonlocal exit_called, exit_code
        exit_called = True
        exit_code = code
        # Don't actually exit, just capture the call

    sys.exit = mock_exit

    try:
        if "config" in sys.modules:
            importlib.reload(sys.modules["config"])

        import config

        settings = getattr(config, "settings", None)
        if settings is None:
            raise AttributeError("Config module does not have a 'settings' attribute")

        return settings, exit_called, exit_code

    except SystemExit as e:
        # Handle SystemExit explicitly
        exit_called = True
        exit_code = e.code
        # Try to still get the config if possible
        try:
            import config

            settings = getattr(config, "settings", None)
            if settings is not None:
                return settings, exit_called, exit_code
        except:
            pass
        # If we can't get settings, raise the original exception
        raise e

    finally:
        sys.exit = original_exit


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

        print(f"✅ Development environment loaded successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Debug: {settings.debug}")
        print(f"   OpenAI configured: {bool(settings.openai_api_key)}")
        print(f"   Exit called: {exit_called}")

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

        print(f"✅ Production environment with valid keys loaded successfully")
        print(f"   Environment: {settings.environment}")
        print(f"   Debug: {settings.debug}")
        print(f"   OpenAI configured: {bool(settings.openai_api_key)}")
        print(f"   Host: {settings.host}")
        print(f"   Workers: {settings.workers}")

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

        summary = settings.get_config_summary()
        print("✅ Configuration summary:")
        for key, value in summary.items():
            print(f"   {key}: {value}")

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

            try:
                settings, exit_called, exit_code = safe_import_config()

                if should_raise:
                    print(
                        f"    ❌ Expected error for PORT='{port_value}' in {environment} mode, but got port {settings.port}"
                    )
                    return False
                else:
                    actual_port = settings.port
                    if actual_port == expected_port:
                        print(f"    ✅ PORT='{port_value}' → {actual_port}")
                    else:
                        print(
                            f"    ❌ PORT='{port_value}' → {actual_port} (expected {expected_port})"
                        )
                        return False

            except Exception as e:
                if should_raise:
                    print(
                        f"    ✅ Expected error for PORT='{port_value}' in {environment} mode: {e}"
                    )
                else:
                    print(
                        f"    ❌ Unexpected error for PORT='{port_value}' in {environment} mode: {e}"
                    )
                    return False

        # Test production mode with invalid ports (should raise)
        print("  Testing invalid ports in production mode...")
        production_error_cases = ["invalid", "0", "65536", "-1", ""]

        for port_value in production_error_cases:
            os.environ["PORT"] = port_value
            os.environ["ENVIRONMENT"] = "production"

            try:
                settings, exit_called, exit_code = safe_import_config()

                # Check if validation failed appropriately
                if exit_called and exit_code == 1:
                    print(
                        f"    ✅ Expected error for PORT='{port_value}' in production mode: SystemExit"
                    )
                else:
                    # This should raise an error when accessing the port
                    try:
                        port = settings.port
                        print(
                            f"    ❌ Expected error for PORT='{port_value}' in production mode, but got port {port}"
                        )
                        return False
                    except Exception as port_error:
                        print(
                            f"    ✅ Expected error for PORT='{port_value}' in production mode: {type(port_error).__name__}"
                        )

            except Exception as e:
                print(
                    f"    ✅ Expected error for PORT='{port_value}' in production mode: {type(e).__name__}"
                )

        print("  ✅ All port validation tests passed!")
        return True

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


if __name__ == "__main__":
    test_configuration_validation()
    test_port_validation()
