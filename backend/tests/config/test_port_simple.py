#!/usr/bin/env python3
"""
Simple test to verify port validation improvements
"""

import os
import sys
import importlib
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent
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


def test_port_validation_simple():
    """Test port validation with various invalid inputs"""

    print("🧪 Testing Port Validation Improvements")
    print("=" * 40)

    # Test cases: (port_value, environment, should_raise, expected_port)
    test_cases = [
        ("8000", "development", False, 8000),
        ("8000", "production", False, 8000),
        ("invalid", "development", False, 8000),  # fallback to default
        ("invalid", "production", True, None),  # should raise error
        ("0", "development", False, 8000),  # fallback to default
        ("0", "production", True, None),  # should raise error
        ("65536", "development", False, 8000),  # fallback to default
        ("65536", "production", True, None),  # should raise error
    ]

    # Store original environment
    original_env = {}
    for key in ["PORT", "ENVIRONMENT", "OPENAI_API_KEY"]:
        if key in os.environ:
            original_env[key] = os.environ[key]

    try:
        for port_value, environment, should_raise, expected_port in test_cases:
            print(f"\n📋 Testing PORT='{port_value}' in {environment} mode...")

            # Set environment variables
            os.environ["PORT"] = port_value
            os.environ["ENVIRONMENT"] = environment
            os.environ["OPENAI_API_KEY"] = "sk-test1234567890abcdef"

            try:
                settings, exit_called, exit_code = safe_import_config()

                # Test the port property directly
                if should_raise:
                    if exit_called and exit_code == 1:
                        print(
                            f"✅ Expected error for PORT='{port_value}' in {environment} mode: SystemExit"
                        )
                    else:
                        try:
                            actual_port = settings.port
                            print(
                                f"❌ Expected error for PORT='{port_value}' in {environment} mode, but got port {actual_port}"
                            )
                            return False
                        except Exception as e:
                            print(
                                f"✅ Expected error for PORT='{port_value}' in {environment} mode: {str(e)[:100]}..."
                            )
                        continue
                else:
                    try:
                        actual_port = settings.port
                        if actual_port == expected_port:
                            print(
                                f"✅ PORT='{port_value}' in {environment} mode → {actual_port} (expected)"
                            )
                        else:
                            print(
                                f"❌ PORT='{port_value}' in {environment} mode → {actual_port} (expected {expected_port})"
                            )
                            return False
                    except Exception as e:
                        print(
                            f"❌ Unexpected error for PORT='{port_value}' in {environment} mode: {e}"
                        )
                        return False

            except Exception as e:
                if should_raise:
                    print(
                        f"✅ Expected error for PORT='{port_value}' in {environment} mode: {str(e)[:100]}..."
                    )
                else:
                    print(
                        f"❌ Unexpected error for PORT='{port_value}' in {environment} mode: {e}"
                    )
                    return False

    finally:
        # Restore original environment
        for key in ["PORT", "ENVIRONMENT", "OPENAI_API_KEY"]:
            if key in original_env:
                os.environ[key] = original_env[key]
            elif key in os.environ:
                del os.environ[key]

    print("\n🎉 All port validation tests passed!")
    return True


if __name__ == "__main__":
    success = test_port_validation_simple()
    if success:
        print("\n✅ Port validation test completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ Port validation test failed!")
        sys.exit(1)
